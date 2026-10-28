"""Build the judge bundle from canonical evidence; never invent run outcomes."""
from __future__ import annotations

import hashlib
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


if __name__ == "__main__":
    bundle = build()
    target = HERE / "evidence.json"
    target.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Built {len(bundle['cases'])} cases and {len(bundle['summary']['attempts'])} ledger entries")
