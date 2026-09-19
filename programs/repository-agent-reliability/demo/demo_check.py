from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


DEMO_ROOT = Path(__file__).resolve().parent
BUILD = DEMO_ROOT / "build_evidence_brief.py"


def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="rarb-demo-evidence-"
    ) as td:
        temp = Path(td)
        out_json = temp / "brief.json"
        out_md = temp / "brief.md"

        process = subprocess.run(
            [
                sys.executable,
                str(BUILD),
                "--out-json",
                str(out_json),
                "--out-md",
                str(out_md),
            ],
            cwd=DEMO_ROOT.parent,
            text=True,
            capture_output=True,
        )

        if process.stdout:
            print(process.stdout.strip())
        if process.stderr:
            print(process.stderr, file=sys.stderr)

        if process.returncode != 0:
            print("PHASE 9B DEMO EVIDENCE FAILED")
            return 1

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        markdown = out_md.read_text(encoding="utf-8")
        snap = payload["evidence_snapshot"]

        ap005 = [
            item
            for item in payload["task_evidence"]
            if item["task_id"] == "AP-005"
        ]
        ap005_observations = (
            ap005[0]["observations"]
            if len(ap005) == 1
            else []
        )

        checks = {
            "attempts": snap["live_attempts"] == 9,
            "verdicts": (
                snap["verified_pass"] == 3
                and snap["verified_fail"] == 3
                and snap["hold"] == 3
            ),
            "qualified_tasks": snap["qualified_tasks"] == 5,
            "mutations": (
                snap["critical_mutations_total"] == 17
                and snap["critical_mutation_escapes"] == 0
            ),
            "claim_evidence_gap": (
                snap["claim_evidence_gap"] == 0.5
            ),
            "false_green": snap["false_green_rate"] == 0.5,
            "initial_false_green": (
                snap["initial_false_green_rate"] == 0.4
            ),
            "repair_conversion": snap["repair_conversion"] == 0.0,
            "ap005_live_false_green": (
                len(ap005_observations) == 1
                and ap005_observations[0]["run_label"]
                == "ap005-ollama-llama3-001"
                and ap005_observations[0]["verdict"]
                == "VERIFIED_FAIL"
                and "false-green" in ap005_observations[0]["note"]
            ),
            "ap005_live_gap_removed": not any(
                item == "AP-005 live task evidence."
                for item in payload["not_yet_demonstrated"]
            ),
            "repair_gap_preserved": any(
                "A successful bounded repair conversion" in item
                for item in payload["not_yet_demonstrated"]
            ),
            "all_five_live_claim": (
                "Live initial model evidence across AP-001 through AP-005."
                in payload["demonstrated"]
            ),
            "ap003_story": (
                "RARB measures whether a patch deserves to ship"
                in markdown
                and "repair budget was exhausted"
                in markdown
            ),
        }

        for name, passed in checks.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")

        ok = all(checks.values())
        print(
            "PHASE 9B DEMO EVIDENCE GREEN"
            if ok
            else "PHASE 9B DEMO EVIDENCE FAILED"
        )
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
