import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "doestaxx-workflows" / "scripts"))

import comfy_run  # noqa: E402

GRAPH = {
    "3": {"class_type": "KSampler", "inputs": {"seed": 1, "model": ["4", 0]}},
    "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "a.safetensors"}},
    "9": {"class_type": "SaveImage", "inputs": {"images": ["3", 0], "filename_prefix": "x"}},
}


class FakeComfy(BaseHTTPRequestHandler):
    state = {}

    def log_message(self, *args):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        s = self.state
        s.setdefault("auth", []).append(self.headers.get("Authorization"))
        url = urlparse(self.path)
        if url.path == "/system_stats":
            return self._json(
                200, {"system": {"comfyui_version": "0.0-test"}, "devices": [{"name": "cpu"}]}
            )
        if url.path == "/object_info":
            return self._json(200, {k: {} for k in s.get("nodes", [])})
        if url.path.startswith("/history/"):
            s["polls"] = s.get("polls", 0) + 1
            if s["polls"] < s.get("ready_after", 1):
                return self._json(200, {})
            return self._json(200, s.get("history", {}))
        if url.path == "/view":
            q = parse_qs(url.query)
            s.setdefault("views", []).append(q)
            body = b"PNGDATA-" + q["filename"][0].encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return None
        return self._json(404, {})

    def do_POST(self):
        s = self.state
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        if self.path == "/prompt":
            s["submitted"] = json.loads(body)
            if s.get("reject"):
                return self._json(
                    400,
                    {
                        "error": {"type": "prompt_outputs_failed_validation"},
                        "node_errors": {"3": {"errors": ["bad"], "class_type": "KSampler"}},
                    },
                )
            return self._json(200, {"prompt_id": "p1", "number": 0, "node_errors": {}})
        if self.path == "/upload/image":
            s["upload_body"] = body
            sub = b'name="subfolder"\r\n\r\nrefs' in body
            return self._json(
                200, {"name": "photo.png", "subfolder": "refs" if sub else "", "type": "input"}
            )
        return self._json(404, {})


class ComfyRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeComfy)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = "http://127.0.0.1:%d" % cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        FakeComfy.state = {"nodes": ["KSampler", "CheckpointLoaderSimple", "SaveImage"]}
        os.environ["COMFYUI_URL"] = self.url
        os.environ.pop("COMFYUI_TOKEN", None)
        self.tmp = tempfile.TemporaryDirectory()
        self.graph_path = os.path.join(self.tmp.name, "g.json")
        with open(self.graph_path, "w") as fh:
            json.dump(GRAPH, fh)

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = comfy_run.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_check_reports_missing_nodes(self):
        FakeComfy.state["nodes"] = ["KSampler", "SaveImage"]
        code, out, _ = self.call("check", self.graph_path)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["missing_class_types"], ["CheckpointLoaderSimple"])

    def test_check_without_graph(self):
        code, out, _ = self.call("check")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["comfyui_version"], "0.0-test")

    def test_run_sets_inputs_and_downloads_outputs(self):
        FakeComfy.state.update(
            ready_after=2,
            history={
                "p1": {
                    "status": {"status_str": "success", "completed": True},
                    "outputs": {
                        "9": {
                            "images": [
                                {"filename": "x_001.png", "subfolder": "", "type": "output"},
                                {"filename": "prev.png", "subfolder": "", "type": "temp"},
                            ]
                        }
                    },
                }
            },
        )
        out_dir = os.path.join(self.tmp.name, "out")
        code, out, _ = self.call(
            "run", self.graph_path, "--set", "3.seed=42", "--set", '9.filename_prefix="hero"',
            "--out", out_dir, "--poll", "0",
        )
        self.assertEqual(code, 0, out)
        sent = FakeComfy.state["submitted"]["prompt"]
        self.assertEqual(sent["3"]["inputs"]["seed"], 42)
        self.assertEqual(sent["9"]["inputs"]["filename_prefix"], "hero")
        files = json.loads(out)["files"]
        self.assertEqual(len(files), 1)
        with open(files[0]["path"], "rb") as fh:
            self.assertEqual(fh.read(), b"PNGDATA-x_001.png")

    def test_run_rejected_graph_returns_node_errors(self):
        FakeComfy.state["reject"] = True
        code, out, _ = self.call("run", self.graph_path)
        self.assertEqual(code, 2)
        self.assertIn("3", json.loads(out)["node_errors"])

    def test_run_timeout_keeps_prompt_id(self):
        FakeComfy.state["ready_after"] = 10**6
        code, out, _ = self.call("run", self.graph_path, "--timeout", "0", "--poll", "0")
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(out), {"prompt_id": "p1", "status": "pending"})

    def test_run_error_status(self):
        FakeComfy.state["history"] = {"p1": {"status": {"status_str": "error", "completed": False}}}
        code, _, _ = self.call("run", self.graph_path, "--poll", "0")
        self.assertEqual(code, 4)

    def test_ui_format_is_rejected(self):
        with open(self.graph_path, "w") as fh:
            json.dump({"nodes": [{"id": 1, "type": "KSampler"}], "links": []}, fh)
        code, _, err = self.call("run", self.graph_path)
        self.assertEqual(code, 1)
        self.assertIn("UI-format", err)

    def test_set_unknown_node(self):
        code, _, err = self.call("run", self.graph_path, "--set", "77.seed=1")
        self.assertEqual(code, 1)
        self.assertIn("77", err)

    def test_upload_returns_load_image_value(self):
        img = os.path.join(self.tmp.name, "photo.png")
        with open(img, "wb") as fh:
            fh.write(b"\x89PNG")
        code, out, _ = self.call("upload", img, "--subfolder", "refs")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["load_image_value"], "refs/photo.png")
        self.assertIn(b'filename="photo.png"', FakeComfy.state["upload_body"])

    def test_token_sent_but_never_printed(self):
        os.environ["COMFYUI_TOKEN"] = "sekrit-token"
        try:
            code, out, err = self.call("check")
        finally:
            os.environ.pop("COMFYUI_TOKEN")
        self.assertEqual(code, 0)
        self.assertIn("Bearer sekrit-token", FakeComfy.state["auth"])
        self.assertNotIn("sekrit", out + err)

    def test_missing_url(self):
        os.environ.pop("COMFYUI_URL")
        code, _, err = self.call("check")
        self.assertEqual(code, 1)
        self.assertIn("COMFYUI_URL", err)


if __name__ == "__main__":
    unittest.main()
