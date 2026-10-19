"""ProofQ Verify API: dependency-free local HTTP endpoint for supported quantum audits.

Bind to loopback only. Experimental software, not an internet production service.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from research.futureproof_eval.qproof_audit import audit

MAX_BYTES = 128 * 1024

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            return self.reply(404, {"error": "not_found"})
        return self.reply(200, {"status": "ok", "service": "ProofQ Verify", "version": "0.1"})
    def do_POST(self):
        if self.path != "/v1/quantum/audit":
            return self.reply(404, {"error": "not_found"})
        try:
            length = int(self.headers.get("Content-Length", "-1"))
            if not 0 < length <= MAX_BYTES:
                return self.reply(413, {"error": "invalid_content_length"})
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("JSON root must be an object")
            result = audit(data)
        except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self.reply(400, {"error": "invalid_input", "detail": str(exc)})
        return self.reply(200, result)
    def reply(self, status, payload):
        encoded = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)
    def log_message(self, fmt, *args):
        # No raw payload logging.
        return

def serve(host="127.0.0.1", port=8765):
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise ValueError("Public network binding is disabled in prototype")
    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()

if __name__ == "__main__":
    serve(port=int(os.environ.get("PROOFQ_PORT", "8765")))
