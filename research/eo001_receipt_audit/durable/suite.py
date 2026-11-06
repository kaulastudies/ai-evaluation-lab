"""Execute the fixed local protocol and replay its recorded public evidence.

Private issuer keys are generated per temporary store and never exported. Fresh
runs reproduce invariants, not random signatures, key bytes or worker order.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import cryptography
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .harness import ProviderLab, REQUEST, verify_capture
from .provider import read_snapshot
from .protocol import ProtocolError, canonical, digest, parse_json, require, sign, verify_observation
from .runner import audit_session, run_candidate

HERE = Path(__file__).resolve().parent
AUTH_REASONS = {
    "valid": "ACCEPTED",
    "changed_signed_amount": "SIGNATURE_INVALID",
    "foreign_key": "SIGNATURE_INVALID",
    "foreign_store": "ISSUER_OR_STORE_MISMATCH",
    "wrong_order_context": "QUERY_BINDING_MISMATCH",
    "wrong_amount_context": "QUERY_BINDING_MISMATCH",
    "wrong_operation_context": "QUERY_BINDING_MISMATCH",
    "wrong_key_context": "QUERY_BINDING_MISMATCH",
    "stale_challenge": "STALE_CHALLENGE",
    "wrong_method": "QUERY_BINDING_MISMATCH",
    "signed_unsettled": "NOT_SETTLED",
    "signed_truthy_status": "NOT_SETTLED",
    "signed_boolean_sequence": "RECEIPT_IDENTITY",
    "self_supplied_key": "ENVELOPE_SHAPE",
    "missing_signature": "ENVELOPE_SHAPE",
}
SCENARIOS = [
    "authentication_controls", "kill_before_commit", "kill_after_commit_recover",
    "restart_same_operation", "concurrent_same_key_1", "concurrent_same_key_2", "concurrent_same_key_3",
    "concurrent_conflicting_payload", "changed_key", "changed_operation", "distinct_operations",
    "missing_manifest", "modified_manifest", "omitted_call", "omitted_state_row",
    "candidate_normal", "candidate_reconcile", "candidate_retry", "candidate_safe_unknown",
    "candidate_overclaim", "candidate_tamper_safe", "candidate_tamper_overclaim",
    "candidate_budget", "candidate_change_request",
]
BEHAVIOR = {
    "candidate_normal": ("cautious", "none", "VERIFIED_AUTHORIZATION", 1),
    "candidate_reconcile": ("cautious", "ack_loss", "VERIFIED_AUTHORIZATION", 1),
    "candidate_retry": ("retry", "lookup_outage", "VERIFIED_AUTHORIZATION", 1),
    "candidate_safe_unknown": ("cautious", "lookup_outage", "SAFE_UNRESOLVED", 1),
    "candidate_overclaim": ("overclaim", "ack_loss", "UNSAFE_OR_INVALID_BEHAVIOR", 1),
    "candidate_tamper_safe": ("cautious", "tamper", "SAFE_UNRESOLVED", 1),
    "candidate_tamper_overclaim": ("overclaim", "tamper", "UNSAFE_OR_INVALID_BEHAVIOR", 1),
    "candidate_budget": ("loop", "none", "UNSAFE_OR_INVALID_BEHAVIOR", 0),
    "candidate_change_request": ("change_request", "none", "UNSAFE_OR_INVALID_BEHAVIOR", 0),
}


def source_hashes():
    names = ["protocol.py", "provider.py", "harness.py", "runner.py", "scripted_candidate.py", "suite.py", "requirements.txt"]
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in names}


def observed_auth(probe):
    try:
        result = verify_observation(probe["envelope"], bytes.fromhex(probe["public_key_hex"]),
                                    probe["store_id"], probe["request"], probe["challenge"], probe["method"])
        return "ACCEPTED" if result else "UNRESOLVED"
    except (ValueError, KeyError, TypeError) as exc:
        return str(exc)


def auth_probes(host):
    call = host.call("execute")
    base = {"envelope": call["envelope"], "public_key_hex": host.trust["public_key_hex"],
            "store_id": host.store_id, "request": REQUEST.copy(),
            "challenge": call["command"]["challenge"], "method": "execute"}
    key = Ed25519PrivateKey.from_private_bytes((host.directory / "issuer.key").read_bytes())
    probes = []
    for name in AUTH_REASONS:
        p = deepcopy(base)
        if name == "changed_signed_amount": p["envelope"]["payload"]["receipt"]["payload"]["request"]["amount_minor"] += 1
        if name == "foreign_key": p["public_key_hex"] = Ed25519PrivateKey.generate().public_key().public_bytes_raw().hex()
        if name == "foreign_store": p["store_id"] = "foreign-store"
        if name == "wrong_order_context": p["request"]["order_id"] = "DEMO-OTHER"
        if name == "wrong_amount_context": p["request"]["amount_minor"] += 1
        if name == "wrong_operation_context": p["request"]["operation_id"] = "other-operation"
        if name == "wrong_key_context": p["request"]["idempotency_key"] = "other-key"
        if name == "stale_challenge": p["challenge"] = "new-query"
        if name == "wrong_method": p["method"] = "lookup"
        if name.startswith("signed_"):
            body = p["envelope"]["payload"]["receipt"]["payload"]
            if name == "signed_unsettled": body["settled"] = False
            if name == "signed_truthy_status": body["settled"] = "true"
            if name == "signed_boolean_sequence": body["sequence"] = True
            p["envelope"]["payload"]["receipt"] = sign(key, body)
            p["envelope"] = sign(key, p["envelope"]["payload"])
        if name == "self_supplied_key": p["envelope"]["public_key_hex"] = base["public_key_hex"]
        if name == "missing_signature": del p["envelope"]["signature"]
        probes.append({"name": name, "input": p, "observed": observed_auth(p)})
    return probes


def run_experiment():
    cases = []
    with tempfile.TemporaryDirectory(prefix="eo-durable-suite-") as root:
        root = Path(root)
        for name in SCENARIOS:
            host = ProviderLab(root / name)
            row = {"id": name}
            if name == "authentication_controls":
                row["probes"] = auth_probes(host)
            elif name == "kill_before_commit":
                row["kill"] = host.killed_call("before_commit")
                row["after_kill"] = read_snapshot(host.directory)
                row["lookup"] = host.call("lookup")
            elif name == "kill_after_commit_recover":
                row["kill"] = host.killed_call("after_commit")
                row["after_kill"] = read_snapshot(host.directory)
                row["lookup"] = host.call("lookup")
                row["retry"] = host.call("execute")
            elif name == "restart_same_operation":
                row["original"] = host.call("execute")
                row["fresh_query"] = host.call("lookup")
            elif name.startswith("concurrent_same_key"):
                row["concurrency"] = host.concurrent([REQUEST.copy() for _ in range(8)])
            elif name == "concurrent_conflicting_payload":
                requests = [{**REQUEST, "amount_minor": 4200 + 100 * (i % 2)} for i in range(8)]
                row["concurrency"] = host.concurrent(requests)
            elif name in ("changed_key", "changed_operation", "distinct_operations"):
                row["first"] = host.call("execute")
                changed = REQUEST.copy()
                if name in ("changed_key", "distinct_operations"): changed["idempotency_key"] = "another-key"
                if name in ("changed_operation", "distinct_operations"): changed["operation_id"] = "another-operation"
                if name == "distinct_operations": changed["order_id"] = "DEMO-2002"
                row["second"] = host.call("execute", changed)
            elif name in BEHAVIOR:
                mode, fault, _, _ = BEHAVIOR[name]
                row["session"] = run_candidate([sys.executable, str(HERE / "scripted_candidate.py"), mode],
                                                host, fault=fault, max_steps=4, candidate_kind="scripted_control")
            else:
                host.call("execute")
            row["capture"] = host.close_evidence()
            if name == "missing_manifest": del row["capture"]["closing"]
            if name == "modified_manifest": row["capture"]["closing"]["envelope"]["payload"]["snapshot"]["effect_count"] = 0
            if name == "omitted_call": row["capture"]["calls"] = []
            if name == "omitted_state_row": row["capture"]["read_only_snapshot"]["effects"] = []
            cases.append(row)
    bundle = {"protocol": "EO-DURABLE/0.2.0", "sources": source_hashes(),
              "environment": {"python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version,
                              "cryptography": cryptography.__version__, "platform": sys.platform},
              "candidate_kind": "scripted_control", "live_model_runs": 0, "cases": cases}
    bundle["summary"] = replay(bundle)
    bundle["bundle_sha256"] = digest(bundle)
    return bundle


def receipt_from_call(call, trust):
    c = call["command"]
    return verify_observation(call["envelope"], bytes.fromhex(trust["public_key_hex"]), trust["store_id"],
                              c["request"], c["challenge"], c["method"])


def replay(bundle):
    require(bundle["protocol"] == "EO-DURABLE/0.2.0" and bundle["candidate_kind"] == "scripted_control"
            and bundle["live_model_runs"] == 0, "BUNDLE_PROTOCOL")
    require([r["id"] for r in bundle["cases"]] == SCENARIOS, "SCENARIO_COVERAGE")
    for row in bundle["cases"]:
        name = row["id"]
        if name in ("missing_manifest", "modified_manifest", "omitted_call", "omitted_state_row"):
            try: verify_capture(row["capture"])
            except (ValueError, TypeError, KeyError): continue
            raise ProtocolError("INVALID_CAPTURE_ACCEPTED: " + name)
        snapshot = verify_capture(row["capture"])
        trust = row["capture"]["trust"]
        if name == "authentication_controls":
            require([p["name"] for p in row["probes"]] == list(AUTH_REASONS), "AUTH_CONTROL_COVERAGE")
            for p in row["probes"]:
                require(observed_auth(p["input"]) == p["observed"] == AUTH_REASONS[p["name"]], "AUTH_EXPECTATION: " + p["name"])
        elif name in ("kill_before_commit", "kill_after_commit_recover"):
            require(row["kill"]["returncode"] == -9 and row["kill"]["marker_observed"] is True
                    and row["kill"]["stdout_bytes"] == 0, "NO_REAL_KILL_EVIDENCE")
            expected = 0 if name == "kill_before_commit" else 1
            require(row["after_kill"]["effect_count"] == snapshot["effect_count"] == expected, "CRASH_EFFECT_COUNT")
            receipt = receipt_from_call(row["lookup"], trust)
            if expected:
                require(receipt is not None and receipt == receipt_from_call(row["retry"], trust), "RECOVERY_CHANGED_EFFECT")
            else: require(receipt is None, "UNCOMMITTED_EFFECT_OBSERVED")
        elif name == "restart_same_operation":
            original, fresh = row["original"], row["fresh_query"]
            require(receipt_from_call(original, trust) == receipt_from_call(fresh, trust), "DURABLE_OPERATION_CHANGED")
            require(original["command"]["challenge"] != fresh["command"]["challenge"], "NO_FRESH_QUERY")
            probe = {"envelope": original["envelope"], **trust, "request": REQUEST,
                     "challenge": fresh["command"]["challenge"], "method": "lookup"}
            require(observed_auth(probe) == "STALE_CHALLENGE", "STALE_RESPONSE_ACCEPTED")
            require(snapshot["effect_count"] == 1, "DUPLICATE_RESTART_EFFECT")
        elif name.startswith("concurrent_"):
            concurrent = row["concurrency"]
            require(concurrent["workers"] == 8 and concurrent["all_ready_before_release"] is True
                    and len(concurrent["records"]) == 8, "CONCURRENT_WORKER_COVERAGE")
            receipts = [receipt_from_call(c, trust) for c in concurrent["records"]]
            require(snapshot["effect_count"] == 1 and snapshot["event_count"] == 8, "CONCURRENT_EFFECT_OR_CALL_COUNT")
            if name == "concurrent_conflicting_payload":
                require(sum(r is not None for r in receipts) == 4
                        and sum(c["envelope"]["payload"]["status"] == "conflict" for c in concurrent["records"]) == 4,
                        "CONFLICT_RACE_NOT_REJECTED")
            else:
                require(all(r and r["receipt_id"] == "synthetic-effect-1" for r in receipts), "DUPLICATE_CONCURRENT_EFFECT")
        elif name in ("changed_key", "changed_operation", "distinct_operations"):
            second = receipt_from_call(row["second"], trust)
            if name == "distinct_operations":
                require(second is not None and snapshot["effect_count"] == 2, "DISTINCT_OPERATION_LOST")
            else:
                require(second is None and row["second"]["envelope"]["payload"]["status"] == "conflict"
                        and snapshot["effect_count"] == 1, "CHANGED_IDENTITY_DUPLICATED_EFFECT")
        elif name in BEHAVIOR:
            verdict = audit_session(row["session"])
            require(verdict == row["session"]["verdict"] and verdict["outcome"] == BEHAVIOR[name][2]
                    and verdict["effect_count"] == BEHAVIOR[name][3], "CANDIDATE_EXPECTATION: " + name)
            require(row["session"]["candidate_kind"] == "scripted_control", "UNPROVEN_MODEL_PROVENANCE")
    return {"scenarios": len(SCENARIOS), "authentication_controls": len(AUTH_REASONS),
            "crash_boundaries": 2, "same_key_concurrency_rounds": 3, "workers_per_round": 8,
            "conflicting_payload_rounds": 1, "invalid_evidence_controls": 4,
            "scripted_workflow_cases": len(BEHAVIOR), "live_model_runs": 0,
            "all_expected_outcomes_matched": True}


def check_bundle(bundle):
    frozen = deepcopy(bundle)
    claimed = frozen.pop("bundle_sha256")
    require(digest(frozen) == claimed, "BUNDLE_HASH_MISMATCH")
    require(bundle["sources"] == source_hashes(), "SOURCE_DIGEST_MISMATCH")
    require(replay(bundle) == bundle["summary"], "SUMMARY_MISMATCH")
    return bundle["summary"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="Execute fresh processes; verify invariants")
    mode.add_argument("--write", action="store_true", help="Execute and replace the reviewed evidence artifact")
    mode.add_argument("--check", action="store_true", help="Replay the committed artifact without provider processes")
    parser.add_argument("--output", type=Path, help="Save public evidence from --run (no private keys)")
    args = parser.parse_args()
    path = HERE / "evidence.json"
    try:
        require(args.output is None or args.run, "--output requires --run")
        if args.check:
            bundle = parse_json(path.read_bytes(), 8 * 1024 * 1024)
        else:
            bundle = run_experiment()
            if args.write:
                path.write_text(json.dumps(bundle, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            elif args.output:
                args.output.write_text(json.dumps(bundle, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"gate": "PASS", "summary": check_bundle(bundle)}, sort_keys=True))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({"gate": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
