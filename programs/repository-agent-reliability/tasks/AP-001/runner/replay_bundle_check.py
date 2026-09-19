from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER_DIR = Path(__file__).resolve().parent
EXPORTER = RUNNER_DIR / "export_replay_bundle.py"


def export_and_replay(
    name: str,
    candidate: Path,
    expected_verdict: str,
) -> bool:
    with tempfile.TemporaryDirectory(prefix="rarb-replay-check-") as temp_dir:
        temp = Path(temp_dir)
        bundle_zip = temp / f"{name}.zip"

        export = subprocess.run(
            [
                sys.executable,
                str(EXPORTER),
                "--candidate-file",
                str(candidate),
                "--label",
                name,
                "--agent-claim",
                "success",
                "--output",
                str(bundle_zip),
            ],
            cwd=TASK_ROOT,
            text=True,
            capture_output=True,
        )

        if export.returncode != 0:
            print(export.stdout)
            print(export.stderr, file=sys.stderr)
            return False

        export_record = json.loads(export.stdout)
        if export_record["final_verdict"] != expected_verdict:
            print(
                f"{name}: unexpected exported verdict "
                f"{export_record['final_verdict']}"
            )
            return False

        extract_dir = temp / "extracted"
        with zipfile.ZipFile(bundle_zip) as archive:
            archive.extractall(extract_dir)

        replay = subprocess.run(
            [sys.executable, str(extract_dir / "replay.py")],
            cwd=extract_dir,
            text=True,
            capture_output=True,
        )

        print(
            f"{name}: export_verdict={export_record['final_verdict']} "
            f"bundle_sha256={export_record['bundle_sha256']}"
        )
        print(replay.stdout.strip())

        if replay.returncode != 0:
            print(replay.stderr, file=sys.stderr)
            return False

        return "REPLAY VERIFIED" in replay.stdout


def main() -> int:
    bad = TASK_ROOT / "controls" / "known_bad" / "app" / "resource_view.py"
    good = TASK_ROOT / "controls" / "reference" / "app" / "resource_view.py"

    ok_bad = export_and_replay(
        "known-bad-replay",
        bad,
        "VERIFIED_FAIL",
    )
    ok_good = export_and_replay(
        "reference-replay",
        good,
        "VERIFIED_PASS",
    )

    ok = ok_bad and ok_good
    print("PHASE 2C REPLAY GREEN" if ok else "PHASE 2C REPLAY FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
