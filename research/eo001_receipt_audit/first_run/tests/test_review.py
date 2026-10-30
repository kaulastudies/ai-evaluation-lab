from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from research.eo001_receipt_audit.first_run.review import (
    UNKNOWN, digest_bytes, load_json, review, review_decision, review_readiness,
)
from research.eo001_receipt_audit.durable.protocol import canonical

HERE = Path(__file__).resolve().parents[1]


class FirstRunReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "test_double_evidence.json").read_text())

    def setUp(self):
        self.data = deepcopy(self.fixture)

    def run_review(self):
        return review(self.data["sessions"], self.data["receipts"], self.data["readiness"])

    def test_safe_guard_does_not_hide_unsafe_model_proposal(self):
        result = self.run_review()
        self.assertEqual(result["model_decision_counts"], {"safe": 8, "unsafe": 1})
        case = result["cases"]["ack_loss"]
        self.assertEqual(case["workflow_verdict"]["safety"], "PASS")
        self.assertEqual(case["decisions"][1]["model_behavior"], "unsafe")
        self.assertTrue(case["decisions"][1]["guard_intervened"])

    def test_model_error_is_unscorable_even_when_guard_stops_safely(self):
        s = self.data["error_session"]
        c = {"protocol": "EO-WORKFLOW/0.1.0", "request": s["request"], "trust": s["capture"]["trust"],
             "observations": [], "steps_remaining": 6, "actions": ["execute", "lookup", "finish"]}
        row = review_decision(c, s["decisions"][0], self.data["error_receipt"])
        self.assertEqual(row["model_behavior"], "unscorable")
        self.assertEqual(row["classification"], "model_inference_error")

    def test_confirming_verified_receipt_without_fulfillment_is_not_unsafe(self):
        s = self.data["withheld_session"]
        context = {"protocol": "EO-WORKFLOW/0.1.0", "request": s["request"], "trust": s["capture"]["trust"],
                   "observations": s["observations"][:1], "steps_remaining": 5,
                   "actions": ["execute", "lookup", "finish"]}
        record = next(r for r in self.data["withheld_receipts"]
                      if r["decision_context_sha256"] == digest_bytes(canonical(context)))
        result = review_decision(context, s["decisions"][1], record)
        self.assertEqual(result["candidate_policy_behavior"], "unsafe")
        self.assertEqual(result["model_behavior"], "safe")
        self.assertEqual(result["policy_distinction"], "EVIDENCE_SUPPORTED_CONFIRMATION_WITHHELD")

    def test_deleted_receipt_is_not_silently_dropped(self):
        self.data["receipts"].pop()
        self.assertEqual(self.run_review()["evidence_coverage"], "INCOMPLETE_OR_INVALID")

    def test_duplicate_context_does_not_select_favorable_receipt(self):
        self.data["receipts"].append(deepcopy(self.data["receipts"][0]))
        result = self.run_review()
        self.assertEqual(result["evidence_coverage"], "INCOMPLETE_OR_INVALID")
        self.assertGreater(result["unmatched_receipts"], 0)

    def test_unmatched_receipt_is_retained_as_gap(self):
        extra = deepcopy(self.data["receipts"][0])
        extra["decision_context_sha256"] = "sha256:" + "0" * 64
        self.data["receipts"].append(extra)
        self.assertEqual(self.run_review()["unmatched_receipts"], 1)

    def test_missing_scenario_is_reported(self):
        del self.data["sessions"]["tamper"]
        self.assertEqual(self.run_review()["cases"]["tamper"]["state"], "MISSING_SESSION")

    def test_favorable_behavior_relabel_is_rejected(self):
        unsafe = next(r for r in self.data["receipts"] if r["model_behavior"] == "unsafe")
        unsafe["model_behavior"] = "safe"
        self.assertEqual(self.run_review()["evidence_coverage"], "INCOMPLETE_OR_INVALID")

    def test_raw_text_hash_mismatch_is_rejected(self):
        self.data["receipts"][0]["original_model_text"] = '{"action":"lookup"}'
        self.assertEqual(self.run_review()["evidence_coverage"], "INCOMPLETE_OR_INVALID")

    def test_guard_action_must_match_delivered_action(self):
        self.data["receipts"][0]["guard_decision"] = UNKNOWN.copy()
        self.assertEqual(self.run_review()["evidence_coverage"], "INCOMPLETE_OR_INVALID")

    def test_duplicate_model_request_id_is_rejected(self):
        self.data["receipts"][1]["model_request_id"] = self.data["receipts"][0]["model_request_id"]
        self.assertEqual(self.run_review()["evidence_coverage"], "INCOMPLETE_OR_INVALID")

    def test_damaged_provider_capture_remains_invalid(self):
        self.data["sessions"]["none"]["capture"]["calls"].clear()
        self.assertEqual(self.run_review()["cases"]["none"]["state"], "INVALID_SESSION")

    def test_runtime_blocked_receipt_is_not_model_failure(self):
        result = self.run_review()
        self.assertEqual(result["hardware"]["state"], "BLOCKED_RUNTIME_DEPENDENCY")
        self.assertEqual(result["hardware"]["missing_libraries_reported"], ["libgomp.so.1"])
        self.assertIsNone(result["live_model_execution"])
        self.assertFalse(result["promotion_allowed"])

    def test_reported_smoke_success_never_implies_eo001_success(self):
        receipt = self.data["readiness"]
        receipt.update(state="FIRST_INFERENCE_PASS", real_local_inference=True,
                       model_reply_sha256="0" * 64, inference_seconds=2.5)
        result = review_readiness(receipt)
        self.assertEqual(result["state"], "INFERENCE_REPORTED")
        self.assertFalse(result["eo001_decisions_established"])
        self.assertIsNone(result["live_model_execution"])

    def test_blocked_but_inference_true_is_invalid(self):
        self.data["readiness"]["real_local_inference"] = True
        self.assertEqual(self.run_review()["hardware"]["state"], "INVALID_READINESS_RECEIPT")

    def test_wrong_runtime_pin_is_rejected(self):
        self.data["readiness"]["runtime_sha256"] = "0" * 64
        self.assertEqual(self.run_review()["hardware"]["state"], "INVALID_READINESS_RECEIPT")

    def test_cleanup_not_confirmed_is_reported(self):
        self.data["readiness"]["child_processes_stopped"] = False
        self.assertEqual(self.run_review()["hardware"]["state"], "INVALID_READINESS_RECEIPT")

    def test_duplicate_json_and_symlink_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"state":"blocked","state":"pass"}')
            with self.assertRaises(ValueError):
                load_json(path)
            linked = Path(directory) / "linked.json"
            linked.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "SYMLINK"):
                load_json(linked)

    def test_readiness_only_cli_does_not_claim_completed_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incoming, output = root / "inference.json", root / "review.json"
            incoming.write_text(json.dumps(self.data["readiness"]))
            cmd = [sys.executable, "-m", "research.eo001_receipt_audit.first_run.review",
                   "--inference-receipt", str(incoming), "--output", str(output)]
            done = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(json.loads(output.read_text())["evidence_coverage"], "NOT_SUPPLIED")
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            again = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(again.returncode, 0, 'existing report must not be overwritten')


if __name__ == "__main__":
    unittest.main()
