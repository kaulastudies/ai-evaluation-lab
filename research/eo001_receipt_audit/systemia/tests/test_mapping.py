"""Negative controls for replay of the independent recorded mapping evidence."""
from copy import deepcopy
import json
import unittest
from cryptography.exceptions import InvalidSignature
from research.eo001_receipt_audit.systemia.evaluate import HERE, check


class MappingEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recorded = json.loads((HERE / "evidence.json").read_text())

    def setUp(self):
        self.report = deepcopy(self.recorded)

    def test_recording_replays_with_separate_truth_and_authority(self):
        summary = check(self.report)
        self.assertEqual(summary, self.report["summary"])
        self.assertEqual(summary["signed_false_claim"]["effect_truth"], "CONTRADICTED_BY_SYNTHETIC_ORACLE")

    def test_missing_native_case_cannot_improve_the_report(self):
        self.report["native"]["cases"].pop()
        with self.assertRaisesRegex(ValueError, "NATIVE_CASE_INVENTORY"):
            check(self.report)

    def test_completion_cannot_be_promoted_from_native_attestation(self):
        self.report["native"]["cases"][0]["state_after"]["tasks"][0]["status"] = "complete"
        with self.assertRaisesRegex(ValueError, "NATIVE_QUARANTINE_RELEASED"):
            check(self.report)

    def test_retry_permission_cannot_be_promoted(self):
        self.report["native"]["cases"][0]["state_after"]["tasks"][0]["recovery_hold"]["reconciliation"]["retry_authorized"] = True
        with self.assertRaisesRegex(ValueError, "NATIVE_ATTESTATION_PROMOTED"):
            check(self.report)

    def test_altered_observer_claim_does_not_replay(self):
        self.report["native"]["cases"][0]["observation"]["claims"]["outcome"] = "unknown"
        with self.assertRaises(InvalidSignature):
            check(self.report)

    def test_oracle_cannot_be_rewritten_to_match_observer(self):
        self.report["native"]["oracle"]["effects"].append({"effect": "invented"})
        with self.assertRaisesRegex(ValueError, "ORACLE_CHANGED"):
            check(self.report)

    def test_tamper_rejection_cannot_be_relabelled_as_authentication(self):
        self.report["sessions"]["tamper"]["verdict"]["observation_errors"] = []
        with self.assertRaisesRegex(ValueError, "RECORDED_VERDICT_MISMATCH"):
            check(self.report)

    def test_model_provenance_cannot_be_inferred_from_candidate_name(self):
        self.report["sessions"]["none"]["candidate_kind"] = "scripted_control"
        with self.assertRaisesRegex(ValueError, "RECORDED_VERDICT_MISMATCH"):
            check(self.report)


if __name__ == "__main__":
    unittest.main()
