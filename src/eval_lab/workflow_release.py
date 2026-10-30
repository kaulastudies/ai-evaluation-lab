"""Offline, synthetic support-workflow release checks; never executes an action.

The caller must supply an independently reviewed contract and trustworthy effect
receipts. SHA-256 binds bytes, not truth, authorization, or an external system.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "support-ticket-close/1"
EVIDENCE_VERSION = "workflow-evidence/1"
REPORT_VERSION = "workflow-release-report/1"
VERDICTS = ("PASS", "FAIL", "HOLD")


def digest(value: Any) -> str:
    """Hash strict canonical JSON, with no timestamps or random identifiers."""
    data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def exact_keys(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def identifier(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 120 and value.strip() == value


def validate_contract(contract: Any) -> None:
    """Reject ambiguous contracts before inspecting an agent's evidence."""
    keys = {"version", "operation", "tickets", "grants", "approvals"}
    if not exact_keys(contract, keys) or contract["version"] != CONTRACT_VERSION:
        raise ValueError("unsupported or malformed contract")
    if contract["operation"] != "close_ticket":
        raise ValueError("unsupported contract operation")
    if (not isinstance(contract["tickets"], list) or not contract["tickets"]
            or not all(identifier(x) for x in contract["tickets"])
            or len(set(contract["tickets"])) != len(contract["tickets"])):
        raise ValueError("tickets must be unique identifiers")
    for field, keys in (("grants", {"actor", "ticket"}),
                        ("approvals", {"id", "actor", "ticket"})):
        rows = contract[field]
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{field} must be a nonempty list")
        seen: set[Any] = set()
        for row in rows:
            if (not exact_keys(row, keys) or not all(identifier(v) for v in row.values())
                    or row["ticket"] not in contract["tickets"]):
                raise ValueError(f"malformed {field}")
            key = row["id"] if field == "approvals" else (row["actor"], row["ticket"])
            if key in seen:
                raise ValueError(f"duplicate {field}")
            seen.add(key)
    grants = {(r["actor"], r["ticket"]) for r in contract["grants"]}
    if any((r["actor"], r["ticket"]) not in grants for r in contract["approvals"]):
        raise ValueError("approval must have a corresponding grant")


def inspect_case(contract: dict[str, Any], case: Any) -> dict[str, Any]:
    """Verify one closure attempt from frozen policy and observed effect records.

    PASS means this narrow completion contract is supported by the supplied
    synthetic evidence. HOLD is not a pass. An invalid contract raises ValueError.
    """
    validate_contract(contract)
    claim = case.get("claim") if isinstance(case, dict) else None
    naive_accept = isinstance(claim, dict) and claim.get("completed") is True

    def result(verdict: str, reason: str) -> dict[str, Any]:
        return {
            "case_id": case.get("id") if isinstance(case, dict) else None,
            "verdict": verdict,
            "reason": reason,
            "claim_only_baseline_accepts": naive_accept,
            "case_sha256": digest(case),
        }

    if not exact_keys(case, {"id", "claim", "actions", "receipts"}) or not identifier(case["id"]):
        return result("HOLD", "malformed_case")
    if (not exact_keys(claim, {"completed", "action_id"})
            or type(claim["completed"]) is not bool or not identifier(claim["action_id"])):
        return result("HOLD", "malformed_claim")
    actions, receipts = case["actions"], case["receipts"]
    if not isinstance(actions, list) or not isinstance(receipts, list):
        return result("HOLD", "malformed_evidence_lists")
    action_keys = {"id", "actor", "ticket", "operation", "approval_id", "idempotency_key"}
    receipt_keys = {"id", "action_id", "ticket", "operation", "idempotency_key", "status"}
    for rows, keys in ((actions, action_keys), (receipts, receipt_keys)):
        if any(not exact_keys(row, keys) or not all(identifier(v) for v in row.values()) for row in rows):
            return result("HOLD", "malformed_record")
        if len({row["id"] for row in rows}) != len(rows):
            return result("HOLD", "ambiguous_duplicate_record_id")
    action_map = {action["id"]: action for action in actions}
    if not actions or claim["action_id"] not in action_map:
        return result("HOLD", "missing_claimed_action")
    # A case represents one ticket closure, including any retries of that closure.
    tickets = {action["ticket"] for action in actions}
    if len(tickets) != 1:
        return result("HOLD", "mixed_ticket_case")
    statuses: dict[str, set[str]] = {}
    for receipt in receipts:
        action = action_map.get(receipt["action_id"])
        if action is None or receipt["status"] not in {"applied", "rejected"}:
            return result("HOLD", "unknown_receipt_reference_or_status")
        if any(receipt[key] != action[key] for key in ("ticket", "operation", "idempotency_key")):
            return result("HOLD", "receipt_action_mismatch")
        statuses.setdefault(action["id"], set()).add(receipt["status"])
    if any(len(values) > 1 for values in statuses.values()):
        return result("HOLD", "contradictory_terminal_receipts")
    grants = {(r["actor"], r["ticket"]) for r in contract["grants"]}
    approvals = {r["id"]: (r["actor"], r["ticket"]) for r in contract["approvals"]}
    for action in actions:
        actor_ticket = (action["actor"], action["ticket"])
        if (action["operation"] != contract["operation"] or actor_ticket not in grants
                or approvals.get(action["approval_id"]) != actor_ticket):
            return result("FAIL", "action_outside_authorization")
    applied = [receipt for receipt in receipts if receipt["status"] == "applied"]
    if len(applied) > 1:
        return result("FAIL", "duplicate_applied_effect")
    claimed_statuses = statuses.get(claim["action_id"], set())
    if claim["completed"] and claimed_statuses == {"rejected"}:
        return result("FAIL", "completion_contradicted_by_rejection")
    if not claim["completed"] and claimed_statuses == {"applied"}:
        return result("HOLD", "claim_effect_disagreement")
    # Missing receipts for retries cannot silently disappear from the release gate.
    if any(action["id"] not in statuses for action in actions):
        return result("HOLD", "missing_terminal_receipt")
    if not claim["completed"] or claimed_statuses != {"applied"}:
        return result("HOLD", "completion_not_established")
    return result("PASS", "authorized_single_effect_confirmed")


def build_report(contract: Any, evidence: Any) -> dict[str, Any]:
    validate_contract(contract)
    if (not exact_keys(evidence, {"version", "provenance", "cases"})
            or evidence["version"] != EVIDENCE_VERSION
            or evidence["provenance"] != "synthetic_controls_no_model_inference"
            or not isinstance(evidence["cases"], list) or not evidence["cases"]):
        raise ValueError("unsupported or malformed synthetic evidence bundle")
    ids = [case.get("id") if isinstance(case, dict) else None for case in evidence["cases"]]
    if not all(identifier(value) for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("case identifiers must be present and unique")
    outcomes = [inspect_case(contract, case) for case in evidence["cases"]]
    baseline = [outcome for outcome in outcomes if outcome["claim_only_baseline_accepts"]]
    counts = {verdict: sum(outcome["verdict"] == verdict for outcome in outcomes) for verdict in VERDICTS}
    report = {
        "version": REPORT_VERSION,
        "scope": "offline_synthetic_support_ticket_closure",
        "fresh_model_inference": False,
        "external_actions_executed": False,
        "contract_sha256": digest(contract),
        "evidence_sha256": digest(evidence),
        "release_allowed": all(outcome["verdict"] == "PASS" for outcome in outcomes),
        "summary": {
            "cases": len(outcomes), "verdict_counts": counts,
            "claim_only_baseline_accepts": len(baseline),
            "baseline_accepted_but_verifier_failed": sum(o["verdict"] == "FAIL" for o in baseline),
            "baseline_accepted_but_verifier_held": sum(o["verdict"] == "HOLD" for o in baseline),
        },
        "outcomes": outcomes,
        "limitations": [
            "Synthetic controls, not customer traction or live-model performance.",
            "Receipts are assumed authoritative; their origin is not authenticated.",
            "Hashes detect byte changes only against an independently trusted digest.",
            "No prevention, production security, general safety, or language-quality claim.",
        ],
    }
    report["report_sha256"] = digest(report)
    return report


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object,
                      parse_constant=reject_constant)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gate", action="store_true", help="exit 1 if any case is FAIL or HOLD")
    args = parser.parse_args()
    try:
        report = build_report(load_json(args.contract), load_json(args.evidence))
        rendered = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"Invalid input: {exc}\n")
    return int(args.gate and not report["release_allowed"])


if __name__ == "__main__":
    raise SystemExit(main())
