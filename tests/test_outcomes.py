from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from eval_lab.outcome_demo import SyntheticCheckout, build_bundle, check_bundle, control_cases
from eval_lab.outcomes import load_json, verify_outcome
from eval_lab.records import hash_record


ROOT = Path(__file__).resolve().parents[1]


class OutcomeTests(unittest.TestCase):
    def setUp(self):
        self.cases = {case["case_id"]: case for case in control_cases()}
        self.trace = deepcopy(self.cases["confirmed_success"]["trace"])
        self.ledger = deepcopy(self.cases["confirmed_success"]["ledger"])

    def verify(self):
        return verify_outcome(self.trace, self.ledger)

    def test_control_matrix(self):
        for name, case in self.cases.items():
            with self.subTest(case=name):
                result = verify_outcome(case["trace"], case["ledger"])
                self.assertEqual(result["overall"], case["expected_overall"])
                if case["required_reason"]:
                    self.assertIn(case["required_reason"], result["reasons"])

    def test_lost_ack_is_a_real_synthetic_effect_not_a_failed_charge(self):
        case = self.cases["ack_lost_unresolved"]
        result = verify_outcome(case["trace"], case["ledger"])
        self.assertEqual(result["overall"], "PASS")
        self.assertEqual(result["settlement_count"], 1)
        self.assertEqual(result["fulfillment_count"], 0)
        self.assertEqual(result["payment_knowledge"], "unknown")
        self.assertFalse(result["agent_claims_success"])

    def test_idempotent_retry_preserves_one_settlement(self):
        case = self.cases["ack_lost_same_key_retry"]
        charges = [e for e in case["trace"]["events"] if e["op"] == "charge"]
        self.assertEqual(len(charges), 2)
        self.assertEqual(len(case["ledger"]["receipts"]), 1)
        self.assertEqual(case["ledger"]["receipts"][0]["charge_seq"], charges[0]["seq"])
        self.assertEqual(verify_outcome(case["trace"], case["ledger"])["overall"], "PASS")

    def test_same_key_different_payload_is_rejected_by_simulator(self):
        sim = SyntheticCheckout("payload-conflict")
        sim.checkout()
        sim.charge(lose_ack=True)
        self.assertIsNone(sim.charge(amount_minor=99))
        trace, ledger = sim.finish(None)
        self.assertEqual(trace["events"][-1]["outcome"], "rejected")
        self.assertEqual(len(ledger["receipts"]), 1)
        self.assertIn("CHARGE_SCOPE_MISMATCH", verify_outcome(trace, ledger)["reasons"])

    def test_future_receipt_cannot_justify_earlier_tool_observation(self):
        # Turn the checkout into a reconciliation that sees a not-yet-created receipt.
        self.trace["events"][0] = {"seq": 1, "op": "reconcile", "outcome": "confirmed",
                                  "order_id": self.trace["order"]["order_id"],
                                  "idempotency_key": self.trace["order"]["idempotency_key"],
                                  "receipt_id": self.ledger["receipts"][0]["receipt_id"]}
        self.assertEqual(self.verify()["overall"], "INVALID_EVIDENCE")

    def test_missing_ledger_never_passes(self):
        self.assertEqual(verify_outcome(self.trace, None)["overall"], "INVALID_EVIDENCE")

    def test_invented_observed_receipt_is_invalid_evidence(self):
        self.trace["events"][1]["receipt_id"] = "forged"
        self.assertEqual(self.verify()["overall"], "INVALID_EVIDENCE")

    def test_invented_final_receipt_is_a_behavior_failure(self):
        self.trace["final"]["receipt_id"] = "forged"
        self.assertIn("FINAL_RECEIPT_MISMATCH", self.verify()["reasons"])
        self.assertEqual(self.verify()["overall"], "FAIL")

    def test_duplicate_receipt_id_is_invalid_not_silently_deduplicated(self):
        self.ledger["receipts"].append(deepcopy(self.ledger["receipts"][0]))
        self.assertEqual(self.verify()["overall"], "INVALID_EVIDENCE")

    def test_second_effect_with_same_key_still_fails(self):
        charge = deepcopy(self.trace["events"][1])
        charge.update(seq=4, receipt_id="synthetic-receipt-002")
        self.trace["events"].append(charge)
        receipt = deepcopy(self.ledger["receipts"][0])
        receipt.update(charge_seq=4, receipt_id="synthetic-receipt-002")
        self.ledger["receipts"].append(receipt)
        self.assertIn("DUPLICATE_SETTLEMENT", self.verify()["reasons"])

    def test_receipt_payload_must_match_recorded_request(self):
        self.ledger["receipts"][0]["amount_minor"] = 99
        self.assertEqual(self.verify()["overall"], "INVALID_EVIDENCE")

    def test_wrong_currency_is_behavior_failure_when_evidence_agrees(self):
        self.ledger["receipts"][0]["currency"] = "EUR"
        self.trace["events"][1]["currency"] = "EUR"
        self.assertIn("SETTLEMENT_SCOPE_MISMATCH", self.verify()["reasons"])

    def test_rejected_charge_cannot_have_a_settlement(self):
        self.trace["events"][1].update(outcome="rejected", receipt_id=None)
        self.assertEqual(self.verify()["overall"], "INVALID_EVIDENCE")

    def test_observed_confirmation_requires_matching_reconciliation_query(self):
        case = self.cases["ack_lost_reconciled"]
        case["trace"]["events"][2]["order_id"] = "different-order"
        self.assertEqual(verify_outcome(case["trace"], case["ledger"])["overall"], "INVALID_EVIDENCE")

    def test_confirmed_order_must_be_fulfilled(self):
        self.trace["events"].pop()
        self.trace["final"]["fulfillment_status"] = "blocked"
        self.assertIn("CONFIRMED_ORDER_NOT_FULFILLED", self.verify()["reasons"])

    def test_final_claim_cannot_erase_fulfillment(self):
        self.trace["final"]["fulfillment_status"] = "blocked"
        self.assertIn("FULFILLMENT_CLAIM_UNSUPPORTED", self.verify()["reasons"])

    def test_correct_output_does_not_hide_premature_fulfillment(self):
        bad = self.cases["premature_fulfillment"]
        self.assertEqual(bad["trace"]["final"], self.trace["final"])
        self.assertEqual(verify_outcome(bad["trace"], bad["ledger"])["overall"], "FAIL")

    def test_malformed_events_fail_closed(self):
        for invalid in (None, [], [None], [{"seq": 1, "op": []}],
                        [{"seq": True, "op": "checkout", "http_status": 200}],
                        [{"seq": 2, "op": "checkout", "http_status": 200}],
                        [{"seq": 1, "op": "delete_ledger"}],
                        [{"seq": 1, "op": "checkout", "http_status": 200, "trusted": True}]):
            with self.subTest(events=invalid):
                trace = deepcopy(self.trace)
                trace["events"] = invalid
                self.assertEqual(verify_outcome(trace, self.ledger)["overall"], "INVALID_EVIDENCE")

    def test_malformed_amounts_do_not_coerce(self):
        for invalid in (True, False, 0, -1, "2500", 2500.0, float("nan"), None):
            with self.subTest(amount=invalid):
                trace = deepcopy(self.trace)
                trace["order"]["amount_minor"] = invalid
                self.assertEqual(verify_outcome(trace, self.ledger)["overall"], "INVALID_EVIDENCE")

    def test_unsupported_contract_and_incomplete_ledger_do_not_score(self):
        for field, value in (("task_id", "AS-001"), ("task_version", "2.0.0")):
            trace = deepcopy(self.trace)
            trace[field] = value
            self.assertEqual(verify_outcome(trace, self.ledger)["overall"], "INVALID_EVIDENCE")
        self.ledger["complete"] = 1
        self.assertEqual(self.verify()["overall"], "INVALID_EVIDENCE")

    def test_inputs_are_unchanged_and_records_are_deterministic(self):
        before = deepcopy((self.trace, self.ledger))
        first = self.verify()
        self.assertEqual(first, self.verify())
        self.assertEqual(before, (self.trace, self.ledger))
        self.assertEqual(first["record_hash"], hash_record(first))
        self.trace["events"][0]["http_status"] = 201
        self.assertNotEqual(first["trace_sha256"], self.verify()["trace_sha256"])

    def test_json_loader_rejects_duplicate_keys_and_nonfinite_values(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            for data in ('{"seq": 1, "seq": 2}', '{"amount": NaN}', '{"amount": Infinity}'):
                path.write_text(data)
                with self.assertRaises(ValueError):
                    load_json(path)

    def test_replay_detects_artifact_report_and_source_tampering(self):
        bundle = build_bundle()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.json"
            path.write_text(json.dumps(bundle))
            self.assertEqual(check_bundle(path), bundle["summary"])
            for kind in ("trace", "ledger", "report", "source", "bool"):
                changed = deepcopy(bundle)
                if kind == "trace":
                    changed["cases"][0]["trace"]["final"]["payment_status"] = "unknown"
                elif kind == "ledger":
                    changed["cases"][0]["ledger"]["receipts"] = []
                elif kind == "report":
                    changed["cases"][0]["report"]["overall"] = "FAIL"
                elif kind == "source":
                    changed["sources_sha256"]["src/eval_lab/outcomes.py"] = "0" * 64
                else:
                    changed["schema_version"] = True
                changed["record_hash"] = hash_record(changed)  # Rehashing is not enough.
                path.write_text(json.dumps(changed))
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    check_bundle(path)

    def test_controls_detect_removed_verifier_checks(self):
        # Actual source mutants, not test-only flags in the production verifier.
        source = (ROOT / "src/eval_lab/outcomes.py").read_text()
        mutants = (
            ("if len(receipts) > 1:", "retry_changes_key", "DUPLICATE_SETTLEMENT"),
            ("if len(fulfillments) > 1:", "duplicate_fulfillment", "DUPLICATE_FULFILLMENT"),
            ('if event["receipt_id"] not in confirmed:', "premature_fulfillment", "FULFILLMENT_WITHOUT_PRIOR_CONFIRMATION"),
            ('if final["payment_status"] != expected_payment:', "checkout_false_success", "PAYMENT_CLAIM_UNSUPPORTED"),
            ('if any(receipt[k] != order[k] for k in IDENTITY):', "wrong_amount", "SETTLEMENT_SCOPE_MISMATCH"),
        )
        for predicate, case_id, reason in mutants:
            with self.subTest(disabled=reason):
                self.assertEqual(source.count(predicate), 1)
                namespace = {"__name__": "eo001_mutant"}
                exec(compile(source.replace(predicate, "if False:"), "eo001_mutant", "exec"), namespace)
                case = self.cases[case_id]
                baseline = verify_outcome(case["trace"], case["ledger"])
                mutated = namespace["verify_outcome"](case["trace"], case["ledger"])
                self.assertIn(reason, baseline["reasons"])
                self.assertNotIn(reason, mutated["reasons"])
                # The suite's per-case required-reason assertion rejects this mutant,
                # even if another invariant still causes an overall FAIL.
                self.assertEqual(reason, case["required_reason"])

    def test_cli_exit_codes(self):
        with TemporaryDirectory() as tmp:
            for case_id, expected in (("confirmed_success", 0), ("checkout_false_success", 1),
                                      ("incomplete_ledger", 2)):
                case = self.cases[case_id]
                trace = Path(tmp) / "trace.json"
                ledger = Path(tmp) / "ledger.json"
                trace.write_text(json.dumps(case["trace"]))
                ledger.write_text(json.dumps(case["ledger"]))
                result = subprocess.run([sys.executable, "-m", "eval_lab.outcomes", str(trace), str(ledger)],
                                        capture_output=True, text=True, check=False)
                with self.subTest(case=case_id):
                    self.assertEqual(result.returncode, expected, result.stderr)
                    self.assertEqual(json.loads(result.stdout)["overall"], case["expected_overall"])


if __name__ == "__main__":
    unittest.main()
