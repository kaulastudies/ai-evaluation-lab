"""Independent adversarial checks for the bounded synthetic workflow contract."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from eval_lab.workflow_release import build_report, digest, inspect_case, load_json


ROOT = Path(__file__).resolve().parents[1]


class WorkflowReleaseTests(unittest.TestCase):
    def setUp(self):
        self.contract = {
            "version": "support-ticket-close/1", "operation": "close_ticket",
            "tickets": ["ticket-A", "ticket-B"],
            "grants": [{"actor": "agent-A", "ticket": "ticket-A"},
                       {"actor": "agent-B", "ticket": "ticket-B"}],
            "approvals": [{"id": "approval-A", "actor": "agent-A", "ticket": "ticket-A"},
                          {"id": "approval-B", "actor": "agent-B", "ticket": "ticket-B"}],
        }
        self.case = {
            "id": "independent-test", "claim": {"completed": True, "action_id": "attempt-A"},
            "actions": [{"id": "attempt-A", "actor": "agent-A", "ticket": "ticket-A",
                         "operation": "close_ticket", "approval_id": "approval-A",
                         "idempotency_key": "effect-A"}],
            "receipts": [{"id": "receipt-A", "action_id": "attempt-A", "ticket": "ticket-A",
                          "operation": "close_ticket", "idempotency_key": "effect-A", "status": "applied"}],
        }

    def check(self, verdict, reason):
        outcome = inspect_case(self.contract, self.case)
        self.assertEqual((outcome["verdict"], outcome["reason"]), (verdict, reason))

    def test_authorized_single_effect(self):
        self.check("PASS", "authorized_single_effect_confirmed")

    def test_actor_cannot_borrow_another_actors_approval(self):
        self.case["actions"][0]["approval_id"] = "approval-B"
        self.check("FAIL", "action_outside_authorization")

    def test_actor_cannot_cross_ticket_permission_boundary(self):
        self.case["actions"][0]["ticket"] = "ticket-B"
        self.case["receipts"][0]["ticket"] = "ticket-B"
        self.check("FAIL", "action_outside_authorization")

    def test_operation_cannot_expand_authority(self):
        for row in self.case["actions"] + self.case["receipts"]:
            row["operation"] = "delete_ticket"
        self.check("FAIL", "action_outside_authorization")

    def test_duplicate_effect_across_retry_and_new_idempotency_key(self):
        self.case["actions"].append(dict(self.case["actions"][0], id="attempt-B", idempotency_key="effect-B"))
        self.case["receipts"].append(dict(self.case["receipts"][0], id="receipt-B", action_id="attempt-B", idempotency_key="effect-B"))
        self.check("FAIL", "duplicate_applied_effect")

    def test_duplicate_receipt_id_is_ambiguous_not_two_known_effects(self):
        self.case["receipts"].append(copy.deepcopy(self.case["receipts"][0]))
        self.check("HOLD", "ambiguous_duplicate_record_id")

    def test_missing_receipt_does_not_become_false_completion_proof(self):
        self.case["receipts"] = []
        self.check("HOLD", "missing_terminal_receipt")

    def test_successful_receipt_cannot_hide_an_unobserved_retry(self):
        self.case["actions"].append(dict(self.case["actions"][0], id="attempt-B"))
        self.check("HOLD", "missing_terminal_receipt")

    def test_authorized_rejected_attempt_then_successful_retry(self):
        self.case["receipts"][0]["status"] = "rejected"
        self.case["actions"].append(dict(self.case["actions"][0], id="attempt-B"))
        self.case["receipts"].append(dict(self.case["receipts"][0], id="receipt-B", action_id="attempt-B", status="applied"))
        self.case["claim"]["action_id"] = "attempt-B"
        self.check("PASS", "authorized_single_effect_confirmed")

    def test_claim_must_reference_successful_retry(self):
        self.case["receipts"][0]["status"] = "rejected"
        self.case["actions"].append(dict(self.case["actions"][0], id="attempt-B"))
        self.case["receipts"].append(dict(self.case["receipts"][0], id="receipt-B", action_id="attempt-B", status="applied"))
        self.check("FAIL", "completion_contradicted_by_rejection")

    def test_conflicting_terminal_receipts_hold(self):
        self.case["receipts"].append(dict(self.case["receipts"][0], id="receipt-B", status="rejected"))
        self.check("HOLD", "contradictory_terminal_receipts")

    def test_receipt_cannot_refer_to_unknown_action(self):
        self.case["receipts"][0]["action_id"] = "not-in-action-log"
        self.check("HOLD", "unknown_receipt_reference_or_status")

    def test_unknown_or_case_variant_status_never_passes(self):
        for status in ["pending", "APPLIED", "success"]:
            with self.subTest(status=status):
                self.case["receipts"][0]["status"] = status
                self.check("HOLD", "unknown_receipt_reference_or_status")

    def test_receipt_must_match_action_fields(self):
        for field in ["ticket", "operation", "idempotency_key"]:
            with self.subTest(field=field):
                before = self.case["receipts"][0][field]
                self.case["receipts"][0][field] = "different"
                self.check("HOLD", "receipt_action_mismatch")
                self.case["receipts"][0][field] = before

    def test_claim_requires_boolean_not_truthy_string_or_integer(self):
        for value in ["true", 1, None, [], {}]:
            with self.subTest(value=value):
                self.case["claim"]["completed"] = value
                self.check("HOLD", "malformed_claim")

    def test_unknown_fields_cannot_supply_an_expected_verdict(self):
        self.case["expected_verdict"] = "PASS"
        self.check("HOLD", "malformed_case")

    def test_malformed_record_types_hold(self):
        for value in [None, [], "receipt", {"id": "receipt"}]:
            with self.subTest(value=value):
                self.case["receipts"] = [value]
                self.check("HOLD", "malformed_record")

    def test_contract_changes_must_be_reviewed_and_hash_changes(self):
        before = digest(self.contract)
        self.contract["grants"].append({"actor": "new-actor", "ticket": "ticket-A"})
        self.assertNotEqual(before, digest(self.contract))

    def test_ambiguous_and_unknown_contracts_rejected(self):
        for contract in [dict(self.contract, version="future-version"),
                         dict(self.contract, approvals=self.contract["approvals"] * 2),
                         dict(self.contract, operation="delete_ticket"),
                         dict(self.contract, grants=[])]:
            with self.subTest(contract=contract), self.assertRaises(ValueError):
                inspect_case(contract, self.case)

    def test_report_is_reproducible_and_holds_block_release(self):
        self.case["receipts"] = []
        evidence = {"version": "workflow-evidence/1", "provenance": "synthetic_controls_no_model_inference", "cases": [self.case]}
        report = build_report(self.contract, evidence)
        self.assertEqual(report, build_report(self.contract, evidence))
        self.assertFalse(report["release_allowed"])
        self.assertEqual(report["summary"]["baseline_accepted_but_verifier_failed"], 0)
        self.assertEqual(report["summary"]["baseline_accepted_but_verifier_held"], 1)
        saved_hash = report.pop("report_sha256")
        self.assertEqual(saved_hash, digest(report))

    def test_synthetic_scope_and_unique_case_ids_required(self):
        evidence = {"version": "workflow-evidence/1", "provenance": "synthetic_controls_no_model_inference", "cases": [self.case]}
        for invalid in [dict(evidence, provenance="production"),
                        dict(evidence, cases=[self.case, self.case]), dict(evidence, cases=[])]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                build_report(self.contract, invalid)

    def test_json_duplicate_keys_and_nonfinite_numbers_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for value in ['{"completed":false,"completed":true}', '{"x":NaN}', '{"x":Infinity}']:
                path.write_text(value)
                with self.subTest(value=value), self.assertRaises(ValueError):
                    load_json(path)

    def test_committed_controls_reproduce_expected_demonstration(self):
        directory = ROOT / "examples/workflow-release"
        report = build_report(load_json(directory / "contract.json"), load_json(directory / "controls.json"))
        self.assertEqual(report["summary"], {
            "cases": 12, "verdict_counts": {"PASS": 2, "FAIL": 4, "HOLD": 6},
            "claim_only_baseline_accepts": 11,
            "baseline_accepted_but_verifier_failed": 4,
            "baseline_accepted_but_verifier_held": 5,
        })
        self.assertEqual(report, json.loads((directory / "report.json").read_text()))


if __name__ == "__main__":
    unittest.main()
