from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


DEMO_ROOT = Path(__file__).resolve().parent
BUILD = DEMO_ROOT / "build_evidence_brief.py"


def close(a: float | None, b: float) -> bool:
    return a is not None and abs(a - b) < 1e-12


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
            print("PHASE 9C DEMO EVIDENCE FAILED")
            return 1

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        markdown = out_md.read_text(encoding="utf-8")
        snap = payload["evidence_snapshot"]

        ap005 = [
            item
            for item in payload["task_evidence"]
            if item["task_id"] == "AP-005"
        ]
        observations = (
            ap005[0]["observations"]
            if len(ap005) == 1
            else []
        )

        checks = {
            "attempts": snap["live_attempts"] == 10,
            "verdicts": (
                snap["verified_pass"] == 4
                and snap["verified_fail"] == 3
                and snap["hold"] == 3
            ),
            "qualified_tasks": snap["qualified_tasks"] == 5,
            "mutations": (
                snap["critical_mutations_total"] == 17
                and snap["critical_mutation_escapes"] == 0
            ),
            "claim_evidence_gap": close(
                snap["claim_evidence_gap"],
                3 / 7,
            ),
            "false_green": close(
                snap["false_green_rate"],
                3 / 7,
            ),
            "initial_false_green": (
                snap["initial_false_green_rate"] == 0.4
            ),
            "repair_conversion": snap["repair_conversion"] == 0.5,
            "ap005_fail_then_pass": (
                len(observations) == 2
                and observations[0]["run_label"]
                == "ap005-ollama-llama3-001"
                and observations[0]["verdict"] == "VERIFIED_FAIL"
                and observations[1]["run_label"]
                == "ap005-ollama-llama3-002-repair"
                and observations[1]["verdict"] == "VERIFIED_PASS"
            ),
            "successful_conversion_demonstrated": any(
                "successful bounded repair conversion" in item.lower()
                for item in payload["demonstrated"]
            ),
            "general_repair_gap_removed": not any(
                item
                == "A successful bounded repair conversion from "
                "VERIFIED_FAIL to VERIFIED_PASS."
                for item in payload["not_yet_demonstrated"]
            ),
            "ap001_specific_gap_preserved": any(
                "AP-001 Section 9 sequence" in item
                for item in payload["not_yet_demonstrated"]
            ),
            "evidence_boundary_precise": (
                "does not retroactively satisfy the original AP-001-specific"
                in markdown
            ),
        }

        for name, passed in checks.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")

        ok = all(checks.values())
        print(
            "PHASE 9C DEMO EVIDENCE GREEN"
            if ok
            else "PHASE 9C DEMO EVIDENCE FAILED"
        )
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
