from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import tempfile

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER = TASK_ROOT / "runner" / "admission_replay.py"
EVIDENCE = (
    TASK_ROOT
    / "evidence"
    / "live"
    / "ap001-ollama-llama3-002"
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rarb-admission-replay-") as td:
        report = Path(td) / "report.json"
        process = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--evidence-dir",
                str(EVIDENCE),
                "--out",
                str(report),
            ],
            cwd=TASK_ROOT,
            text=True,
            capture_output=True,
        )

        print(process.stdout.strip())
        if process.returncode != 0:
            print(process.stderr, file=sys.stderr)
            print("PHASE 3C ADMISSION REPLAY FAILED")
            return 1

        payload = json.loads(report.read_text(encoding="utf-8"))
        ok = (
            payload["status"] == "ADMISSION_REPLAY_VERIFIED"
            and payload["replayed_candidate_admission"]["accepted"] is False
            and payload["replayed_candidate_admission"]["reason"]
            == "mixed prose/code-fence output is not allowed"
            and payload["replayed_verdict"] == "HOLD"
            and all(payload["checks"].values())
        )

        print(
            "PHASE 3C ADMISSION REPLAY GREEN"
            if ok
            else "PHASE 3C ADMISSION REPLAY FAILED"
        )
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
