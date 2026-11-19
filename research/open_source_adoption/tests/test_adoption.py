from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adoption import (HERE, MAX_BYTES, IntakeError, canonical, check_catalogue,
                      inspect_observations, isolation_report, read_bytes, read_json)


def fixture():
    return {
        "version": 2, "status": "success",
        "eval": {"task": "synthetic-external-case", "model": "mock/review-only",
                 "created": "2026-10-29T00:00:00Z", "run_id": "synthetic-run-001",
                 "task_version": "0.1", "dataset": {"samples": 2}},
        "results": {"total_samples": 2, "completed_samples": 2,
                    "scores": [{"name": "match", "metrics": {"accuracy": {"value": 0.5}}}]},
        "samples": [
            {"id": 1, "epoch": 1, "input": "synthetic input", "target": "expected",
             "scores": {"match": {"value": 1}, "other": {"value": "C"}}},
            {"id": 2, "epoch": 1, "input": "synthetic input", "target": "expected",
             "scores": {"match": {"value": 0}, "other": {"value": {"constraint": False}}}},
        ],
    }


def ingest(log):
    raw = json.dumps(log).encode()
    return inspect_observations(raw, hashlib.sha256(raw).hexdigest())


class InspectSubsetTests(unittest.TestCase):
    def test_preserves_all_samples_and_scorers_without_promoting(self):
        report = ingest(fixture())
        self.assertEqual(len(report["samples"]), 2)
        self.assertEqual(report["samples"][0]["upstream_scores"], {"match": 1, "other": "C"})
        self.assertEqual(report["samples"][1]["upstream_scores"]["match"], 0)
        self.assertEqual(report["evidence_state"], "UNVERIFIED_EXTERNAL")
        self.assertIsNone(report["lab_verdict"])
        self.assertFalse(report["promotion_allowed"])

    def test_aggregate_one_is_never_a_sample_pass(self):
        log = fixture()
        log["results"]["scores"][0]["metrics"]["accuracy"]["value"] = 1
        log["samples"][0]["scores"] = None
        report = ingest(log)
        self.assertEqual(report["samples"][0]["upstream_scores"], {})
        self.assertIn("unscored_samples_present", report["incompleteness_reasons"])
        self.assertIsNone(report["lab_verdict"])

    def test_error_remains_visible_despite_maximum_score(self):
        log = fixture()
        log["samples"][0]["error"] = {"message": "synthetic private error"}
        report = ingest(log)
        self.assertTrue(report["samples"][0]["error_present"])
        self.assertIn("sample_error_present", report["incompleteness_reasons"])

    def test_cancelled_and_missing_attempts_are_retained(self):
        log = fixture()
        log["status"] = "cancelled"
        log["samples"].pop()
        log["results"]["completed_samples"] = 1
        report = ingest(log)
        self.assertEqual(report["declared_counts"]["total_samples"], 2)
        self.assertEqual(report["observed_sample_count"], 1)
        self.assertTrue({"execution_not_success", "planned_samples_missing", "declared_completion_incomplete"} <= set(report["incompleteness_reasons"]))

    def test_aggregate_only_log_has_no_sample_verdict(self):
        log = fixture()
        del log["samples"]
        report = ingest(log)
        self.assertEqual(report["samples"], [])
        self.assertIn("sample_evidence_absent", report["incompleteness_reasons"])

    def test_missing_results_cannot_imply_completeness(self):
        log = fixture()
        del log["results"]
        del log["eval"]["run_id"]
        report = ingest(log)
        self.assertTrue({"results_absent", "planned_count_unavailable", "run_id_absent"} <= set(report["incompleteness_reasons"]))

    def test_epochs_and_typed_ids_are_distinct(self):
        log = fixture()
        log["samples"][1]["id"] = "1"
        self.assertEqual(len(ingest(log)["samples"]), 2)
        log["samples"][1].update(id=1, epoch=2)
        self.assertEqual(len(ingest(log)["samples"]), 2)

    def test_duplicate_sample_epoch_is_rejected(self):
        log = fixture()
        log["samples"][1]["id"] = 1
        with self.assertRaises(IntakeError):
            ingest(log)

    def test_early_stopping_limits_and_invalidations_are_visible(self):
        log = fixture()
        log["invalidated"] = True
        log["results"].update(logged_samples=1, early_stopping={"stopped": True})
        log["samples"][0].update(limit={"type": "time"}, invalidation={}, error_retries=[{}])
        report = ingest(log)
        self.assertTrue({"invalidation_present", "sample_limit_present", "early_stopping_present", "logged_count_incomplete"} <= set(report["incompleteness_reasons"]))
        self.assertEqual(report["samples"][0]["retried_errors"], 1)

    def test_counts_cannot_exceed_plan(self):
        for changes in ({"total_samples": 1}, {"completed_samples": 3}, {"logged_samples": 3}):
            with self.subTest(changes=changes):
                log = fixture()
                log["results"].update(changes)
                with self.assertRaises(IntakeError):
                    ingest(log)

    def test_new_versions_and_unknown_status_require_review(self):
        for key, value in (("version", 3), ("version", True), ("status", "passed"), ("invalidated", "false")):
            with self.subTest(key=key, value=value):
                log = fixture()
                log[key] = value
                with self.assertRaises(IntakeError):
                    ingest(log)

    def test_boolean_identifiers_and_counts_are_rejected(self):
        for target, key in (("sample", "id"), ("sample", "epoch"), ("results", "total_samples")):
            with self.subTest(target=target, key=key):
                log = fixture()
                (log["samples"][0] if target == "sample" else log["results"])[key] = True
                with self.assertRaises(IntakeError):
                    ingest(log)

    def test_malformed_score_and_retry_shapes_are_rejected(self):
        for key, value in (("scores", []), ("scores", {"x": {}}), ("error_retries", "retry")):
            log = fixture()
            log["samples"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(IntakeError):
                ingest(log)

    def test_finite_structured_values_are_preserved(self):
        log = fixture()
        value = [True, None, {"a": -0.5, "b": ["I", 0]}]
        log["samples"][0]["scores"] = {"structured": {"value": value}}
        self.assertEqual(ingest(log)["samples"][0]["upstream_scores"]["structured"], value)

    def test_payload_text_is_not_exported(self):
        log = fixture()
        secret_marker = "SYNTHETIC-DO-NOT-EXPORT-RAW-TEXT"
        log["samples"][0].update(input=secret_marker, target=secret_marker,
             messages=[{"content": secret_marker}], output={"completion": secret_marker},
             metadata={"note": secret_marker}, error={"message": secret_marker})
        log["samples"][0]["scores"]["match"]["explanation"] = secret_marker
        self.assertNotIn(secret_marker, json.dumps(ingest(log)))

    def test_digest_binding_and_deterministic_output(self):
        raw = json.dumps(fixture()).encode()
        digest = hashlib.sha256(raw).hexdigest()
        first = inspect_observations(raw, digest)
        self.assertEqual(first, inspect_observations(raw, digest))
        hashed = {k: v for k, v in first.items() if k != "report_sha256"}
        self.assertEqual(hashlib.sha256(canonical(hashed)).hexdigest(), first["report_sha256"])
        for bad_raw, bad_digest in ((raw + b" ", digest), (raw, "0" * 64), (raw, "bad")):
            with self.subTest(digest=bad_digest), self.assertRaises(IntakeError):
                inspect_observations(bad_raw, bad_digest)

    def test_duplicate_keys_nonfinite_invalid_utf8_and_depth_are_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e309}', b'\xff', b'[' * 2000 + b']' * 2000):
            with self.subTest(raw=raw[:30]), self.assertRaises(IntakeError):
                read_json(raw)

    def test_size_limit(self):
        with self.assertRaises(IntakeError):
            read_json(b" " * (MAX_BYTES + 1))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "oversized.json"
            with path.open("wb") as handle:
                handle.truncate(MAX_BYTES + 1)
            with self.assertRaises(IntakeError):
                read_bytes(path)

    def test_nesting_limit_ignores_brackets_and_escapes_in_text(self):
        value = {"text": '[' * 100 + '\\"' + ']' * 100}
        self.assertEqual(read_json(json.dumps(value).encode()), value)

    def test_original_input_is_unchanged(self):
        log = fixture()
        before = copy.deepcopy(log)
        ingest(log)
        self.assertEqual(log, before)

    def test_cli_outputs_only_report_without_writing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            raw = json.dumps(fixture()).encode()
            path.write_bytes(raw)
            result = subprocess.run([sys.executable, str(HERE / "adoption.py"), "inspect-json",
                                     str(path), "--expected-sha256", hashlib.sha256(raw).hexdigest()],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIsNone(json.loads(result.stdout)["lab_verdict"])
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_cli_failure_has_no_success_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"version": true}')
            result = subprocess.run([sys.executable, str(HERE / "adoption.py"), "inspect-json",
                                     str(path), "--expected-sha256", "0" * 64], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertIn("error", json.loads(result.stderr))


class IsolationAndCatalogueTests(unittest.TestCase):
    def test_complete_catalogue_and_pins(self):
        result = check_catalogue()
        self.assertEqual(result["projects_reviewed"], 125)
        self.assertEqual(result["public_sources_pinned"], 14)
        self.assertFalse(result["external_execution_enabled"])

    def test_unpinned_source_or_cleared_marketplace_asset_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            original = json.loads((HERE / "sources.json").read_text())
            catalogue = json.loads((HERE / "catalogue.json").read_text())
            (directory / "catalogue.json").write_text(json.dumps(catalogue))
            broken = copy.deepcopy(original)
            broken["sources"][0]["commit"] = "main"
            (directory / "sources.json").write_text(json.dumps(broken))
            with self.assertRaises(IntakeError):
                check_catalogue(directory)
            (directory / "sources.json").write_text(json.dumps(original))
            catalogue["projects"][0]["listing_reuse_status"] = "approved"
            (directory / "catalogue.json").write_text(json.dumps(catalogue))
            with self.assertRaises(IntakeError):
                check_catalogue(directory)

    def test_isolation_detects_protected_edits_and_untracked_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                return subprocess.check_output(["git", "-C", folder, *args], stderr=subprocess.DEVNULL).decode().strip()
            git("init")
            (root / "protected.txt").write_text("frozen")
            git("add", "protected.txt")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "synthetic baseline")
            baseline = {"base_commit": git("rev-parse", "HEAD"), "allowed_new_prefix": "research/open_source_adoption/"}
            candidate = root / baseline["allowed_new_prefix"]
            candidate.mkdir(parents=True)
            (candidate / "new.txt").write_text("allowed")
            self.assertTrue(isolation_report(root, baseline)["isolated"])
            (root / "protected.txt").write_text("modified")
            (root / "unexpected.txt").write_text("outside")
            report = isolation_report(root, baseline)
            self.assertFalse(report["isolated"])
            self.assertEqual(report["outside_prefix"], ["protected.txt", "unexpected.txt"])


if __name__ == "__main__":
    unittest.main()
