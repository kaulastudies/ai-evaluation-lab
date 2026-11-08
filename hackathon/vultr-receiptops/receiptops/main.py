import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import audit, provider, sandbox
from .receipts import Signer, canonical, digest, verify

ROOT = Path(__file__).parent
STATE = Path(os.getenv("RECEIPTOPS_STATE", str(ROOT.parent / "runtime")))
STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
SIGNER = Signer(STATE)
LOCK = threading.Lock()
DB = STATE / "runs.sqlite3"

def connection():
    db = sqlite3.connect(DB, timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, day TEXT, kind TEXT, bundle TEXT)")
    return db

with connection() as db:
    pass

app = FastAPI(title="ReceiptOps", docs_url=None, redoc_url=None, openapi_url=None)

class BodyLimit:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            chunks.append(body)
            size += len(body)
            if size > 65536:
                return await JSONResponse({"detail": "Request exceeds 64 KiB."}, status_code=413)(scope, receive, send)
            if not message.get("more_body", False):
                break
        consumed = False
        async def bounded_receive():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()
        await self.app(scope, bounded_receive, send)

app.add_middleware(BodyLimit)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response

class RunRequest(BaseModel):
    csv: str = Field(default=audit.SAMPLE, max_length=32768)

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def start_run(kind: str) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    with connection() as db:
        used = db.execute("SELECT COUNT(*) FROM runs WHERE day=?", (today,)).fetchone()[0]
        if used >= int(os.getenv("DAILY_RUN_LIMIT", "60")):
            raise HTTPException(429, "Today's demonstration budget is used. Try again tomorrow.")
        run_id = uuid.uuid4().hex
        db.execute("INSERT INTO runs VALUES (?, ?, ?, NULL)", (run_id, today, kind))
    return run_id

def save(run_id: str, bundle: dict):
    with connection() as db:
        db.execute("UPDATE runs SET bundle=? WHERE id=?", (json.dumps(bundle), run_id))

@app.get("/api/status")
def status():
    return {"sandbox_ready": sandbox.available(), "inference_ready": provider.ready(),
            "provider": "Vultr Serverless Inference", "model": os.getenv("VULTR_MODEL") or None,
            "public_demo": os.getenv("PUBLIC_DEMO", "1") == "1", "policy": sandbox.POLICY,
            "as_of": audit.AS_OF, "public_key": SIGNER.public, "key_id": SIGNER.key_id,
            "deployment": os.getenv("DEPLOYMENT_LABEL", "Development — Vultr deployment unverified")}

@app.get("/api/sample")
def sample():
    return {"csv": audit.SAMPLE, "as_of": audit.AS_OF, "reference": audit.reference(audit.SAMPLE),
            "label": "Deterministic reference, not an agent execution"}

@app.get("/api/public-key")
def public_key():
    return Response(SIGNER.public + "\n", media_type="text/plain",
                    headers={"Content-Disposition": 'attachment; filename="receiptops-public-key.txt"'})

@app.post("/api/run")
def run(request: RunRequest):
    try:
        audit.read_rows(request.csv)
    except ValueError as error:
        raise HTTPException(400, str(error))
    if os.getenv("PUBLIC_DEMO", "1") == "1" and request.csv != audit.SAMPLE:
        raise HTTPException(400, "This public demo accepts only its fictional sample. Self-host to use other data.")
    if not provider.ready() or not sandbox.available():
        raise HTTPException(503, "Run blocked: Vultr inference and the Docker sandbox must both be ready.")
    if not LOCK.acquire(blocking=False):
        raise HTTPException(429, "Another run is active. Please retry when it finishes.")
    run_id = None
    try:
        run_id = start_run("audit")
        attempts = []
        feedback = ""
        for attempt in range(2):
            generated = provider.generate(feedback)
            execution = sandbox.execute(generated["code"], request.csv)
            candidate = None
            validation = {"passed": False, "differences": ["Execution failed or returned invalid JSON."]}
            if execution["exit_code"] == 0 and not execution["timed_out"] and not execution["output_limited"] and execution["container_removed"]:
                try:
                    candidate = json.loads(execution["stdout"])
                    validation = audit.check(request.csv, candidate)
                except (ValueError, TypeError):
                    pass
            attempts.append({"attempt": attempt + 1, "generated": generated,
                             "execution": execution, "validation": validation})
            if validation["passed"]:
                break
            feedback = ", ".join(validation["differences"])
        payload = {"schema": "receiptops.execution.v1", "run_id": run_id,
                   "created_at": utcnow(), "kind": "invoice_audit", "as_of": audit.AS_OF,
                   "input_sha256": digest(request.csv.encode()),
                   "code_sha256": digest(generated["code"].encode()),
                   "stdout_sha256": digest(execution["stdout"].encode()),
                   "provider": generated["provider"], "model": generated["model"],
                   "attempts": len(attempts), "verification": validation,
                   "result": candidate if validation["passed"] else None,
                   "sandbox": {k: v for k, v in execution.items() if k != "stdout"}}
        receipt = SIGNER.sign(payload)
        bundle = {"receipt": receipt, "input_csv": request.csv, "code": generated["code"],
                  "stdout": execution["stdout"], "attempts": attempts}
        save(run_id, bundle)
        return bundle
    except HTTPException:
        raise
    except Exception:
        # Provider response bodies can contain request data: do not expose them.
        if run_id:
            save(run_id, {"error": "Run failed before a verifiable result was available.", "run_id": run_id})
        raise HTTPException(502, "The run could not finish. No successful execution receipt was issued.")
    finally:
        LOCK.release()

@app.post("/api/containment")
def containment():
    if not sandbox.available():
        raise HTTPException(503, "Docker sandbox unavailable; probes were not run.")
    if not LOCK.acquire(blocking=False):
        raise HTTPException(429, "Another run is active.")
    try:
        run_id = start_run("containment")
        probe = sandbox.execute(sandbox.PROBE, audit.SAMPLE)
        checks = json.loads(probe["stdout"]) if probe["exit_code"] == 0 else {}
        expected_checks = {"network_blocked", "input_read_only", "root_read_only", "non_root", "inference_key_absent", "docker_socket_absent"}
        timeout = sandbox.execute("while True: pass\n", audit.SAMPLE, timeout=2)
        checks["time_limit_enforced"] = timeout["timed_out"]
        checks["containers_removed"] = probe["container_removed"] and timeout["container_removed"]
        passed = set(checks) == expected_checks | {"time_limit_enforced", "containers_removed"} and all(v is True for v in checks.values())
        payload = {"schema": "receiptops.containment.v1", "run_id": run_id,
                   "created_at": utcnow(), "kind": "containment_probe", "checks": checks,
                   "passed": passed, "policy": sandbox.POLICY, "probe": probe, "timeout_probe": timeout,
                   "limitation": "Fixed probes observe these controls; they do not certify resistance to kernel escapes."}
        bundle = {"receipt": SIGNER.sign(payload)}
        save(run_id, bundle)
        return bundle
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502, "Containment probes did not complete; no pass is claimed.")
    finally:
        LOCK.release()

@app.post("/api/verify")
def verify_receipt(receipt: dict):
    return {"valid": verify(receipt, SIGNER.public), "trusted_key_id": SIGNER.key_id,
            "scope": "Signature and integrity against this server's key. Use the offline verifier to recompute the invoice result."}

@app.get("/api/runs/{run_id}")
def download(run_id: str):
    if not __import__("re").fullmatch(r"[0-9a-f]{32}", run_id):
        raise HTTPException(404)
    with connection() as db:
        row = db.execute("SELECT bundle FROM runs WHERE id=?", (run_id,)).fetchone()
    if not row or not row[0]:
        raise HTTPException(404)
    return Response(row[0], media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="receiptops-{run_id}.json"'})

app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")
