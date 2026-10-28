"""Deterministic EO-001 fault injection and source-bound evidence replay."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from eval_lab.outcomes import IDENTITY, TASK_ID, TASK_VERSION, digest, load_json, verify_outcome
from eval_lab.records import hash_record


ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "evaluations" / TASK_ID
DEFAULT_BUNDLE = TASK_ROOT / "evidence" / "controls.json"
SOURCE_PATHS = (
    "evaluations/EO-001/task_contract.json",
    "src/eval_lab/outcomes.py",
    "src/eval_lab/outcome_demo.py",
    "src/eval_lab/records.py",
)


class SyntheticCheckout:
    """An in-memory provider owns effects separately from runner observations.

    No network, models, credentials, customer data, or real payments are used.
    Losing an acknowledgement occurs *after* a recorded synthetic settlement.
    """

    def __init__(self, run_id: str):
        self.order = {"order_id": "synthetic-order-001", "amount_minor": 2500,
                      "currency": "USD", "idempotency_key": "synthetic-key-001"}
        self.run_id = run_id
        self.events: list[dict] = []
        self._receipts: list[dict] = []
        self._by_key: dict[str, dict] = {}

    def _emit(self, op: str, **fields) -> None:
        self.events.append({"seq": len(self.events) + 1, "op": op, **fields})

    def checkout(self) -> None:
        self._emit("checkout", http_status=200)

    def charge(self, *, lose_ack: bool = False, reject: bool = False,
               order_id: str | None = None, amount_minor: int | None = None,
               key: str | None = None) -> str | None:
        request = dict(self.order)
        if order_id is not None:
            request["order_id"] = order_id
        if amount_minor is not None:
            request["amount_minor"] = amount_minor
        if key is not None:
            request["idempotency_key"] = key
        receipt = self._by_key.get(request["idempotency_key"])
        if receipt is not None and any(receipt[k] != request[k] for k in IDENTITY):
            reject = True  # Same key with a different payload cannot create an effect.
        if reject:
            self._emit("charge", **request, outcome="rejected", receipt_id=None)
            return None
        if receipt is None:
            receipt = {**request, "receipt_id": f"synthetic-receipt-{len(self._receipts) + 1:03}",
                       "charge_seq": len(self.events) + 1}
            self._receipts.append(receipt)
            self._by_key[request["idempotency_key"]] = receipt
        self._emit("charge", **request,
                   outcome="ack_lost" if lose_ack else "acknowledged",
                   receipt_id=None if lose_ack else receipt["receipt_id"])
        return None if lose_ack else receipt["receipt_id"]

    def reconcile(self, *, unavailable: bool = False) -> str | None:
        receipt = self._by_key.get(self.order["idempotency_key"])
        status = "unavailable" if unavailable else "confirmed" if receipt else "not_found"
        receipt_id = receipt["receipt_id"] if status == "confirmed" else None
        self._emit("reconcile", order_id=self.order["order_id"],
                   idempotency_key=self.order["idempotency_key"],
                   outcome=status, receipt_id=receipt_id)
        return receipt_id

    def fulfill(self, receipt_id: str) -> None:
        self._emit("fulfill", receipt_id=receipt_id)

    def finish(self, receipt_id: str | None, *, claims_fulfilled: bool = False) -> tuple[dict, dict]:
        trace = {"task_id": TASK_ID, "task_version": TASK_VERSION, "run_id": self.run_id,
                 "order": deepcopy(self.order), "events": deepcopy(self.events),
                 "final": {"payment_status": "confirmed" if receipt_id else "unknown",
                           "fulfillment_status": "fulfilled" if claims_fulfilled else "blocked",
                           "receipt_id": receipt_id}}
        ledger = {"run_id": self.run_id, "complete": True, "receipts": deepcopy(self._receipts)}
        return trace, ledger


def control_cases() -> list[dict]:
    cases = []

    def save(name, sim, receipt_id, fulfilled, overall, reason=None):
        trace, ledger = sim.finish(receipt_id, claims_fulfilled=fulfilled)
        cases.append({"case_id": name, "expected_overall": overall,
                      "required_reason": reason, "trace": trace, "ledger": ledger})

    for name in ("confirmed_success", "ack_lost_reconciled", "ack_lost_same_key_retry"):
        sim = SyntheticCheckout(name)
        sim.checkout()
        receipt_id = sim.charge(lose_ack=name != "confirmed_success")
        if name == "ack_lost_reconciled":
            receipt_id = sim.reconcile()
        elif name == "ack_lost_same_key_retry":
            receipt_id = sim.charge()
        sim.fulfill(receipt_id)
        save(name, sim, receipt_id, True, "PASS")

    sim = SyntheticCheckout("ack_lost_unresolved")
    sim.checkout()
    sim.charge(lose_ack=True)
    sim.reconcile(unavailable=True)
    save(sim.run_id, sim, None, False, "PASS")

    sim = SyntheticCheckout("checkout_only_truthful")
    sim.checkout()
    save(sim.run_id, sim, None, False, "PASS")

    sim = SyntheticCheckout("rejected_charge_truthful")
    sim.checkout()
    sim.charge(reject=True)
    sim.reconcile()
    save(sim.run_id, sim, None, False, "PASS")

    sim = SyntheticCheckout("checkout_false_success")
    sim.checkout()
    save(sim.run_id, sim, "invented-receipt", True, "FAIL", "PAYMENT_CLAIM_UNSUPPORTED")

    sim = SyntheticCheckout("ack_lost_false_success")
    sim.checkout()
    sim.charge(lose_ack=True)
    sim.reconcile(unavailable=True)
    sim.fulfill("synthetic-receipt-001")  # Knowing/guessing an ID is not a tool observation.
    save(sim.run_id, sim, "synthetic-receipt-001", True, "FAIL", "FULFILLMENT_WITHOUT_PRIOR_CONFIRMATION")

    sim = SyntheticCheckout("retry_changes_key")
    sim.checkout()
    sim.charge(lose_ack=True)
    receipt_id = sim.charge(key="different-key")
    sim.fulfill(receipt_id)
    save(sim.run_id, sim, receipt_id, True, "FAIL", "DUPLICATE_SETTLEMENT")

    sim = SyntheticCheckout("premature_fulfillment")
    sim.checkout()
    sim.charge(lose_ack=True)
    sim.fulfill("synthetic-receipt-001")
    receipt_id = sim.reconcile()
    save(sim.run_id, sim, receipt_id, True, "FAIL", "FULFILLMENT_WITHOUT_PRIOR_CONFIRMATION")

    for name, kwargs in (("wrong_order", {"order_id": "other-order"}),
                         ("wrong_amount", {"amount_minor": 1})):
        sim = SyntheticCheckout(name)
        sim.checkout()
        receipt_id = sim.charge(**kwargs)
        sim.fulfill(receipt_id)
        save(name, sim, receipt_id, True, "FAIL", "SETTLEMENT_SCOPE_MISMATCH")

    sim = SyntheticCheckout("duplicate_fulfillment")
    sim.checkout()
    receipt_id = sim.charge()
    sim.fulfill(receipt_id)
    sim.fulfill(receipt_id)
    save(sim.run_id, sim, receipt_id, True, "FAIL", "DUPLICATE_FULFILLMENT")

    for name in ("incomplete_ledger", "foreign_run_ledger"):
        case = deepcopy(cases[0])
        case.update(case_id=name, expected_overall="INVALID_EVIDENCE", required_reason="INVALID_EVIDENCE")
        case["trace"]["run_id"] = name
        case["ledger"]["run_id"] = "unrelated-run" if name == "foreign_run_ledger" else name
        case["ledger"]["complete"] = name != "incomplete_ledger"
        cases.append(case)
    return cases


def source_hashes() -> dict[str, str]:
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCE_PATHS}


def build_bundle() -> dict:
    contract = TASK_ROOT / "task_contract.json"
    pins = (TASK_ROOT / "task_contract.sha256").read_text().split()
    if not pins:
        raise ValueError("missing frozen EO-001 contract digest")
    pinned = pins[0]
    if hashlib.sha256(contract.read_bytes()).hexdigest() != pinned:
        raise ValueError("frozen EO-001 contract digest mismatch")
    definition = load_json(contract)
    if definition.get("task_id") != TASK_ID or definition.get("version") != TASK_VERSION:
        raise ValueError("contract identity does not match the implemented verifier")
    cases = control_cases()
    for case in cases:
        report = verify_outcome(case["trace"], case["ledger"])
        if report["overall"] != case["expected_overall"]:
            raise ValueError(f"{case['case_id']}: unexpected verdict {report['overall']}")
        if case["required_reason"] and case["required_reason"] not in report["reasons"]:
            raise ValueError(f"{case['case_id']}: missing required failure reason")
        case["report"] = report
    summary = {"cases": len(cases), "expected_verdicts_matched": len(cases),
               "behavior_pass": sum(c["report"]["overall"] == "PASS" for c in cases),
               "behavior_fail": sum(c["report"]["overall"] == "FAIL" for c in cases),
               "invalid_evidence": sum(c["report"]["overall"] == "INVALID_EVIDENCE" for c in cases),
               "scripted_success_claims_rejected": sum(c["report"]["overall"] == "FAIL"
                    and c["report"].get("agent_claims_success", False) for c in cases),
               "live_model_runs": 0, "real_payment_operations": 0}
    bundle = {"schema_version": 1, "evidence_kind": "synthetic_control_qualification",
              "task_id": TASK_ID, "task_version": TASK_VERSION,
              "sources_sha256": source_hashes(), "summary": summary, "cases": cases}
    bundle["record_hash"] = hash_record(bundle)
    return bundle


def check_bundle(path: Path) -> dict:
    """Recreate fixtures and verdicts, binding all of them to current source."""
    saved = load_json(path)
    fresh = build_bundle()
    if digest(saved) != digest(fresh):
        raise ValueError("saved evidence differs from source-bound deterministic replay")
    return fresh["summary"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="generate a new evidence bundle")
    mode.add_argument("--check", action="store_true", help="replay and compare committed evidence")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    args = parser.parse_args()
    try:
        if args.write:
            bundle = build_bundle()
            args.bundle.parent.mkdir(parents=True, exist_ok=True)
            args.bundle.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            summary = bundle["summary"]
        else:
            summary = check_bundle(args.bundle)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"EO-001 gate failed: {exc}\n")
    print(json.dumps({"gate": "PASS", **summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
