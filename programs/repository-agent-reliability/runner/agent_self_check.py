import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

RUNNER_ROOT = Path(__file__).resolve().parent
REPO_ROOT = RUNNER_ROOT.parents[2]

AGENT_EVALUATE = RUNNER_ROOT / "agent_evaluate.py"
AGENT_REPLAY = RUNNER_ROOT / "agent_replay.py"
SOURCE_COMMIT = "9cd80fdcbb2334dded7ebed61ff18dd84a5159e1"

PASSING_CANDIDATE = '''
class ResourceView:
    def __init__(self):
        self.current_resource = None
        self.value = None

    def select_resource(self, resource, fetch):
        self.current_resource = resource
        def on_complete(value, _requested_resource=resource):
            if self.current_resource is _requested_resource:
                self.value = value
        fetch(resource, on_complete)
'''

class TestAgentWorkspace(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.evidence_dir = self.root / "evidence"
        self.evidence_dir.mkdir()
        self.prompt = self.evidence_dir / "prompt.txt"
        self.prompt.write_text("dummy prompt", encoding="utf-8")
        self.summary = self.evidence_dir / "model-response.txt"
        self.summary.write_text("dummy summary", encoding="utf-8")
        
    def tearDown(self):
        self.temp_dir.cleanup()

    def run_evaluate(self, candidate_code, expected_verdict, expected_exit_code, source_commit=SOURCE_COMMIT):
        candidate = self.evidence_dir / "candidate-resource_view.py"
        candidate.write_text(candidate_code, encoding="utf-8")
        
        eval_out = self.evidence_dir / "evaluation.json"
        manifest_out = self.evidence_dir / "manifest.json"
        
        cmd = [
            sys.executable, str(AGENT_EVALUATE),
            "--task-id", "AP-001",
            "--candidate", str(candidate),
            "--prompt-file", str(self.prompt),
            "--summary-file", str(self.summary),
            "--source-commit", source_commit,
            "--run-label", "test-run",
            "--out-eval", str(eval_out),
            "--out-manifest", str(manifest_out)
        ]
        
        p = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, expected_exit_code, f"evaluate failed: stdout: {p.stdout} \nstderr: {p.stderr}")
        
        if eval_out.exists():
            record = json.loads(eval_out.read_text(encoding="utf-8"))
            self.assertEqual(record["final_verdict"], expected_verdict)
            return record
        return None

    def run_replay(self, expected_exit_code):
        cmd = [
            sys.executable, str(AGENT_REPLAY),
            "--evidence-dir", str(self.evidence_dir),
            "--out", str(self.evidence_dir / "replay.json")
        ]
        p = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, expected_exit_code, f"replay failed: stdout: {p.stdout} \nstderr: {p.stderr}")
        p_out = self.evidence_dir / "replay.json"
        return json.loads(p_out.read_text(encoding="utf-8")) if p_out.exists() else None

    def test_passing_candidate(self):
        self.run_evaluate(PASSING_CANDIDATE, "VERIFIED_PASS", 0)
        report = self.run_replay(0)
        self.assertEqual(report["status"], "SOURCE_EXACT_REPLAY_VERIFIED")
        
    def test_invalid_candidate(self):
        self.run_evaluate("def foo(): pass", "HOLD", 2)
        report = self.run_replay(0)
        self.assertEqual(report["status"], "SOURCE_EXACT_REPLAY_VERIFIED")

    def test_failing_candidate(self):
        code = '''
class ResourceView:
    def __init__(self):
        self.current_resource = None
        self.value = None
    def select_resource(self, r, f):
        self.current_resource = r
        def cb(v):
            self.value = "wrong"
        f(r, cb)
'''
        self.run_evaluate(code, "VERIFIED_FAIL", 1)
        report = self.run_replay(0)
        self.assertEqual(report["status"], "SOURCE_EXACT_REPLAY_VERIFIED")

    def test_hash_mismatch(self):
        self.run_evaluate(PASSING_CANDIDATE, "VERIFIED_PASS", 0)
        candidate = self.evidence_dir / "candidate-resource_view.py"
        candidate.write_text("modified", encoding="utf-8")
        report = self.run_replay(1)
        self.assertIsNone(report) # It exits early with RuntimeError

    def test_source_commit_unavailable(self):
        self.run_evaluate(PASSING_CANDIDATE, "VERIFIED_PASS", 0, source_commit="0000000000000000000000000000000000000000")
        report = self.run_replay(1)
        self.assertIsNone(report) # Exits early with RuntimeError

    def test_trusted_boundary_mismatch(self):
        self.run_evaluate(PASSING_CANDIDATE, "VERIFIED_PASS", 0)
        eval_out = self.evidence_dir / "evaluation.json"
        data = json.loads(eval_out.read_text(encoding="utf-8"))
        data["trusted_files_unchanged"] = False
        eval_out.write_text(json.dumps(data), encoding="utf-8")
        
        report = self.run_replay(1)
        self.assertEqual(report["status"], "SOURCE_EXACT_REPLAY_MISMATCH")

if __name__ == "__main__":
    unittest.main(verbosity=2)
