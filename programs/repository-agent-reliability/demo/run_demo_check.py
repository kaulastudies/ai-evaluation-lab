from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


DEMO_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = DEMO_ROOT.parent
RUN_DEMO = DEMO_ROOT / "run_demo.py"


def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="rarb-phase7c-check-"
    ) as td:
        temp = Path(td)
        out_json = temp / "status.json"
        out_md = temp / "status.md"

        process = subprocess.run(
            [
                sys.executable,
                str(RUN_DEMO),
                "--out-json",
                str(out_json),
                "--out-md",
                str(out_md),
            ],
            cwd=PROGRAM_ROOT.parents[1],
            text=True,
            capture_output=True,
        )

        if process.stdout:
            print(process.stdout.strip())
        if process.stderr:
            print(process.stderr, file=sys.stderr)

        if process.returncode != 0:
            print("PHASE 7C ENTRYPOINT CHECK FAILED")
            return 1

        status = json.loads(
            out_json.read_text(encoding="utf-8")
        )
        markdown = out_md.read_text(encoding="utf-8")

        checks = {
            "overall_green": status["status"] == "GREEN",
            "all_checks_pass": all(
                item["passed"]
                for item in status["checks"].values()
            ),
            "fresh_artifacts": (
                status[
                    "generated_artifacts_match_head_evidence"
                ]
                is True
            ),
            "attempts": (
                status["evidence_snapshot"]["attempts_total"] == 8
            ),
            "verdicts": (
                status["evidence_snapshot"]["verified_pass"] == 3
                and status["evidence_snapshot"]["verified_fail"] == 2
                and status["evidence_snapshot"]["hold"] == 3
            ),
            "qualification": (
                status["evidence_snapshot"]["qualified_tasks"] == 5
                and status["evidence_snapshot"][
                    "critical_mutation_escapes"
                ] == 0
                and status["evidence_snapshot"][
                    "critical_mutations_total"
                ] == 17
            ),
            "claim_gap": (
                status["evidence_snapshot"]["claim_evidence_gap"] == 0.4
            ),
            "false_green": (
                status["evidence_snapshot"]["false_green_rate"] == 0.4
            ),
            "honest_repair_gap": any(
                "successful bounded repair conversion" in item
                for item in status["evidence_boundary"]
            ),
            "ap005_live_gap": any(
                item == "AP-005 live task evidence."
                for item in status["evidence_boundary"]
            ),
            "human_summary": (
                "# RARB Demo Status" in markdown
                and "**Overall: GREEN**" in markdown
            ),
        }

        for name, passed in checks.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")

        ok = all(checks.values())
        print(
            "PHASE 7C ENTRYPOINT CHECK GREEN"
            if ok
            else "PHASE 7C ENTRYPOINT CHECK FAILED"
        )
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
