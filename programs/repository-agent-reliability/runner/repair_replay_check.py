from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPLAY = RUNNER_ROOT / "repair_replay.py"

CASES = [
    {
        "label": "AP-003 repair #002 HOLD",
        "evidence": (
            PROGRAM_ROOT
            / "tasks"
            / "AP-003"
            / "evidence"
            / "live"
            / "ap003-ollama-llama3-002-repair"
        ),
        "verdict": "HOLD",
        "record_hash": None,
        "candidate_sha256": None,
        "repair_conversion": False,
    },
    {
        "label": "AP-003 repair #003 terminal fail",
        "evidence": (
            PROGRAM_ROOT
            / "tasks"
            / "AP-003"
            / "evidence"
            / "live"
            / "ap003-ollama-llama3-003-repair"
        ),
        "verdict": "VERIFIED_FAIL",
        "record_hash": (
            "21f30bf5ea6bcfdd4f84e3ae493f9aa"
            "3609d99ef2b8b6781059c6276f19cb9c6"
        ),
        "candidate_sha256": (
            "b43766dfe1f016a3b3a9c66c254649fc"
            "71b8591d8c2d3937b55ebef653fe25b9"
        ),
        "repair_conversion": False,
    },
]


def main() -> int:
    all_ok = True

    with tempfile.TemporaryDirectory(
        prefix="rarb-repair-replay-check-"
    ) as td:
        temp = Path(td)

        for index, case in enumerate(CASES, start=1):
            out = temp / f"repair-replay-{index}.json"

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
                print(f"{case['label']} REPLAY FAILED")
                continue

            report = json.loads(
                out.read_text(encoding="utf-8")
            )

            ok = (
                report["status"]
                == "SOURCE_EXACT_REPAIR_REPLAY_VERIFIED"
                and report["replay_mode"]
                == "source-exact-repair-detached-worktree-v1"
                and report["replayed_verdict"]
                == case["verdict"]
                and report["stored_record_hash"]
                == case["record_hash"]
                and report["replayed_record_hash"]
                == case["record_hash"]
                and report["candidate_sha256"]
                == case["candidate_sha256"]
                and report["replayed_repair_conversion"]
                is case["repair_conversion"]
                and report["replay_provider"] == "mock"
                and all(report["checks"].values())
            )

            print(
                f"{case['label']} SOURCE-EXACT REPLAY "
                + ("GREEN" if ok else "FAILED")
            )
            all_ok = all_ok and ok

    print(
        "PHASE 6C SOURCE-EXACT REPAIR REPLAY GREEN"
        if all_ok
        else "PHASE 6C SOURCE-EXACT REPAIR REPLAY FAILED"
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
