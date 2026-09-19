from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPLAY = RUNNER_ROOT / "replay.py"

CASES = [
    {
        "task_id": "AP-002",
        "evidence": (
            PROGRAM_ROOT
            / "tasks"
            / "AP-002"
            / "evidence"
            / "live"
            / "ap002-ollama-llama3-001"
        ),
        "record_hash": (
            "7a8e86fd2929438f545a9379117dc4eb"
            "f43eccb0391f46ac9c4ba012f008bb49"
        ),
        "verdict": "VERIFIED_PASS",
    },
    {
        "task_id": "AP-003",
        "evidence": (
            PROGRAM_ROOT
            / "tasks"
            / "AP-003"
            / "evidence"
            / "live"
            / "ap003-ollama-llama3-001"
        ),
        "record_hash": (
            "934c5f633d9d37bd55e6dddbaf73903f"
            "ea16669fcc6c6acc0fa586c795dd325d"
        ),
        "verdict": "VERIFIED_FAIL",
    },
    {
        "task_id": "AP-004",
        "evidence": (
            PROGRAM_ROOT
            / "tasks"
            / "AP-004"
            / "evidence"
            / "live"
            / "ap004-ollama-llama3-001"
        ),
        "record_hash": None,
        "verdict": "HOLD",
    },
]


def main() -> int:
    all_ok = True

    with tempfile.TemporaryDirectory(
        prefix="rarb-source-exact-check-"
    ) as td:
        temp = Path(td)

        for index, case in enumerate(CASES, start=1):
            out = temp / f"replay-{index}.json"

            process = subprocess.run(
                [
                    sys.executable,
                    str(REPLAY),
                    "--evidence-dir",
                    str(case["evidence"]),
                    "--out",
                    str(out),
                ],
                cwd=PROGRAM_ROOT,
                text=True,
                capture_output=True,
            )

            if process.stdout:
                print(process.stdout.strip())
            if process.stderr:
                print(process.stderr, file=sys.stderr)

            if process.returncode != 0 or not out.is_file():
                all_ok = False
                continue

            report = json.loads(
                out.read_text(encoding="utf-8")
            )

            ok = (
                report["status"]
                == "SOURCE_EXACT_REPLAY_VERIFIED"
                and report["replay_mode"]
                == "source-exact-detached-worktree-v1"
                and report["task_id"] == case["task_id"]
                and report["stored_record_hash"]
                == case["record_hash"]
                and report["replayed_record_hash"]
                == case["record_hash"]
                and report["replayed_verdict"]
                == case["verdict"]
                and report["replay_provider"] == "mock"
                and all(report["checks"].values())
            )

            print(
                f"{case['task_id']} SOURCE-EXACT REPLAY "
                + ("GREEN" if ok else "FAILED")
            )
            all_ok = all_ok and ok

    print(
        "PHASE 6A SOURCE-EXACT REPLAY GREEN"
        if all_ok
        else "PHASE 6A SOURCE-EXACT REPLAY FAILED"
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
