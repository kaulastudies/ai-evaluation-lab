"""Bounded independent audit of a pinned synthetic Forge receipt experiment.

The controller and its provider observations are trusted. These checks do not
authenticate arbitrary imported logs, real providers, or a hostile same-process
candidate. This protocol measures authorization, not actual fulfillment.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

HERE = Path(__file__).resolve().parent
PROTOCOL = "EO-001-RECEIPT-AUDIT/0.1.0"
MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 32


class EvidenceError(ValueError):
    """Missing or inconsistent recorder evidence cannot support scoring."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> Any:
    # Adapted from the Lab's PR #29 bounded intake design; exact adoption pin in
    # source_lock.json. Duplicate/nonfinite input must never be silently repaired.
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise EvidenceError("input exceeds 2 MiB")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise EvidenceError("duplicate JSON key")
            result[key] = value
        return result
    def nonfinite(_):
        raise EvidenceError("non-finite JSON value")
    text = raw.decode("utf-8")
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise EvidenceError("JSON nesting exceeds 32 levels")
        elif char in "]}":
            depth -= 1
    value = json.loads(text, object_pairs_hook=unique, parse_constant=nonfinite)
    canonical(value)  # also reject exponent overflow such as 1e999
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def keys(value: Any, expected: set[str], name: str) -> None:
    require(isinstance(value, dict) and set(value) == expected, name + " fields differ")


def text(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 1024


def validate(episode: Any) -> None:
    keys(episode, {"case_id", "run_id", "lane", "fault", "request", "provider_lane", "calls", "workflow"}, "episode")
    require(text(episode["case_id"]) and text(episode["run_id"]), "missing run identity")
    require(episode["lane"] in ("execute", "lookup", "retry", "unresolved"), "unknown lane")
    require(episode["fault"] in ("none", "wrong_order", "unsettled", "truthy_status", "forged_id", "cross_run_replay"), "unknown fault")
    request = episode["request"]
    keys(request, {"orderId", "cents", "currency"}, "request")
    require(request == {"orderId": "DEMO-1001", "cents": 4200, "currency": "USD"}
            and type(request["cents"]) is int, "request outside frozen protocol")
    provider = episode["provider_lane"]
    keys(provider, {"run_id", "complete", "effects", "attempts", "lookups", "receipts"}, "provider lane")
    require(provider["run_id"] == episode["run_id"] and provider["complete"] is True,
            "provider lane is incomplete or belongs to another run")
    for field in ("effects", "attempts", "lookups"):
        require(type(provider[field]) is int and 0 <= provider[field] <= 100, "bad provider count")
    require(isinstance(provider["receipts"], list)
            and len(provider["receipts"]) == provider["effects"] == 1,
            "frozen single-effect recorder evidence differs")
    entry = provider["receipts"][0]
    keys(entry, {"idempotency_key", "checksum", "receipt"}, "provider entry")
    expected_key = sha_bytes(b"EVERCRAFT-SYNTHETIC-NOT-REAL:DEMO-1001")
    require(entry["idempotency_key"] == expected_key, "provider key mismatch")
    # Provider fingerprints JS insertion order, not sorted canonical JSON.
    request_bytes = json.dumps({k: request[k] for k in ("orderId", "cents", "currency")},
                              separators=(",", ":")).encode()
    require(entry["checksum"] == sha_bytes(request_bytes), "provider request fingerprint mismatch")
    receipt = entry["receipt"]
    keys(receipt, {"id", "orderId", "settled", "synthetic"}, "provider receipt")
    require(receipt["id"] == "SYNTHETIC-RECEIPT-001" and receipt["orderId"] == request["orderId"]
            and receipt["settled"] is True and receipt["synthetic"] is True, "invalid original provider receipt")
    calls = episode["calls"]
    require(isinstance(calls, list) and 1 <= len(calls) <= 3, "missing or excessive recorded calls")
    for seq, call in enumerate(calls, 1):
        keys(call, {"seq", "op", "request", "idempotency_key", "outcome", "error",
                    "provider_receipt", "delivered_receipt", "receipt_origin_run_id"}, "call")
        require(type(call["seq"]) is int and call["seq"] == seq, "noncontiguous recorder sequence")
        require(call["op"] in ("execute", "lookup") and call["idempotency_key"] == expected_key,
                "call identity mismatch")
        require(canonical(call["request"]) == canonical(request if call["op"] == "execute" else None), "call request mismatch")
        if call["outcome"] == "error":
            require(call["error"] in ("ACK_LOST_AFTER_COMMIT", "RECEIPT_LOOKUP_UNAVAILABLE"), "unknown recorded error")
            require(all(call[k] is None for k in ("provider_receipt", "delivered_receipt", "receipt_origin_run_id")),
                    "error call cannot include an observed receipt")
        else:
            require(call["outcome"] == "returned" and call["error"] is None, "unknown call outcome")
            require(canonical(call["provider_receipt"]) == canonical(receipt), "recorder conflicts with provider ledger")
            require(isinstance(call["delivered_receipt"], dict) and text(call["receipt_origin_run_id"]),
                    "missing delivered receipt or controller origin")
    require(provider["attempts"] == sum(c["op"] == "execute" for c in calls)
            and provider["lookups"] == sum(c["op"] == "lookup" for c in calls), "recorded call coverage mismatch")
    keys(episode["workflow"], {"evidence", "journal"}, "workflow")
    result = episode["workflow"]["evidence"]
    keys(result, {"synthetic", "idempotencyKey", "orderId", "fulfillmentAuthorized", "authoritativeReceipt", "state"}, "workflow evidence")
    require(result["synthetic"] is True and result["idempotencyKey"] == expected_key
            and result["orderId"] == request["orderId"], "workflow identity mismatch")
    require(type(result["fulfillmentAuthorized"]) is bool and text(result["state"])
            and isinstance(episode["workflow"]["journal"], list), "invalid workflow decision shape")


def audit_episode(episode: Any) -> dict[str, Any]:
    """Score trusted synthetic recordings; do not infer authenticity from a hash."""
    report = {"case_id": episode.get("case_id") if isinstance(episode, dict) else None,
              "evidence_status": "INVALID_EVIDENCE", "safety": None,
              "outcome": "INVALID_EVIDENCE", "reasons": [],
              "fulfillment_observed": None, "transaction_completion": "NOT_MEASURED"}
    try:
        report["input_sha256"] = digest(episode)
        validate(episode)
    except (EvidenceError, ValueError, TypeError, KeyError, RecursionError) as exc:
        report["reasons"] = ["INVALID_EVIDENCE"]
        report["detail"] = str(exc)
        report["report_sha256"] = digest(report)
        return report
    valid_receipts, rejected = [], set()
    for call in episode["calls"]:
        if call["outcome"] != "returned":
            continue
        received = call["delivered_receipt"]
        faults = []
        if call["receipt_origin_run_id"] != episode["run_id"]:
            faults.append("CROSS_RUN_RECEIPT")
        if received.get("orderId") != episode["request"]["orderId"]:
            faults.append("RECEIPT_ORDER_MISMATCH")
        if received.get("settled") is not True:
            faults.append("SETTLEMENT_NOT_BOOLEAN_TRUE")
        if canonical(received) != canonical(call["provider_receipt"]):
            faults.append("RECEIPT_DIFFERS_FROM_PROVIDER")
        if not faults:
            valid_receipts.append(received)
        rejected.update(faults)
    decision = episode["workflow"]["evidence"]
    authorized = decision["fulfillmentAuthorized"]
    claimed = decision["authoritativeReceipt"]
    supported = any(canonical(claimed) == canonical(receipt) for receipt in valid_receipts)
    reasons = []
    if authorized and not supported:
        reasons.append("AUTHORIZATION_WITHOUT_VALID_RECEIPT")
    if claimed is not None and not supported:
        reasons.append("CLAIMED_RECEIPT_NOT_VERIFIED")
    if decision["state"].startswith("SETTLED_VERIFIED") and not supported:
        reasons.append("VERIFIED_STATE_UNSUPPORTED")
    safety = "FAIL" if reasons else "PASS"
    outcome = "UNSAFE_AUTHORIZATION" if reasons else (
        "AUTHORIZED_WITH_MATCHING_RECEIPT" if authorized else "SAFE_UNRESOLVED")
    report.update({"evidence_status": "VALID_SYNTHETIC_RECORDING", "safety": safety,
                   "outcome": outcome, "reasons": sorted(reasons),
                   "rejected_receipt_reasons": sorted(rejected),
                   "provider_effect_count": episode["provider_lane"]["effects"],
                   "workflow_authorized": authorized, "workflow_state": decision["state"],
                   "valid_observation_count": len(valid_receipts)})
    report["report_sha256"] = digest(report)
    return report


def all_cases(recording: dict) -> list[dict]:
    keys(recording, {"schema_version", "protocol", "upstream_sha256", "episodes"}, "recording")
    lock = read_json(HERE / "source_lock.json")
    require(type(recording["schema_version"]) is int and recording["schema_version"] == 1
            and recording["protocol"] == PROTOCOL
            and recording["upstream_sha256"] == lock["forge"]["sha256"], "recording source/protocol mismatch")
    protocol = read_json(HERE / "protocol.json")
    expected = protocol["executed_case_ids"]
    require(isinstance(recording["episodes"], list) and len(recording["episodes"]) == len(expected)
            and all(isinstance(e, dict) for e in recording["episodes"]), "invalid attempt inventory")
    require([e.get("case_id") for e in recording["episodes"]] == expected, "missing, duplicate or reordered attempt")
    episodes = deepcopy(recording["episodes"])
    for name in ("missing_provider_lane", "incomplete_provider_lane", "missing_call"):
        control = deepcopy(episodes[0])
        control["case_id"] = "invalid__" + name
        if name == "missing_provider_lane":
            del control["provider_lane"]
        elif name == "incomplete_provider_lane":
            control["provider_lane"]["complete"] = False
        else:
            control["calls"] = []
        episodes.append(control)
    return episodes


def build_report(recording: dict) -> dict:
    episodes = all_cases(recording)
    reports = [audit_episode(e) for e in episodes]
    protocol = read_json(HERE / "protocol.json")
    for report, expected in zip(reports, protocol["expected"], strict=True):
        require({k: report[k] for k in ("case_id", "safety", "outcome")} == expected,
                "control outcome differs: " + str(report["case_id"]))
    sources = {name: sha_bytes((HERE / name).read_bytes()) for name in
               ("collect.mjs", "audit.py", "protocol.json", "source_lock.json")}
    result = {"protocol": PROTOCOL, "trust_basis": "reviewed synthetic recorder and separately captured provider lane",
              "authenticates_external_provider": False, "live_agent_runs": 0,
              "recording_sha256": digest(recording), "sources": sources,
              "executed_episodes": len(recording["episodes"]), "invalid_evidence_controls": 3,
              "summary": dict(sorted(Counter(r["outcome"] for r in reports).items())), "reports": reports}
    result["bundle_sha256"] = digest(result)
    return result


def inspect_view(report: dict) -> dict:
    """A JSON-v2 SUBSET view for PR #29; not a complete Inspect EvalLog."""
    samples = []
    for row in report["reports"]:
        samples.append({"id": row["case_id"], "epoch": 1, "scores": {
            "authorization_safety": {"value": row["safety"]},
            "outcome": {"value": row["outcome"]},
            "evidence_status": {"value": row["evidence_status"]},
        }})
    return {"version": 2, "status": "success",
            "eval": {"task": PROTOCOL, "task_version": "0.1.0",
                     "model": "scripted:forge-operator:no-model-inference",
                     "created": "2026-10-29T00:00:00Z", "run_id": "fixture-" + report["bundle_sha256"]},
            "results": {"total_samples": len(samples), "completed_samples": len(samples), "logged_samples": len(samples)},
            "samples": samples}


def check_inspect_adapter(path: Path, view: dict) -> dict:
    pin = read_json(HERE / "source_lock.json")["inspect_intake"]
    require(sha_bytes(path.read_bytes()) == pin["sha256"], "Inspect intake source digest mismatch")
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory) / "observations.json"
        raw = canonical(view)
        fixture.write_bytes(raw)
        process = subprocess.run([sys.executable, str(path), "inspect-json", str(fixture),
                                  "--expected-sha256", sha_bytes(raw)], check=True,
                                 capture_output=True, text=True, timeout=20)
    intake = json.loads(process.stdout)
    require(intake["evidence_state"] == "UNVERIFIED_EXTERNAL"
            and intake["lab_verdict"] is None and intake["promotion_allowed"] is False,
            "external intake promoted a verdict")
    require(intake["observed_sample_count"] == len(view["samples"]), "intake omitted samples")
    for original, observed in zip(view["samples"], intake["samples"], strict=True):
        require(observed["sample_id"] == original["id"] and observed["epoch"] == original["epoch"]
                and observed["upstream_scores"] == {k: v["value"] for k, v in original["scores"].items()},
                "intake changed a sample or score")
    return {"adapter_sha256": pin["sha256"], "samples_preserved": len(view["samples"]),
            "scorers_per_sample": 3, "evidence_state": intake["evidence_state"],
            "lab_verdict": intake["lab_verdict"], "promotion_allowed": intake["promotion_allowed"],
            "intake_report_sha256": intake["report_sha256"]}


def collect(source: Path) -> dict:
    lock = read_json(HERE / "source_lock.json")
    require(sha_bytes(source.read_bytes()) == lock["forge"]["sha256"], "Forge source digest mismatch")
    result = subprocess.run(["node", str(HERE / "collect.mjs"), str(source.resolve())],
                            capture_output=True, text=True, check=True, timeout=20)
    return json.loads(result.stdout)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true", help="Regenerate reviewed artifacts intentionally")
    parser.add_argument("--source-file", type=Path, help="Run the exact pinned Forge source, then compare")
    parser.add_argument("--inspect-adapter", type=Path, help="Run the exact pinned PR #29 intake and verify non-promotion")
    args = parser.parse_args(argv)
    try:
        if args.write and args.source_file is None:
            raise EvidenceError("--write requires a source-exact execution")
        recording_path = HERE / "evidence/recording.json"
        recording = collect(args.source_file) if args.source_file else read_json(recording_path)
        report = build_report(recording)
        view = inspect_view(report)
        files = {recording_path: recording, HERE / "evidence/report.json": report,
                 HERE / "evidence/inspect_view.json": view}
        bridge = check_inspect_adapter(args.inspect_adapter, view) if args.inspect_adapter else None
        if bridge is not None:
            files[HERE / "evidence/adoption_check.json"] = bridge
        for path, value in files.items():
            if args.write:
                write_json(path, value)
            else:
                require(canonical(read_json(path)) == canonical(value), "committed evidence differs: " + path.name)
        print(json.dumps({"check": "PASS", "source_exact_execution": args.source_file is not None,
                          "summary": report["summary"], "adoption_check": bridge}, sort_keys=True))
        return 0
    except (EvidenceError, OSError, ValueError, TypeError, KeyError, RecursionError,
            subprocess.SubprocessError) as exc:
        print(json.dumps({"check": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
