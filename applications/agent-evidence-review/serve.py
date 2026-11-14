"""Loopback-only reviewer. Does not execute candidates or contact external APIs."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json

from eval_lab.web_trace import InvalidTrace, MAX_BYTES, parse_trace, review_trace

ROOT = Path(__file__).resolve().parent
STATIC = {"/": ("web/index.html", "text/html"), "/app.js": ("web/app.js", "text/javascript"),
          "/style.css": ("web/style.css", "text/css"), "/examples.json": ("examples.json", "application/json")}


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def reply(self, status, body, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def local_request(self):
        hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in hosts and (origin is None or origin in {"http://" + host for host in hosts})

    def do_GET(self):
        if not self.local_request():
            return self.reply(403, b'{"error":"Local requests only"}')
        if self.path not in STATIC:
            return self.reply(404, b'{"error":"Not found"}')
        file, content_type = STATIC[self.path]
        self.reply(200, (ROOT / file).read_bytes(), content_type)

    def do_POST(self):
        if not self.local_request():
            return self.reply(403, b'{"error":"Local requests only"}')
        if self.path != "/review":
            return self.reply(404, b'{"error":"Not found"}')
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.reply(415, b'{"error":"JSON required"}')
        try:
            if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1:
                raise InvalidTrace("One Content-Length required")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BYTES:
                raise InvalidTrace("Trace must be at most 1 MB")
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise InvalidTrace("Incomplete request")
            report = review_trace(parse_trace(raw))
        except (ValueError, TimeoutError) as exc:
            return self.reply(400, json.dumps({"error": str(exc)}).encode())
        self.reply(200, json.dumps(report).encode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Agent Evidence Review: http://127.0.0.1:{server.server_port}", flush=True)
    server.serve_forever()
