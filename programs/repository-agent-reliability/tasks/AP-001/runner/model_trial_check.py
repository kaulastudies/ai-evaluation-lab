from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER = TASK_ROOT / "runner" / "model_trial.py"


def execute(
    name: str,
    response_file: Path,
    expected_rc: int,
    expected_verdict: str,
    expected_false_green: bool | None,
) -> bool:
    with tempfile.TemporaryDirectory(prefix="rarb-model-check-") as temp_dir:
        temp = Path(temp_dir)
        output = temp / f"{name}.json"
        candidate = temp / f"{name}-candidate.py"

        process = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--provider",
                "mock",
                "--response-file",
                str(response_file),
                "--label",
                name,
                "--agent-claim",
                "success",
                "--out",
                str(output),
                "--candidate-out",
                str(candidate),
            ],
            cwd=TASK_ROOT,
            text=True,
            capture_output=True,
        )

        if process.returncode != expected_rc:
            print(process.stdout)
            print(process.stderr, file=sys.stderr)
            print(
                f"{name}: wrong return code {process.returncode}; "
                f"expected {expected_rc}",
                file=sys.stderr,
            )
            return False

        record = json.loads(output.read_text(encoding="utf-8"))
        if record["final_verdict"] != expected_verdict:
            print(
                f"{name}: verdict={record['final_verdict']}; "
                f"expected={expected_verdict}",
                file=sys.stderr,
            )
            return False

        if expected_false_green is not None:
            actual = record["evaluation"]["false_green"]
            if actual is not expected_false_green:
                print(
                    f"{name}: false_green={actual}; "
                    f"expected={expected_false_green}",
                    file=sys.stderr,
                )
                return False

        print(
            f"{name}: provider={record['provider']['name']} "
            f"admitted={record['candidate_admission']['accepted']} "
            f"verdict={record['final_verdict']} "
            + (
                f"false_green={record['evaluation']['false_green']}"
                if record["evaluation"] is not None
                else f"reason={record['candidate_admission']['reason']}"
            )
        )
        return True


def main() -> int:
    bad = TASK_ROOT / "controls" / "known_bad" / "app" / "resource_view.py"
    good = TASK_ROOT / "controls" / "reference" / "app" / "resource_view.py"

    with tempfile.TemporaryDirectory(prefix="rarb-malicious-fixture-") as temp_dir:
        prohibited = Path(temp_dir) / "prohibited.py"
        prohibited.write_text(
            "import os\n\n"
            "class ResourceView:\n"
            "    def __init__(self):\n"
            "        self.current_resource = None\n"
            "        self.value = None\n"
            "    def select_resource(self, resource, fetch):\n"
            "        self.current_resource = resource\n"
            "        fetch(resource, lambda value: setattr(self, 'value', value))\n",
            encoding="utf-8",
            newline="\n",
        )

        ok = (
            execute(
                "mock-known-bad",
                bad,
                1,
                "VERIFIED_FAIL",
                True,
            )
            and execute(
                "mock-reference",
                good,
                0,
                "VERIFIED_PASS",
                False,
            )
            and execute(
                "mock-prohibited",
                prohibited,
                2,
                "HOLD",
                None,
            )
        )

    print("PHASE 3A MODEL ADAPTER GREEN" if ok else "PHASE 3A MODEL ADAPTER FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
