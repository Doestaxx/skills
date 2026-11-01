#!/usr/bin/env python3
"""Run ComfyUI API-format graphs from the shell, standard library only.

The agent runs this; it is the doestaxx-workflows skill's route to a ComfyUI
server over its HTTP API.

Environment:
  COMFYUI_URL    base URL of the server, e.g. http://127.0.0.1:8188 (required)
  COMFYUI_TOKEN  optional bearer token for a server behind an auth proxy;
                 sent as "Authorization: Bearer ...", never printed

Subcommands:
  check [GRAPH]                 server reachable; with GRAPH, every class_type
                                exists in /object_info (exit 1 if not)
  upload FILE [--subfolder S] [--overwrite]
                                POST /upload/image; prints the value a
                                LoadImage node takes
  run GRAPH [--set ID.INPUT=VALUE ...] [--out DIR] [--timeout S] [--poll S]
                                queue, wait on /history, download outputs

Exit codes: 0 ok, 1 usage or missing nodes, 2 server rejected the graph,
3 timed out while the prompt is still queued or running (never resubmit:
re-check /history with the printed prompt_id), 4 the run itself failed.
"""

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


class ComfyError(Exception):
    def __init__(self, message, code=1, payload=None):
        super().__init__(message)
        self.code = code
        self.payload = payload


def base_url():
    url = os.environ.get("COMFYUI_URL", "").strip().rstrip("/")
    if not url:
        raise ComfyError("COMFYUI_URL is not set (for example http://127.0.0.1:8188)")
    return url


def request(path, data=None, headers=None, method=None, raw=False):
    hdrs = dict(headers or {})
    token = os.environ.get("COMFYUI_TOKEN")
    if token:
        hdrs["Authorization"] = "Bearer " + token
    req = urllib.request.Request(base_url() + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
    except urllib.error.HTTPError as err:
        body = err.read()
        try:
            payload = json.loads(body.decode("utf-8"))
        except ValueError:
            payload = {"error": body.decode("utf-8", "replace")[:500]}
        raise ComfyError("HTTP %d on %s" % (err.code, path), 2, payload)
    except urllib.error.URLError as err:
        raise ComfyError("cannot reach ComfyUI at %s: %s" % (base_url(), err.reason))
    if raw:
        return body
    return json.loads(body.decode("utf-8")) if body else {}


def load_graph(path):
    with open(path, encoding="utf-8") as fh:
        graph = json.load(fh)
    # A UI-format save holds a "nodes" list and a "links" list; /prompt rejects it.
    if isinstance(graph, dict) and isinstance(graph.get("nodes"), list) and "links" in graph:
        raise ComfyError(
            "%s is a UI-format workflow; export it with Save (API Format) or convert it "
            "per doestaxx-workflow-authoring" % path
        )
    if isinstance(graph, dict) and isinstance(graph.get("prompt"), dict):
        graph = graph["prompt"]
    if not isinstance(graph, dict) or not all(
        isinstance(n, dict) and "class_type" in n for n in graph.values()
    ):
        raise ComfyError("%s is not an API-format graph (node id -> {class_type, inputs})" % path)
    return graph


def parse_value(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def apply_sets(graph, sets):
    for item in sets or []:
        target, sep, value = item.partition("=")
        node_id, dot, field = target.partition(".")
        if not sep or not dot or not field:
            raise ComfyError("--set takes NODE_ID.INPUT=VALUE, got %r" % item)
        if node_id not in graph:
            raise ComfyError("--set names node %r, which the graph does not hold" % node_id)
        graph[node_id].setdefault("inputs", {})[field] = parse_value(value)
    return graph


def missing_nodes(graph):
    info = request("/object_info")
    return sorted({n["class_type"] for n in graph.values()} - set(info))


def cmd_check(args):
    stats = request("/system_stats")
    system = stats.get("system", {})
    devices = [d.get("name") for d in stats.get("devices", [])]
    out = {"comfyui_version": system.get("comfyui_version"), "devices": devices}
    code = 0
    if args.graph:
        missing = missing_nodes(load_graph(args.graph))
        out["missing_class_types"] = missing
        code = 1 if missing else 0
    print(json.dumps(out, indent=2))
    return code


def multipart(fields, file_field, file_path):
    boundary = uuid.uuid4().hex
    parts = []
    for key, value in fields.items():
        parts.append(
            ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
             % (boundary, key, value)).encode("utf-8")
        )
    name = os.path.basename(file_path)
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    with open(file_path, "rb") as fh:
        content = fh.read()
    parts.append(
        ('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\n'
         "Content-Type: %s\r\n\r\n" % (boundary, file_field, name, ctype)).encode("utf-8")
        + content
        + b"\r\n"
    )
    parts.append(("--%s--\r\n" % boundary).encode("utf-8"))
    return b"".join(parts), "multipart/form-data; boundary=" + boundary


def cmd_upload(args):
    fields = {"type": "input", "overwrite": "true" if args.overwrite else "false"}
    if args.subfolder:
        fields["subfolder"] = args.subfolder
    body, ctype = multipart(fields, "image", args.file)
    resp = request("/upload/image", data=body, headers={"Content-Type": ctype}, method="POST")
    name = resp.get("name")
    sub = resp.get("subfolder") or ""
    resp["load_image_value"] = sub + "/" + name if sub else name
    print(json.dumps(resp, indent=2))
    return 0


def output_files(outputs):
    for node_id, node_out in (outputs or {}).items():
        for key, items in node_out.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and "filename" in item:
                    yield node_id, key, item


def download(item, out_dir):
    query = urllib.parse.urlencode(
        {
            "filename": item["filename"],
            "subfolder": item.get("subfolder", ""),
            "type": item.get("type", "output"),
        }
    )
    data = request("/view?" + query, raw=True)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, os.path.basename(item["filename"]))
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def cmd_run(args):
    graph = apply_sets(load_graph(args.graph), args.set)
    missing = missing_nodes(graph)
    if missing:
        print(json.dumps({"missing_class_types": missing}, indent=2))
        return 1
    payload = json.dumps({"prompt": graph, "client_id": uuid.uuid4().hex}).encode("utf-8")
    try:
        queued = request(
            "/prompt", data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
    except ComfyError as err:
        print(json.dumps(err.payload or {"error": str(err)}, indent=2))
        return 2
    if queued.get("node_errors"):
        print(json.dumps(queued, indent=2))
        return 2
    prompt_id = queued["prompt_id"]
    deadline = time.monotonic() + args.timeout
    while True:
        history = request("/history/" + urllib.parse.quote(prompt_id))
        entry = history.get(prompt_id)
        if entry is not None:
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                print(json.dumps({"prompt_id": prompt_id, "status": status}, indent=2))
                return 4
            if status.get("completed", True):
                break
        if time.monotonic() >= deadline:
            print(json.dumps({"prompt_id": prompt_id, "status": "pending"}, indent=2))
            return 3
        time.sleep(args.poll)
    files = [
        {"node": node_id, "kind": key, "path": download(item, args.out)}
        for node_id, key, item in output_files(entry.get("outputs"))
        if item.get("type", "output") == "output" or args.include_temp
    ]
    print(json.dumps({"prompt_id": prompt_id, "status": "success", "files": files}, indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check")
    p.add_argument("graph", nargs="?")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("upload")
    p.add_argument("file")
    p.add_argument("--subfolder")
    p.add_argument("--overwrite", action="store_true")
    p.set_defaults(func=cmd_upload)
    p = sub.add_parser("run")
    p.add_argument("graph")
    p.add_argument("--set", action="append", metavar="ID.INPUT=VALUE")
    p.add_argument("--out", default="comfy_outputs")
    p.add_argument("--timeout", type=float, default=600)
    p.add_argument("--poll", type=float, default=2)
    p.add_argument("--include-temp", action="store_true", help="also save preview (temp) files")
    p.set_defaults(func=cmd_run)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ComfyError as err:
        print("comfy_run: " + str(err), file=sys.stderr)
        if err.payload:
            print(json.dumps(err.payload, indent=2), file=sys.stderr)
        return err.code


if __name__ == "__main__":
    sys.exit(main())
