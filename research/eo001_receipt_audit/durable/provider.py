"""Original local reference provider: SQLite effects plus Ed25519 receipts.

It extends the *semantics* of the Forge fixture; it is not Systemia or Forge code.
Run only in disposable directories. The SQL row is the entire synthetic effect.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .protocol import VERSION, canonical, digest, exact, label, parse_json, public_id, request_valid, require, sign


def connect(path):
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.execute("PRAGMA busy_timeout=10000")
    db.execute("PRAGMA synchronous=FULL")
    return db


def initialize(directory: Path, store_id=None):
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    key = Ed25519PrivateKey.generate()
    fd = os.open(directory / "issuer.key", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(key.private_bytes_raw())
        handle.flush()
        os.fsync(handle.fileno())
    public_key = key.public_key().public_bytes_raw()
    store_id = store_id or "store-" + secrets.token_hex(16)
    require(label(store_id), "STORE_ID")
    db = connect(directory / "provider.sqlite")
    require(db.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal", "WAL_UNAVAILABLE")
    db.executescript("""
      CREATE TABLE metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL);
      CREATE TABLE effects (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_id TEXT NOT NULL UNIQUE,
        idempotency_key TEXT NOT NULL UNIQUE,
        request_sha256 TEXT NOT NULL,
        receipt_json TEXT NOT NULL);
      CREATE TABLE events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        method TEXT NOT NULL, request_sha256 TEXT NOT NULL,
        challenge TEXT NOT NULL, status TEXT NOT NULL);
    """)
    db.executemany("INSERT INTO metadata VALUES (?,?)", [("store_id", store_id), ("issuer_id", public_id(public_key))])
    db.close()
    os.chmod(directory / "provider.sqlite", 0o600)
    return {"public_key_hex": public_key.hex(), "store_id": store_id}


def snapshot_from_connection(db):
    effects = [json.loads(row[0]) for row in db.execute("SELECT receipt_json FROM effects ORDER BY seq")]
    events = [dict(zip(("seq", "method", "request_sha256", "challenge", "status"), row))
              for row in db.execute("SELECT seq,method,request_sha256,challenge,status FROM events ORDER BY seq")]
    return {"effects": effects, "events": events, "effect_count": len(effects), "event_count": len(events)}


def read_snapshot(directory):
    """Evaluator-owned SQL read, using a separate read-only connection."""
    uri = (Path(directory).resolve() / "provider.sqlite").as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    try:
        db.execute("BEGIN")
        require(db.execute("PRAGMA quick_check").fetchone()[0] == "ok", "DATABASE_INTEGRITY")
        return snapshot_from_connection(db)
    finally:
        db.close()


def wait_at_boundary(marker):
    Path(marker).write_text("ready", encoding="ascii")
    # The evaluator kills this process after reading the marker. Time out if it
    # disappears instead of leaving an orphan waiting forever.
    time.sleep(20)
    raise RuntimeError("fault controller did not kill the paused process")


def operate(directory, command, pause=None, marker=None):
    exact(command, {"method", "request", "challenge"}, "COMMAND_SHAPE")
    method, request, challenge = (command[k] for k in ("method", "request", "challenge"))
    require(method in ("execute", "lookup", "snapshot") and label(challenge), "COMMAND_VALUE")
    if method != "snapshot":
        request_valid(request)
    else:
        require(request is None, "SNAPSHOT_REQUEST")
    key = Ed25519PrivateKey.from_private_bytes((Path(directory) / "issuer.key").read_bytes())
    db = connect(Path(directory) / "provider.sqlite")
    try:
        meta = dict(db.execute("SELECT name,value FROM metadata"))
        require(meta["issuer_id"] == public_id(key.public_key().public_bytes_raw()), "ISSUER_KEY_CHANGED")
        base = {"version": VERSION, "issuer_id": meta["issuer_id"], "store_id": meta["store_id"]}
        if method == "snapshot":
            db.execute("BEGIN")
            snapshot = snapshot_from_connection(db)
            db.commit()
            return sign(key, {**base, "kind": "closing-manifest", "challenge": challenge, "snapshot": snapshot})
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT request_sha256,receipt_json FROM effects WHERE operation_id=? OR idempotency_key=?",
                         (request["operation_id"], request["idempotency_key"])).fetchall()
        status, receipt = "not_found", None
        if row:
            if len(row) == 1 and row[0][0] == digest(request):
                status, receipt = "settled", json.loads(row[0][1])
            else:
                status = "conflict"
        elif method == "execute":
            cursor = db.execute("INSERT INTO effects(operation_id,idempotency_key,request_sha256,receipt_json) VALUES (?,?,?,?)",
                                (request["operation_id"], request["idempotency_key"], digest(request), "{}"))
            seq = cursor.lastrowid
            receipt = sign(key, {**base, "kind": "settlement", "request": request,
                                "receipt_id": "synthetic-effect-" + str(seq), "sequence": seq, "settled": True})
            db.execute("UPDATE effects SET receipt_json=? WHERE seq=?", (canonical(receipt).decode(), seq))
            status = "settled"
        db.execute("INSERT INTO events(method,request_sha256,challenge,status) VALUES (?,?,?,?)",
                   (method, digest(request), challenge, status))
        if pause == "before_commit": wait_at_boundary(marker)
        db.commit()
        if pause == "after_commit": wait_at_boundary(marker)
        return sign(key, {**base, "kind": "observation", "request_sha256": digest(request),
                          "challenge": challenge, "method": method, "status": status, "receipt": receipt})
    finally:
        db.close()  # uncommitted work rolls back, including the before-commit control


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--pause", choices=("before_commit", "after_commit"))
    parser.add_argument("--marker", type=Path)
    parser.add_argument("--start-gate", type=Path)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    try:
        command = parse_json(sys.stdin.buffer.read(65537))
        require(not args.pause or args.marker is not None, "FAULT_MARKER_REQUIRED")
        if args.start_gate:
            require(args.ready is not None, "READY_MARKER_REQUIRED")
            args.ready.write_text("ready")
            deadline = time.monotonic() + 10
            while not args.start_gate.exists():
                require(time.monotonic() < deadline, "START_GATE_TIMEOUT")
                time.sleep(0.005)
        envelope = operate(args.directory, command, args.pause, args.marker)
        print(canonical(envelope).decode(), flush=True)
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"transport_error": type(exc).__name__, "detail": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
