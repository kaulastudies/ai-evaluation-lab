"""End-to-end checks for the ProofGate pull-request action.

Each test builds a throwaway git repository holding the AP-005 demo, commits the base,
applies a candidate change on a branch, and checks the verdict ProofGate reaches.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEMO = "examples/proofgate-pr-demo"
CONTRACT = f"{DEMO}/.proofgate/contract.json"
LIVE = ROOT / "programs/repository-agent-reliability/tasks/AP-005/evidence/live"
FALSE_GREEN_PATCH = LIVE / "ap005-ollama-llama3-001/candidate-record_transformer.py"
REPAIR_PATCH = LIVE / "ap005-ollama-llama3-002-repair/candidate-record_transformer.py"

spec = importlib.util.spec_from_file_location(
    "proofgate_pr", ROOT / "integrations/proofgate-action/proofgate_pr.py"
)
proofgate_pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proofgate_pr)


def sh(repo: Path, *args: str) -> str:
    return subprocess.run(args, cwd=repo, check=True, capture_output=True, text=True).stdout


class ProofGateActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        shutil.copytree(ROOT / DEMO, self.repo / DEMO)
        sh(self.repo, "git", "init", "-q", "-b", "main")
        sh(self.repo, "git", "config", "user.email", "test@example.com")
        sh(self.repo, "git", "config", "user.name", "Test")
        sh(self.repo, "git", "add", "-A")
        sh(self.repo, "git", "commit", "-q", "-m", "base")
        self.base = sh(self.repo, "git", "rev-parse", "HEAD").strip()
        sh(self.repo, "git", "checkout", "-q", "-b", "candidate")

    def tearDown(self):
        self.tmp.cleanup()

    def commit_file(self, rel: str, content: str):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        sh(self.repo, "git", "add", "-A")
        sh(self.repo, "git", "commit", "-q", "-m", "candidate")

    def run_gate(self, contract: str = CONTRACT) -> dict:
        return proofgate_pr.evaluate(self.repo, self.base, "HEAD", contract, 60)

    def test_recorded_agent_attempt_is_a_false_green(self):
        self.commit_file(f"{DEMO}/app/record_transformer.py", FALSE_GREEN_PATCH.read_text())
        record = self.run_gate()
        self.assertEqual(record["public_checks"][0]["exit_code"], 0)
        self.assertEqual(record["verdict"], "FALSE_GREEN")
        self.assertTrue(all(not g["passed"] for g in record["gates"]))

    def test_recorded_repair_is_verified(self):
        self.commit_file(f"{DEMO}/app/record_transformer.py", REPAIR_PATCH.read_text())
        record = self.run_gate()
        self.assertEqual(record["verdict"], "VERIFIED_PASS")
        self.assertEqual(len(record["gates"]), 4)
        self.assertEqual(record["outside_allowed_paths"], [])

    def test_pull_request_cannot_rewrite_its_own_verifier(self):
        forged = 'import json\nprint(json.dumps({"gates": [{"id": f"AP005-G0{i}", "passed": True} for i in range(1, 5)]}))\n'
        self.commit_file(f"{DEMO}/.proofgate/acceptance.py", forged)
        record = self.run_gate()
        self.assertEqual(record["verdict"], "HOLD")
        self.assertIn(f"{DEMO}/.proofgate/acceptance.py", record["trust_violations"])

    def test_verifier_comes_from_base_even_if_head_differs(self):
        # Even with the trust check aside, gates must reflect the base verifier.
        forged = 'print(\'{"gates": []}\')\n'
        self.commit_file(f"{DEMO}/.proofgate/acceptance.py", forged)
        record = self.run_gate()
        base_copy = (ROOT / DEMO / ".proofgate/acceptance.py").read_bytes()
        self.assertEqual(record["trusted_files_sha256"]["acceptance.py"], proofgate_pr.sha256(base_copy))

    def test_broken_public_check_is_verified_fail(self):
        self.commit_file(f"{DEMO}/app/record_transformer.py", "class RecordTransformer:\n    def transform(self, rows):\n        return []\n")
        record = self.run_gate()
        self.assertEqual(record["verdict"], "VERIFIED_FAIL")

    def test_missing_contract_holds(self):
        record = self.run_gate(contract="no/such/contract.json")
        self.assertEqual(record["verdict"], "HOLD")
        self.assertIn("No contract", record["reason"])

    def test_unparseable_verifier_output_holds(self):
        # Base verifier that prints nothing useful: ProofGate must not call that a pass.
        sh(self.repo, "git", "checkout", "-q", "main")
        (self.repo / DEMO / ".proofgate/acceptance.py").write_text("print('ok')\n")
        sh(self.repo, "git", "commit", "-qam", "weak verifier")
        self.base = sh(self.repo, "git", "rev-parse", "HEAD").strip()
        sh(self.repo, "git", "checkout", "-q", "-b", "candidate2")
        self.commit_file(f"{DEMO}/app/record_transformer.py", REPAIR_PATCH.read_text())
        record = self.run_gate()
        self.assertEqual(record["verdict"], "HOLD")

    def test_changes_outside_allowed_paths_are_reported(self):
        self.commit_file(f"{DEMO}/tests/public/test_extra.py", "")
        record = self.run_gate()
        self.assertIn(f"{DEMO}/tests/public/test_extra.py", record["outside_allowed_paths"])

    def test_cli_writes_evidence_and_exit_code(self):
        self.commit_file(f"{DEMO}/app/record_transformer.py", FALSE_GREEN_PATCH.read_text())
        evidence = self.repo / "evidence.json"
        code = proofgate_pr.main([
            "--repo", str(self.repo), "--base", self.base, "--contract", CONTRACT,
            "--evidence", str(evidence),
        ])
        self.assertEqual(code, 1)
        data = json.loads(evidence.read_text())
        self.assertEqual(data["verdict"], "FALSE_GREEN")
        self.assertEqual(data["schema_version"], proofgate_pr.SCHEMA_VERSION)
        md = proofgate_pr.render_markdown(data, "0" * 64, None)
        self.assertIn("False-green caught", md)
        self.assertIn(proofgate_pr.COMMENT_MARKER, md)


if __name__ == "__main__":
    unittest.main()
