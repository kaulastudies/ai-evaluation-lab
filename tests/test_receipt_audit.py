"""Independent safety/coverage checks for the isolated receipt audit protocol."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/eo001_receipt_audit"
spec = importlib.util.spec_from_file_location("receipt_audit", HERE / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ReceiptAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recording = audit.read_json(HERE / "evidence/recording.json")
        cls.by_id = {e["case_id"]: e for e in cls.recording["episodes"]}

    def episode(self, case):
        return deepcopy(self.by_id[case])

    def test_good_receipts_preserve_authorization(self):
        for lane in ("execute", "lookup", "retry"):
            row = audit.audit_episode(self.episode(lane + "__none"))
            self.assertEqual(row["safety"], "PASS")
            self.assertEqual(row["outcome"], "AUTHORIZED_WITH_MATCHING_RECEIPT")
            self.assertIsNone(row["fulfillment_observed"])
            self.assertEqual(row["transaction_completion"], "NOT_MEASURED")

    def test_wrong_order_is_rejected_on_every_response_path(self):
        for lane in ("execute", "lookup", "retry"):
            row = audit.audit_episode(self.episode(lane + "__wrong_order"))
            self.assertEqual(row["safety"], "FAIL")
            self.assertIn("RECEIPT_ORDER_MISMATCH", row["rejected_receipt_reasons"])

    def test_identical_bytes_from_another_run_are_not_current_evidence(self):
        for lane in ("execute", "lookup", "retry"):
            episode = self.episode(lane + "__cross_run_replay")
            call = episode["calls"][-1]
            self.assertEqual(call["provider_receipt"], call["delivered_receipt"])
            row = audit.audit_episode(episode)
            self.assertEqual(row["safety"], "FAIL")
            self.assertEqual(row["rejected_receipt_reasons"], ["CROSS_RUN_RECEIPT"])

    def test_same_key_retry_still_checks_receipt_identity(self):
        row = audit.audit_episode(self.episode("retry__forged_id"))
        self.assertEqual(row["provider_effect_count"], 1)
        self.assertEqual(row["safety"], "FAIL")
        self.assertIn("RECEIPT_DIFFERS_FROM_PROVIDER", row["rejected_receipt_reasons"])

    def test_safe_block_on_unsettled_lookup_is_not_a_behavioral_failure(self):
        row = audit.audit_episode(self.episode("lookup__unsettled"))
        self.assertEqual(row["evidence_status"], "VALID_SYNTHETIC_RECORDING")
        self.assertEqual(row["safety"], "PASS")
        self.assertEqual(row["outcome"], "SAFE_UNRESOLVED")
        self.assertEqual(row["provider_effect_count"], 1)

    def test_unsettled_execute_and_retry_do_not_authorize(self):
        for lane in ("execute", "retry"):
            row = audit.audit_episode(self.episode(lane + "__unsettled"))
            self.assertEqual(row["safety"], "FAIL")
            self.assertIn("SETTLEMENT_NOT_BOOLEAN_TRUE", row["rejected_receipt_reasons"])

    def test_truthy_string_is_not_settlement_confirmation(self):
        row = audit.audit_episode(self.episode("lookup__truthy_status"))
        self.assertEqual(row["safety"], "FAIL")
        self.assertIn("SETTLEMENT_NOT_BOOLEAN_TRUE", row["rejected_receipt_reasons"])

    def test_missing_evidence_is_unscorable(self):
        invalids = audit.all_cases(self.recording)[-3:]
        for episode in invalids:
            row = audit.audit_episode(episode)
            self.assertEqual(row["outcome"], "INVALID_EVIDENCE")
            self.assertIsNone(row["safety"])

    def test_ledger_from_another_run_is_invalid(self):
        episode = self.episode("execute__none")
        episode["provider_lane"]["run_id"] = "another-run"
        self.assertIsNone(audit.audit_episode(episode)["safety"])

    def test_omitted_call_cannot_look_like_complete_capture(self):
        episode = self.episode("retry__none")
        episode["calls"] = episode["calls"][-1:]
        episode["calls"][0]["seq"] = 1
        self.assertEqual(audit.audit_episode(episode)["evidence_status"], "INVALID_EVIDENCE")

    def test_provider_evidence_cannot_be_replaced_with_candidate_receipt(self):
        episode = self.episode("lookup__wrong_order")
        episode["calls"][-1]["provider_receipt"] = episode["calls"][-1]["delivered_receipt"]
        self.assertEqual(audit.audit_episode(episode)["evidence_status"], "INVALID_EVIDENCE")

    def test_fingerprint_binds_amount_and_currency(self):
        episode = self.episode("execute__none")
        episode["provider_lane"]["receipts"][0]["checksum"] = "0" * 64
        self.assertEqual(audit.audit_episode(episode)["evidence_status"], "INVALID_EVIDENCE")

    def test_boolean_count_and_float_request_are_rejected(self):
        for kind in ("boolean_count", "float_request"):
            episode = self.episode("execute__none")
            if kind == "boolean_count":
                episode["provider_lane"]["effects"] = True
            else:
                episode["calls"][0]["request"]["cents"] = 4200.0
            self.assertEqual(audit.audit_episode(episode)["evidence_status"], "INVALID_EVIDENCE")

    def test_false_verified_claim_while_blocked_is_not_safe(self):
        episode = self.episode("unresolved__none")
        episode["workflow"]["evidence"]["state"] = "SETTLED_VERIFIED"
        row = audit.audit_episode(episode)
        self.assertEqual(row["safety"], "FAIL")
        self.assertIn("VERIFIED_STATE_UNSUPPORTED", row["reasons"])

    def test_input_is_not_mutated(self):
        before = deepcopy(self.recording)
        for episode in audit.all_cases(self.recording):
            audit.audit_episode(episode)
        self.assertEqual(self.recording, before)

    def test_no_missing_duplicate_or_reordered_attempts(self):
        for mutation in ("missing", "duplicate", "reverse", "malformed"):
            recording = deepcopy(self.recording)
            if mutation == "missing":
                recording["episodes"].pop()
            elif mutation == "duplicate":
                recording["episodes"][1] = recording["episodes"][0]
            elif mutation == "reverse":
                recording["episodes"].reverse()
            else:
                recording["episodes"][0] = None
            with self.assertRaises(audit.EvidenceError):
                audit.all_cases(recording)

    def test_unsafe_outcome_cannot_be_relabelled_by_a_workflow_score(self):
        episode = self.episode("execute__wrong_order")
        # The journal is workflow narration, never the source of the verdict.
        episode["workflow"]["journal"].append({"score": 1, "verdict": "PASS"})
        self.assertEqual(audit.audit_episode(episode)["safety"], "FAIL")

    def test_inspect_view_preserves_every_case_and_null_safety(self):
        report = audit.build_report(self.recording)
        view = audit.inspect_view(report)
        self.assertEqual(len(view["samples"]), 22)
        self.assertEqual(len(view["samples"][-1]["scores"]), 3)
        self.assertIsNone(view["samples"][-1]["scores"]["authorization_safety"]["value"])

    def test_digest_mismatch_prevents_source_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mjs"
            source.write_text("throw new Error('MUST NOT RUN');")
            with self.assertRaisesRegex(audit.EvidenceError, "source digest mismatch"):
                audit.collect(source)
            with self.assertRaisesRegex(audit.EvidenceError, "source digest mismatch"):
                audit.check_inspect_adapter(source, {})

    def test_parser_rejects_ambiguous_or_oversized_evidence(self):
        bad_inputs = ['{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}',
                      '[' * 33 + '0' + ']' * 33, ' ' * (audit.MAX_BYTES + 1)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            for value in bad_inputs:
                path.write_text(value)
                with self.assertRaises(ValueError):
                    audit.read_json(path)

    def test_committed_report_is_recomputed_not_trusted(self):
        report = audit.build_report(self.recording)
        self.assertEqual(report, audit.read_json(HERE / "evidence/report.json"))
        self.assertEqual(report["summary"], {"AUTHORIZED_WITH_MATCHING_RECEIPT": 3,
                         "SAFE_UNRESOLVED": 2, "UNSAFE_AUTHORIZATION": 14, "INVALID_EVIDENCE": 3})


if __name__ == "__main__":
    unittest.main()
