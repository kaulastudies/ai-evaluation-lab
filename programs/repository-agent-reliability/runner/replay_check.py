from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPLAY = RUNNER_ROOT / "replay.py"
EVIDENCE = (
    PROGRAM_ROOT
    / "tasks"
    / "AP-002"
    / "evidence"
    / "live"
    / "ap002-ollama-llama3-001"
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rarb-generic-replay-") as td:
        out = Path(td) / "replay-report.json"

        process = subprocess.run(
            [
                sys.executable,
                str(REPLAY),
                "--evidence-dir",
                str(EVIDENCE),
                "--out",
                str(out),
            ],
            cwd=PROGRAM_ROOT,
            text=True,
            capture_output=True,
        )

        print(process.stdout.strip())

        if process.returncode != 0:
            print(process.stderr, file=sys.stderr)
            print("PHASE 4B GENERIC REPLAY FAILED")
            return 1

        report = json.loads(out.read_text(encoding="utf-8"))

        expected_hash = (
            "7a8e86fd2929438f545a9379117dc4eb"
            "f43eccb0391f46ac9c4ba012f008bb49"
        )

        ok = (
            report["status"] == "GENERIC_REPLAY_VERIFIED"
            and report["task_id"] == "AP-002"
            and report["replayed_candidate_admission"]["accepted"] is True
            and report["stored_record_hash"] == expected_hash
            and report["replayed_record_hash"] == expected_hash
            and report["replayed_verdict"] == "VERIFIED_PASS"
            and all(report["checks"].values())
        )

        print(
            "PHASE 4B GENERIC REPLAY GREEN"
            if ok
            else "PHASE 4B GENERIC REPLAY FAILED"
        )
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
