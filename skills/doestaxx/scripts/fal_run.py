#!/usr/bin/env python3
"""Run a fal.ai model through its queue API, standard library only.

The agent runs this when the doestaxx skill routes a job to fal.ai.

Environment:
  FAL_KEY        fal API key (required); sent as "Authorization: Key ...",
                 never printed
  FAL_QUEUE_URL  queue base URL override, default https://queue.fal.run

Subcommands:
  run MODEL [--input JSON | --input @FILE] [--set KEY=VALUE ...]
            [--file KEY=PATH ...] [--out DIR] [--timeout S] [--poll S]
      Submit, wait, save result.json, download every media URL in it.
      MODEL is the full id, subpath included (fal-ai/flux/dev).
      --set parses VALUE as JSON when it can (numbers, true, lists).
      --file inlines a local file as a base64 data URI; fal recommends
      hosted URLs for anything over a few KB.
  resume DIR [--timeout S] [--poll S]
      Keep waiting on the request saved in DIR/request.json.

Exit codes: 0 ok, 1 usage or HTTP error, 3 timed out while the request is
still queued or running (never resubmit: run "resume DIR"), 4 the run failed.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DATA_URI_WARN_BYTES = 256 * 1024


class FalError(Exception):
    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code


def queue_base():
    return os.environ.get("FAL_QUEUE_URL", "https://queue.fal.run").rstrip("/")


def auth_headers():
    key = os.environ.get("FAL_KEY", "").strip()
    if not key:
        raise FalError("FAL_KEY is not set in the environment")
    return {"Authorization": "Key " + key}


def http_json(url, payload=None, method=None):
    headers = auth_headers()
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:2000]
        raise FalError(f"HTTP {err.code} from {url}: {detail}")
    except urllib.error.URLError as err:
        raise FalError(f"cannot reach {url}: {err.reason}")
    return json.loads(body or b"{}")


def parse_value(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def set_path(target, dotted, value):
    keys = dotted.split(".")
    for key in keys[:-1]:
        target = target.setdefault(key, {})
    target[keys[-1]] = value


def data_uri(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if len(raw) > DATA_URI_WARN_BYTES:
        print(
            f"warning: {path} is {len(raw)} bytes; fal recommends a hosted URL for large inputs",
            file=sys.stderr,
        )
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


def build_input(args):
    payload = {}
    if args.input:
        text = args.input
        if text.startswith("@"):
            with open(text[1:], encoding="utf-8") as fh:
                text = fh.read()
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise FalError("--input must be a JSON object")
    for item in args.set or []:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise FalError(f"--set needs KEY=VALUE, got {item!r}")
        set_path(payload, key, parse_value(value))
    for item in args.file or []:
        key, sep, path = item.partition("=")
        if not sep or not key:
            raise FalError(f"--file needs KEY=PATH, got {item!r}")
        set_path(payload, key, data_uri(path))
    return payload


def media_urls(node, found=None):
    """Every http(s) value under a "url" key, in document order, deduplicated."""
    found = [] if found is None else found
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "url" and isinstance(value, str) and value.startswith(("http://", "https://")):
                if value not in found:
                    found.append(value)
            else:
                media_urls(value, found)
    elif isinstance(node, list):
        for value in node:
            media_urls(value, found)
    return found


def download(url, out_dir, index):
    name = os.path.basename(urllib.parse.urlparse(url).path) or f"output-{index}"
    target = os.path.join(out_dir, f"{index:02d}-{name}")
    # Output media URLs are public; no auth header, so the key never leaves for a CDN.
    with urllib.request.urlopen(url, timeout=300) as resp, open(target, "wb") as fh:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            fh.write(chunk)
    return target


def wait(state, out_dir, timeout, poll):
    deadline = time.monotonic() + timeout
    while True:
        status = http_json(state["status_url"])
        current = status.get("status")
        if current == "COMPLETED":
            break
        if current not in ("IN_QUEUE", "IN_PROGRESS"):
            raise FalError(f"request {state['request_id']} ended as {current!r}: {status}", 4)
        if time.monotonic() >= deadline:
            raise FalError(
                f"timed out with request {state['request_id']} still {current}; "
                f'run "resume {out_dir}", never resubmit',
                3,
            )
        time.sleep(poll)
    result = http_json(state["response_url"])
    if isinstance(result, dict) and result.get("detail") and not media_urls(result):
        raise FalError(f"request {state['request_id']} failed: {result['detail']}", 4)
    with open(os.path.join(out_dir, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    files = [download(url, out_dir, i) for i, url in enumerate(media_urls(result), 1)]
    return {"request_id": state["request_id"], "files": files, "result": os.path.join(out_dir, "result.json")}


def cmd_run(args):
    payload = build_input(args)
    os.makedirs(args.out, exist_ok=True)
    model = args.model.strip("/")
    submitted = http_json(f"{queue_base()}/{model}", payload, method="POST")
    for field in ("request_id", "status_url", "response_url"):
        if field not in submitted:
            raise FalError(f"submit response lacks {field}: {submitted}")
    state = {k: submitted[k] for k in ("request_id", "status_url", "response_url")}
    state["model"] = model
    with open(os.path.join(args.out, "request.json"), "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
    print(json.dumps({"submitted": state["request_id"]}), file=sys.stderr)
    return wait(state, args.out, args.timeout, args.poll)


def cmd_resume(args):
    path = os.path.join(args.dir, "request.json")
    try:
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
    except OSError:
        raise FalError(f"no request.json in {args.dir}")
    return wait(state, args.dir, args.timeout, args.poll)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("model")
    run.add_argument("--input")
    run.add_argument("--set", action="append")
    run.add_argument("--file", action="append")
    run.add_argument("--out", default="fal-output")
    run.add_argument("--timeout", type=float, default=900)
    run.add_argument("--poll", type=float, default=3)
    resume = sub.add_parser("resume")
    resume.add_argument("dir")
    resume.add_argument("--timeout", type=float, default=900)
    resume.add_argument("--poll", type=float, default=3)
    args = parser.parse_args(argv)
    try:
        report = cmd_run(args) if args.cmd == "run" else cmd_resume(args)
    except FalError as err:
        print(f"error: {err}", file=sys.stderr)
        return err.code
    except (ValueError, OSError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
