"""Build the judge bundle from canonical evidence; never invent run outcomes."""
from __future__ import annotations

import hashlib
import ast
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROGRAM = ROOT / "programs/repository-agent-reliability"
CASES = {
    "false-green": ("AP-005", "ap005-ollama-llama3-001"),
    "repair": ("AP-005", "ap005-ollama-llama3-002-repair"),
    "nemotron": ("AP-001", "ap001-nebius-nemotron-phase12-001"),
    "failure": ("AP-001", "ap001-ollama-llama3-phase12-001"),
    "hold": ("AP-003", "ap003-ollama-llama3-002-repair"),
}


def evidence_path(case: str) -> Path:
    task, run = CASES[case]
    return PROGRAM / "tasks" / task / "evidence/live" / run


def build() -> dict:
    # Bind links to the commit that last changed canonical evidence, not UI commits.
    ref = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", "programs/repository-agent-reliability"],
        cwd=ROOT, text=True,
    ).strip()
    bundle = {
        "schema_version": 1,
        "evidence_commit": ref,
        "repository": "https://github.com/kaulastudies/ai-evaluation-lab",
        "summary": json.loads((PROGRAM / "metrics/summary.json").read_text()),
        "cases": {},
    }
    for key in CASES:
        folder = evidence_path(key)
        manifest = json.loads((folder / "manifest.json").read_text())
        evaluation = json.loads((folder / "evaluation.json").read_text())
        replay_path = folder / "replay.json"
        if not replay_path.exists():
            replay_path = folder / "replay-report.json"
        replay = json.loads(replay_path.read_text()) if replay_path.exists() else None
        candidates = list(folder.glob("candidate-*"))
        candidate = candidates[0].read_bytes().decode("utf-8") if candidates else None
        if candidates:
            assert len(candidates) == 1
            assert hashlib.sha256(candidates[0].read_bytes()).hexdigest() == manifest["candidate_sha256"]
        response = folder / "model-response.txt"
        assert hashlib.sha256(response.read_bytes()).hexdigest() == manifest["response_sha256"]
        task = PROGRAM / "tasks" / manifest["task_id"]
        bundle["cases"][key] = {
            "manifest": manifest,
            "evaluation": evaluation,
            "replay": replay,
            "candidate": candidate,
            "response": response.read_bytes().decode("utf-8"),
            "candidate_filename": candidates[0].name if candidates else None,
            "path": folder.relative_to(ROOT).as_posix(),
            "brief": (task / "agent_brief.md").read_text(),
            "qualification": json.loads((task / "evidence/verifier-qualification.json").read_text()),
        }
    return bundle


def build_browser() -> dict:
    """Bundle unchanged Python tests/verifiers and only reviewed, fixed candidates."""
    evidence = build()
    result = {"schema_version": 1, "evidence_commit": evidence["evidence_commit"], "tasks": {}, "variants": {}}
    engine = (PROGRAM / "runner/engine.py").read_text()
    admission_node = next(n for n in ast.parse(engine).body if isinstance(n, ast.FunctionDef) and n.name == "candidate_admission")
    result["admission_source"] = ast.get_source_segment(engine, admission_node)
    result["admission_sha256"] = hashlib.sha256(result["admission_source"].encode()).hexdigest()
    for task_id in ("AP-001", "AP-005"):
        root = PROGRAM / "tasks" / task_id
        config = json.loads((root / "runtime.json").read_text())
        public = next((root / "fixture/tests/public").glob("test_*.py"))
        verifier = root / config["verifier_path"]
        result["tasks"][task_id] = {
            "candidate_path": config["candidate_path"], "admission": config["admission"],
            "public_source": public.read_bytes().decode(), "verifier_source": verifier.read_bytes().decode(),
            "public_sha256": hashlib.sha256(public.read_bytes()).hexdigest(),
            "verifier_sha256": hashlib.sha256(verifier.read_bytes()).hexdigest(),
        }
    for key in ("false-green", "repair", "nemotron", "failure"):
        case = evidence["cases"][key]
        result["variants"][key] = {"task_id": case["manifest"]["task_id"], "source": case["candidate"],
            "sha256": case["manifest"]["candidate_sha256"], "path": case["path"],
            "kind": "recorded_model_candidate", "expected_verdict": case["manifest"]["final_verdict"]}
    root = PROGRAM / "tasks/AP-005"
    for name, rel in [("reference", "controls/reference"), ("known-bad", "controls/known_bad"),
                      ("drop-inactive", "controls/mutations/drop_inactive"), ("coerce-zero", "controls/mutations/coerce_zero"),
                      ("collapse-note", "controls/mutations/collapse_empty_note"), ("mutate-input", "controls/mutations/mutate_input")]:
        source = root / rel / "app/record_transformer.py"
        result["variants"][name] = {"task_id": "AP-005", "source": source.read_bytes().decode(),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "path": source.relative_to(ROOT).as_posix(),
            "kind": "qualification_control", "expected_verdict": "VERIFIED_PASS" if name == "reference" else "VERIFIED_FAIL"}
    return result


if __name__ == "__main__":
    bundle = build()
    target = HERE / "evidence.json"
    target.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / "browser-evidence.json").write_text(json.dumps(build_browser(), indent=2) + "\n")
    print(f"Built {len(bundle['cases'])} cases and {len(bundle['summary']['attempts'])} ledger entries")
