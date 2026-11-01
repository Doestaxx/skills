import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
import unittest.mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "doestaxx" / "scripts"))

import fal_run  # noqa: E402


class FakeFal(BaseHTTPRequestHandler):
    state = {}

    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="application/json"):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        s = self.state
        s["auth"] = self.headers.get("Authorization")
        length = int(self.headers.get("Content-Length", 0))
        s["submitted"] = json.loads(self.rfile.read(length) or b"{}")
        s["submit_path"] = self.path
        if s.get("reject"):
            return self._send(422, {"detail": "bad input"})
        base = f"http://127.0.0.1:{self.server.server_port}/fal-ai/flux/requests/r1"
        self._send(200, {"request_id": "r1", "status_url": base + "/status", "response_url": base})

    def do_GET(self):
        s = self.state
        port = self.server.server_port
        if self.path.endswith("/status"):
            s["polls"] = s.get("polls", 0) + 1
            if s.get("never_done") or s["polls"] < 2:
                return self._send(200, {"status": "IN_PROGRESS"})
            return self._send(200, {"status": s.get("final", "COMPLETED")})
        if self.path == "/fal-ai/flux/requests/r1":
            return self._send(
                200,
                {
                    "images": [{"url": f"http://127.0.0.1:{port}/media/a.png"}],
                    "video": {"url": f"http://127.0.0.1:{port}/media/b.mp4"},
                    "seed": 7,
                },
            )
        if self.path.startswith("/media/"):
            s.setdefault("media_auth", []).append(self.headers.get("Authorization"))
            return self._send(200, b"bytes:" + self.path.encode(), "application/octet-stream")
        self._send(404, {"detail": "not found"})


class FalRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeFal)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        FakeFal.state = {}
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {
            "FAL_KEY": "secret-key",
            "FAL_QUEUE_URL": f"http://127.0.0.1:{self.server.server_port}",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, argv, env=None):
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.dict(os.environ, env if env is not None else self.env, clear=True):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = fal_run.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_run_submits_waits_and_downloads(self):
        out_dir = os.path.join(self.tmp.name, "o")
        code, out, err = self.run_main(
            ["run", "fal-ai/flux/dev", "--input", '{"prompt": "a lantern"}', "--set", "num_images=2",
             "--set", "image_size.width=1024", "--out", out_dir, "--poll", "0.01"]
        )
        self.assertEqual(code, 0, err)
        s = FakeFal.state
        self.assertEqual(s["submit_path"], "/fal-ai/flux/dev")
        self.assertEqual(s["auth"], "Key secret-key")
        self.assertEqual(s["submitted"], {"prompt": "a lantern", "num_images": 2, "image_size": {"width": 1024}})
        report = json.loads(out)
        self.assertEqual(len(report["files"]), 2)
        self.assertTrue(report["files"][0].endswith("01-a.png"))
        self.assertEqual(Path(report["files"][1]).read_bytes(), b"bytes:/media/b.mp4")
        self.assertEqual(s["media_auth"], [None, None])
        self.assertTrue(os.path.exists(os.path.join(out_dir, "request.json")))

    def test_key_is_never_printed(self):
        FakeFal.state = {"reject": True}
        code, out, err = self.run_main(["run", "fal-ai/flux/dev", "--out", self.tmp.name])
        self.assertEqual(code, 1)
        self.assertNotIn("secret-key", out + err)

    def test_missing_key_is_a_usage_error(self):
        env = {"FAL_QUEUE_URL": self.env["FAL_QUEUE_URL"]}
        code, _, err = self.run_main(["run", "fal-ai/flux/dev", "--out", self.tmp.name], env)
        self.assertEqual(code, 1)
        self.assertIn("FAL_KEY", err)

    def test_timeout_exits_3_and_resume_finishes(self):
        FakeFal.state = {"never_done": True}
        out_dir = os.path.join(self.tmp.name, "t")
        code, _, err = self.run_main(
            ["run", "fal-ai/flux/dev", "--out", out_dir, "--timeout", "0.05", "--poll", "0.01"]
        )
        self.assertEqual(code, 3)
        self.assertIn("resume", err)
        FakeFal.state["never_done"] = False
        code, out, err = self.run_main(["resume", out_dir, "--poll", "0.01"])
        self.assertEqual(code, 0, err)
        self.assertEqual(len(json.loads(out)["files"]), 2)

    def test_unknown_terminal_status_exits_4(self):
        FakeFal.state = {"final": "FAILED"}
        code, _, _ = self.run_main(["run", "fal-ai/flux/dev", "--out", self.tmp.name, "--poll", "0.01"])
        self.assertEqual(code, 4)

    def test_file_becomes_data_uri(self):
        img = os.path.join(self.tmp.name, "ref.png")
        Path(img).write_bytes(b"\x89PNG")
        code, _, err = self.run_main(
            ["run", "fal-ai/flux/dev", "--file", "image_url=" + img, "--out", self.tmp.name, "--poll", "0.01"]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(FakeFal.state["submitted"]["image_url"], "data:image/png;base64,iVBORw==")

    def test_bad_set_is_rejected(self):
        code, _, err = self.run_main(["run", "m", "--set", "novalue", "--out", self.tmp.name])
        self.assertEqual(code, 1)
        self.assertIn("KEY=VALUE", err)

    def test_media_urls_dedupes_and_ignores_non_url_keys(self):
        found = fal_run.media_urls({"a": [{"url": "https://x/1"}, {"url": "https://x/1"}], "b": {"href": "https://x/2"}})
        self.assertEqual(found, ["https://x/1"])


if __name__ == "__main__":
    unittest.main()
