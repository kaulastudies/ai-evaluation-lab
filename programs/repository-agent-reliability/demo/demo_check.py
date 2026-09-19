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
            print("PHASE 8B DEMO EVIDENCE FAILED")
            return 1

        payload = json.loads(
            out_json.read_text(encoding="utf-8")
        )
        markdown = out_md.read_text(encoding="utf-8")

        snap = payload["evidence_snapshot"]

        ap004 = [
            item
            for item in payload["task_evidence"]
            if item["task_id"] == "AP-004"
        ]

        checks = {
            "attempts": snap["live_attempts"] == 7,
            "verdicts": (
                snap["verified_pass"] == 2
                and snap["verified_fail"] == 2
                and snap["hold"] == 3
            ),
            "qualified_tasks": snap["qualified_tasks"] == 4,
            "mutations": (
                snap["critical_mutations_total"] == 13
                and snap["critical_mutation_escapes"] == 0
            ),
            "false_green": snap["false_green_rate"] == 0.5,
            "repair_conversion": snap["repair_conversion"] == 0.0,
            "honest_gap": any(
                "A successful bounded repair conversion" in item
                for item in payload["not_yet_demonstrated"]
            ),
            "ap004_hold": (
                len(ap004) == 1
                and len(ap004[0]["observations"]) == 1
                and ap004[0]["observations"][0]["run_label"]
                == "ap004-ollama-llama3-001"
                and ap004[0]["observations"][0]["verdict"] == "HOLD"
                and "unterminated fenced code block"
                in ap004[0]["observations"][0]["note"]
            ),
            "ap004_gap_is_precise": any(
                "AP-004 candidate outcome beyond admission HOLD" in item
                for item in payload["not_yet_demonstrated"]
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
            "PHASE 8B DEMO EVIDENCE GREEN"
            if ok
            else "PHASE 8B DEMO EVIDENCE FAILED"
        )
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
