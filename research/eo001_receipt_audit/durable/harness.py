"""Evaluator-controlled processes, fault boundaries and read-only state capture."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import secrets
import subprocess
import sys
import time
from . import provider
from .protocol import canonical, parse_json, require, verify_manifest

ROOT = Path(__file__).resolve().parents[3]
PROVIDER_MODULE = "research.eo001_receipt_audit.durable.provider"
REQUEST = {"operation_id": "purchase-001", "order_id": "DEMO-1001", "amount_minor": 4200,
           "currency": "USD", "idempotency_key": "purchase-001-key"}


def wait_for(paths, processes, timeout=8):
    deadline = time.monotonic() + timeout
    while not all(p.exists() for p in paths):
        require(all(p.poll() is None for p in processes), "PROVIDER_EXITED_BEFORE_BOUNDARY")
        require(time.monotonic() < deadline, "BOUNDARY_TIMEOUT")
        time.sleep(0.005)


class ProviderLab:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.trust = provider.initialize(self.directory)
        self.calls = []

    @property
    def public_key(self):
        return bytes.fromhex(self.trust["public_key_hex"])

    @property
    def store_id(self):
        return self.trust["store_id"]

    def command(self, method, request):
        return {"method": method, "request": request, "challenge": "query-" + secrets.token_hex(16)}

    def start(self, command, *args):
        p = subprocess.Popen([sys.executable, "-m", PROVIDER_MODULE, "--directory", str(self.directory), *map(str, args)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT)
        p.stdin.write(canonical(command))
        p.stdin.close()
        p.stdin = None
        return p

    def finish(self, p, command):
        try:
            raw, error = p.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
            raise
        require(p.returncode == 0, "PROVIDER_ERROR: " + error.decode()[:300])
        envelope = parse_json(raw)
        record = {"command": command, "transport": "received", "envelope": envelope}
        if command["method"] != "snapshot": self.calls.append(record)
        return record

    def call(self, method, request=REQUEST):
        command = self.command(method, request)
        return self.finish(self.start(command), command)

    def killed_call(self, phase, request=REQUEST):
        command = self.command("execute", request)
        marker = self.directory / ("fault-" + secrets.token_hex(8))
        p = self.start(command, "--pause", phase, "--marker", marker)
        try:
            wait_for([marker], [p])
            p.kill()  # actual SIGKILL on Linux; no graceful cleanup or exception stand-in
            raw, error = p.communicate(timeout=5)
            require(p.returncode == -9 and not raw, "KILL_DID_NOT_PRECEDE_ACK")
        finally:
            if p.poll() is None:
                p.kill()
                p.communicate()
        record = {"command": command, "transport": "ack_lost", "envelope": None,
                  "fault_boundary": phase, "returncode": p.returncode, "marker_observed": marker.exists(),
                  "stdout_bytes": len(raw)}
        self.calls.append(record)
        return record

    def concurrent(self, requests):
        gate = self.directory / ("gate-" + secrets.token_hex(8))
        commands = [self.command("execute", r) for r in requests]
        ready = [self.directory / (gate.name + "-" + str(i)) for i in range(len(requests))]
        processes = [self.start(c, "--start-gate", gate, "--ready", r) for c, r in zip(commands, ready)]
        try:
            wait_for(ready, processes)
            pids = {p.pid for p in processes}
            require(len(pids) == len(requests), "CONCURRENCY_NOT_MULTIPROCESS")
            gate.write_text("release")
            with ThreadPoolExecutor(max_workers=len(processes)) as pool:
                records = list(pool.map(lambda pair: self.finish(*pair), zip(processes, commands)))
            return {"workers": len(processes), "all_ready_before_release": True, "records": records}
        finally:
            for p in processes:
                if p.poll() is None:
                    p.kill()
                    p.communicate()

    def close_evidence(self):
        # Called only after every worker has exited. The independent read and
        # signed close must describe the same quiescent database state.
        snapshot = provider.read_snapshot(self.directory)
        close = self.call("snapshot", None)
        verified = verify_manifest(close["envelope"], self.public_key, self.store_id, close["command"]["challenge"])
        require(canonical(snapshot) == canonical(verified), "MANIFEST_DIFFERS_FROM_SQL_READ")
        return {"trust": self.trust, "calls": self.calls.copy(), "closing": close,
                "read_only_snapshot": snapshot}


def verify_capture(capture):
    """Offline check of a *reviewed* capture, not automatic trust in a new key."""
    public_key = bytes.fromhex(capture["trust"]["public_key_hex"])
    store_id = capture["trust"]["store_id"]
    close = capture["closing"]
    snapshot = verify_manifest(close["envelope"], public_key, store_id, close["command"]["challenge"])
    require(canonical(snapshot) == canonical(capture["read_only_snapshot"]), "CAPTURE_STATE_MISMATCH")
    events = {e["challenge"]: e for e in snapshot["events"]}
    require(len(events) == len(snapshot["events"]), "DUPLICATE_CHALLENGE")
    committed_calls = []
    from .protocol import digest
    for call in capture["calls"]:
        command = call["command"]
        if call.get("fault_boundary") == "before_commit":
            require(command["challenge"] not in events, "UNCOMMITTED_EVENT_PRESENT")
            continue
        event = events.get(command["challenge"])
        require(event is not None and event["method"] == command["method"]
                and event["request_sha256"] == digest(command["request"]), "CALL_COVERAGE_MISMATCH")
        committed_calls.append(command["challenge"])
    require(len(committed_calls) == len(events) and len(set(committed_calls)) == len(events), "MISSING_OR_DUPLICATE_CALL")
    return snapshot
