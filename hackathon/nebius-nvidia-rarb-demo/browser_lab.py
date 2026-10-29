"""Execute the bundled, unmodified Python checks in CPython or Pyodide.

This is current-verifier re-execution, not the source-exact historical engine.
Only fixed candidates in browser-evidence.json are accepted by the UI/worker.
"""
from __future__ import annotations
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from typing import Any
import unittest


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def run_case(bundle: dict, variant_id: str) -> dict:
    # Native callers may execute only the repository-reviewed fixed demo bundle.
    # Arbitrary native candidates must use the isolated RARB runner.
    if sys.platform != "emscripten":
        from build_evidence import build_browser
        if bundle != build_browser():
            raise ValueError("Artifact integrity mismatch against reviewed demo bundle")
    variant = bundle["variants"][variant_id]
    task = bundle["tasks"][variant["task_id"]]
    for source, expected in [(variant["source"], variant["sha256"]),
                             (task["public_source"], task["public_sha256"]),
                             (task["verifier_source"], task["verifier_sha256"]),
                             (bundle["admission_source"], bundle["admission_sha256"])]:
        if digest(source) != expected:
            raise ValueError("Artifact integrity mismatch; execution refused")
    admission_scope = {"ast": ast, "Any": Any}
    exec(compile(bundle["admission_source"], "canonical-admission.py", "exec"), admission_scope)
    admission = admission_scope["candidate_admission"](variant["source"], task["admission"])
    report = {"mode": "browser-python-verifier-reexecution-v1", "variant": variant_id,
              "candidate_kind": variant["kind"], "task_id": variant["task_id"],
              "evidence_commit": bundle["evidence_commit"], "python_version": sys.version.split()[0],
              "candidate_sha256": variant["sha256"], "public_test_sha256": task["public_sha256"],
              "verifier_sha256": task["verifier_sha256"], "admission": admission,
              "fresh_model_inference": False, "historical_source_exact_replay": False}
    if not admission["accepted"]:
        return {**report, "final_verdict": "HOLD", "gates": [], "public_tests_passed": None}
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="proofgate-") as temp:
        root = Path(temp)
        candidate = root / task["candidate_path"]
        candidate.parent.mkdir(parents=True)
        candidate.write_text(variant["source"])
        (candidate.parent / "__init__.py").write_text("")
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                del sys.modules[key]
        sys.path.insert(0, str(root))
        try:
            public_scope = {"__name__": "proofgate_public_tests"}
            exec(compile(task["public_source"], "canonical-public-test.py", "exec"), public_scope)
            suite = unittest.TestSuite()
            for value in public_scope.values():
                if isinstance(value, type) and issubclass(value, unittest.TestCase):
                    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(value))
            output = io.StringIO()
            result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
            verifier_scope = {"__name__": "proofgate_verifier"}
            exec(compile(task["verifier_source"], "canonical-verifier.py", "exec"), verifier_scope)
            try:
                verification = verifier_scope["evaluate"](root)
                verdict = "VERIFIED_PASS" if result.wasSuccessful() and verification["status"] == "VERIFIED_PASS" else "VERIFIED_FAIL"
            except Exception as exc:
                verification = {"gates": [], "status": "VERIFIED_FAIL", "error": f"{type(exc).__name__}: {exc}"}
                verdict = "VERIFIED_FAIL"
            report.update({"public_tests_passed": result.wasSuccessful(), "public_tests_run": result.testsRun,
                           "public_test_output": output.getvalue(), "gates": verification["gates"],
                           "final_verdict": verdict, "verifier_error": verification.get("error"),
                           "false_green": result.wasSuccessful() and verdict == "VERIFIED_FAIL",
                           "candidate_unchanged": digest(candidate.read_text()) == variant["sha256"]})
            if not report["candidate_unchanged"]:
                report["final_verdict"] = "HOLD"
        finally:
            sys.path.remove(str(root))
            for key in list(sys.modules):
                if key == "app" or key.startswith("app."):
                    del sys.modules[key]
    report["check_duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return report


if __name__ == "__main__":
    bundle = json.loads(Path(__file__).with_name("browser-evidence.json").read_text())
    print(json.dumps(run_case(bundle, sys.argv[1] if len(sys.argv) > 1 else "false-green"), indent=2))
