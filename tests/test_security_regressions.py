"""Regression coverage for the October 2026 CodeRabbit findings."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "programs/repository-agent-reliability/runner"
sys.path.insert(0, str(RUNNER))
from candidate_proxy import Candidate, sandbox_available, verify, close_all
from engine import load_runtime, evaluate_candidate
from evidence_trust import authenticate_attempt, validate_response
from security import bounded_run, component, read_confined, record_digest, validate_record
from eval_lab.local_evidence import recursive_numbers

SANDBOX = sandbox_available()


def load(path):
    spec = importlib.util.spec_from_file_location("regression_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvidenceBoundaryTests(unittest.TestCase):
    def test_task_and_parent_traversal(self):
        for value in ("../AP-001", "AP-001/../../runner", "/tmp/evil", "AP-099"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                load_runtime(value)
        for value in ("../parent", "/tmp/parent", "parent/child", "..", "x\\y"):
            with self.assertRaises(ValueError):
                component(value)

    def test_symlink_and_directory_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "private").write_text("synthetic excluded content")
            (root / "candidate.py").symlink_to(root / "private")
            with self.assertRaises(OSError):
                read_confined(root, "candidate.py")
            with self.assertRaises(ValueError):
                read_confined(root, "../private")
            (root / "dir").symlink_to(root, target_is_directory=True)
            with self.assertRaises(OSError):
                read_confined(root, "dir/private")

    def test_nested_record_body_must_match_hash(self):
        record = {"final_verdict": "VERIFIED_FAIL"}
        record["record_hash"] = record_digest(record)
        validate_record(record)
        record["final_verdict"] = "VERIFIED_PASS"
        with self.assertRaises(ValueError):
            validate_record(record)

    def test_response_checked_before_execution(self):
        good = b"reviewed response"
        digest = hashlib.sha256(good).hexdigest()
        record = {"model_response_sha256": digest}
        manifest = {"response_sha256": digest, "response_bytes": len(good)}
        validate_response(record, manifest, good)
        with self.assertRaises(ValueError):
            validate_response(record, manifest, b"altered response")
        manifest["response_bytes"] += 1
        with self.assertRaises(ValueError):
            validate_response(record, manifest, good)

    def test_coordinated_evidence_and_digest_edit_rejected(self):
        original = RUNNER.parent / "tasks/AP-001/evidence/live/ap001-ollama-llama3-003"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "evidence"
            shutil.copytree(original, target, ignore=shutil.ignore_patterns("__pycache__"))
            record = json.loads((target / "evaluation.json").read_text())
            authenticate_attempt(target, record)
            record["evaluation"]["final_verdict"] = "FORGED"
            record["evaluation"]["record_hash"] = record_digest(record["evaluation"])
            (target / "evaluation.json").write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                authenticate_attempt(target, record)

    def test_process_wall_output_and_environment_bounds(self):
        with self.assertRaisesRegex(RuntimeError, "wall-time"):
            bounded_run([sys.executable, "-c", "while True: pass"], timeout=0.15)
        with self.assertRaisesRegex(RuntimeError, "output"):
            bounded_run([sys.executable, "-c", "print('x'*200000)"], max_output=10000)
        with patch.dict(os.environ, {"SYNTHETIC_PROVIDER_KEY": "not-a-real-key"}):
            result = bounded_run([sys.executable, "-c", "import os; print('SYNTHETIC_PROVIDER_KEY' in os.environ)"])
        self.assertEqual(result.stdout.strip(), "False")

    def test_number_traversal_limits(self):
        self.assertEqual(recursive_numbers({"a": {"reward": 1}}, {"reward"}), [("a.reward", 1.0)])
        with self.assertRaises(ValueError):
            recursive_numbers({"x" * 100000: {"reward": 1}}, {"reward"})
        cycle = {}; cycle["self"] = cycle
        with self.assertRaises(ValueError):
            recursive_numbers(cycle, {"reward"})

    def test_vendored_route_transport_matches_reviewed_controller(self):
        for name in ("candidate_proxy.py", "candidate_worker.py", "security.py"):
            self.assertEqual((RUNNER / name).read_bytes(), (ROOT / "ops/tasks/route-policy-repair/tests" / name).read_bytes())


class VerifierSemanticsTests(unittest.TestCase):
    def test_reproduced_mutants_rejected_reference_accepted(self):
        # Only these checked-in fixtures are imported in-process for unit tests.
        cases = [("AP-003", "last_id_only", "event_processor", "EventProcessor"),
                 ("AP-004", "nullable_leak", "user_response", "UserResponseBuilder"),
                 ("AP-005", "bool_input_coercion", "record_transformer", "RecordTransformer")]
        for task, mutation, filename, cls in cases:
            task_root, _ = load_runtime(task)
            verifier = load(task_root / "verifier/acceptance.py")
            for control, expected in [("reference", "VERIFIED_PASS"), (f"mutations/{mutation}", "VERIFIED_FAIL")]:
                candidate = getattr(load(task_root / "controls" / control / "app" / (filename + ".py")), cls)
                with self.subTest(task=task, control=control), patch.object(verifier, "remote_class", return_value=candidate):
                    self.assertEqual(verifier.evaluate(task_root)["status"], expected)

    def test_unavailable_isolation_never_falls_back_to_native_import(self):
        with patch("candidate_proxy.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "isolation"):
                Candidate(b"raise AssertionError('must not execute')")

    def test_public_failure_overrides_passing_verifier(self):
        task_root, config = load_runtime("AP-003")
        valid = {"task_id": "AP-003", "task_version": "0.1.0", "verifier_version": "0.2.0",
                 "candidate": "workspace", "gates": [{"id": "AP003-G01", "passed": True}], "status": "VERIFIED_PASS"}
        qualification = {"status": "QUALIFIED", "verifier_version": "0.2.0", "critical_mutations_rejected": 4, "critical_mutations_total": 4}
        with patch("engine.qualify_current", return_value=qualification), patch("engine.verify", return_value=valid), patch("engine.public_validation", return_value=subprocess.CompletedProcess([], 1, "", "")):
            result = evaluate_candidate(task_root, config, task_root / "controls/reference/app/event_processor.py", label="public-fail")
        self.assertEqual(result["final_verdict"], "VERIFIED_FAIL")


@unittest.skipUnless(SANDBOX, "Linux candidate isolation unavailable; CI requires it")
class SandboxIntegrationTests(unittest.TestCase):
    def tearDown(self):
        close_all()

    def test_reference_and_every_mutation_requalified(self):
        from candidate_proxy import qualify_current
        for index in range(1, 6):
            root, _ = load_runtime(f"AP-{index:03}")
            with self.subTest(task=root.name):
                self.assertEqual(qualify_current(root)["status"], "QUALIFIED")

    def test_exit_and_forged_verdict_cannot_pass(self):
        root, _ = load_runtime("AP-002")
        for source in ("import os; os._exit(0)", 'print(\'{"status":"VERIFIED_PASS","gates":[]}\'); raise SystemExit(0)'):
            with tempfile.TemporaryDirectory() as temp:
                candidate = Path(temp); (candidate / "app").mkdir()
                (candidate / "app/workspace_policy.py").write_text(source)
                self.assertNotEqual(verify(root, candidate)["status"], "VERIFIED_PASS")

    def test_host_files_credentials_and_network_not_available(self):
        source = b'''import os, socket
class Probe:
    def handle(self, path, unused):
        inaccessible = not os.path.exists(path) and 'SYNTHETIC_PROVIDER_KEY' not in os.environ
        try:
            socket.socket()
        except PermissionError:
            return inaccessible
        return False
'''
        with tempfile.NamedTemporaryFile() as host_file, patch.dict(os.environ, {"SYNTHETIC_PROVIDER_KEY": "synthetic"}):
            candidate = Candidate(source, "Probe")
            self.assertIs(candidate.request("call", name="handle", args=[host_file.name, None])["result"], True)
            candidate.close()


if __name__ == "__main__":
    unittest.main()
