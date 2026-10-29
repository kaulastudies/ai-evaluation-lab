"""Loopback-only judge UI with genuine source-exact replay and optional Nebius run.

Not a multi-tenant code execution service. Use a disposable development environment
for fresh model candidates; the existing runner's AST admission is not OS isolation.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from build_evidence import CASES, HERE, PROGRAM, ROOT, evidence_path

TOKEN = secrets.token_urlsafe(32)
BUSY = threading.Lock()
MODEL = "nvidia/nemotron-3-super-120b-a12b"


def execute(command: list[str], *, live: bool = False) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["NEBIUS_MODEL"] = MODEL
    if not live:
        env.pop("NEBIUS_API_KEY", None)
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=180)
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        # Provider errors may include response bodies. Do not reflect them to the UI.
        raise RuntimeError("Runner did not return a JSON report; inspect the local terminal and provider configuration.")
    return {"exit_code": result.returncode, "elapsed_ms": round((time.monotonic() - started) * 1000), "report": report}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        super().end_headers()

    def respond(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self) -> bool:
        port = self.server.server_port
        return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def do_GET(self):
        if not self.valid_host():
            return self.respond(403, {"error": "Loopback Host required"})
        if self.path == "/api/status":
            return self.respond(200, {"mode": "local", "csrf": TOKEN, "live_available": bool(os.getenv("NEBIUS_API_KEY")), "model": MODEL})
        # Serve only intended UI assets, never arbitrary source or local files.
        runtime_manifest = json.loads((HERE / "browser-runtime.json").read_text())
        assets = {"/", "/index.html", "/app.js", "/style.css", "/evidence.json", "/lab.js", "/lab-worker.mjs", "/browser_lab.py", "/browser-evidence.json"}
        assets.update("/vendor/pyodide/" + f["name"] for f in runtime_manifest["files"])
        if self.path.split("?")[0] not in assets:
            return self.respond(404, {"error": "Not found"})
        return super().do_GET()

    def do_POST(self):
        origin = self.headers.get("Origin")
        expected = f"http://{self.headers.get('Host')}"
        if not self.valid_host() or origin != expected or not secrets.compare_digest(self.headers.get("X-ProofGate-Token", ""), TOKEN):
            return self.respond(403, {"error": "Same-origin local session required"})
        if self.path not in {"/api/replay", "/api/run", "/api/repair"}:
            return self.respond(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024:
                raise ValueError()
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, json.JSONDecodeError):
            return self.respond(400, {"error": "A small JSON object is required"})
        if not BUSY.acquire(blocking=False):
            return self.respond(409, {"error": "A verification is already running"})
        try:
            if self.path == "/api/replay":
                case = body.get("case")
                if not isinstance(case, str) or case not in CASES:
                    return self.respond(400, {"error": "Unknown evidence case"})
                folder = evidence_path(case)
                manifest = json.loads((folder / "manifest.json").read_text())
                script = "repair_replay.py" if manifest.get("attempt_kind", "initial") == "repair" else "replay.py"
                result = execute([sys.executable, str(PROGRAM / "runner" / script), "--evidence-dir", str(folder)])
                return self.respond(200, {"mode": "executed_no_model_replay", **result})
            if not os.getenv("NEBIUS_API_KEY"):
                return self.respond(503, {"error": "Set NEBIUS_API_KEY in the server environment, then restart. No model call was made."})
            dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
            if dirty:
                return self.respond(409, {"error": "Commit source changes before a fresh run so its source commit is reproducible."})
            label = "proofgate-nebius-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + secrets.token_hex(3)
            output = ROOT / "runs/live/rarb" / label
            output.mkdir(parents=True, exist_ok=False)
            is_repair = self.path == "/api/repair"
            command = [sys.executable, str(PROGRAM / "runner" / ("repair.py" if is_repair else "model_trial.py")),
                "--task", "AP-005" if is_repair else "AP-001", "--provider", "nebius", "--label", label,
                "--output-protocol", "strict-code-only-v2",
                "--out", str(output / "evaluation.json"),
                "--response-out", str(output / "model-response.txt"),
                "--candidate-out", str(output / ("candidate-record_transformer.py" if is_repair else "candidate-resource_view.py")),
                "--manifest-out", str(output / "manifest.json"),
            ]
            if is_repair:
                command += ["--parent-evidence", str(evidence_path("false-green")), "--repair-index", "1", "--max-diagnostic-chars", "600"]
            result = execute(command, live=True)
            return self.respond(200, {"mode": "fresh_nebius_repair" if is_repair else "fresh_nebius_inference", "staging_path": output.relative_to(ROOT).as_posix(), **result})
        except subprocess.TimeoutExpired:
            return self.respond(504, {"error": "Runner exceeded 180 seconds. No successful result is claimed."})
        except Exception as exc:
            print(f"ProofGate operation failed: {type(exc).__name__}", file=sys.stderr)
            return self.respond(500, {"error": "Execution failed. No successful result is claimed. Check the local configuration."})
        finally:
            BUSY.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"ProofGate: http://127.0.0.1:{server.server_port}", flush=True)
    print("Fresh model candidates execute locally. Use a disposable development environment.", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
