from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER = TASK_ROOT / "runner" / "model_trial.py"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    response_file = TASK_ROOT / "controls" / "reference" / "app" / "resource_view.py"

    with tempfile.TemporaryDirectory(prefix="rarb-response-capture-") as td:
        temp = Path(td)
        output = temp / "result.json"
        raw = temp / "response.raw"
        candidate = temp / "candidate.py"

        process = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--provider",
                "mock",
                "--response-file",
                str(response_file),
                "--response-out",
                str(raw),
                "--label",
                "response-capture-check",
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

        if process.returncode != 0:
            print(process.stdout)
            print(process.stderr, file=sys.stderr)
            return 1

        record = json.loads(output.read_text(encoding="utf-8"))
        artifact = record["model_response_artifact"]

        ok = (
            raw.is_file()
            and artifact is not None
            and artifact["sha256"] == record["model_response_sha256"]
            and sha256_file(raw) == record["model_response_sha256"]
            and record["final_verdict"] == "VERIFIED_PASS"
        )

        print(
            f"response_capture={ok} "
            f"sha256={record['model_response_sha256']} "
            f"bytes={artifact['bytes'] if artifact else None} "
            f"verdict={record['final_verdict']}"
        )

        print("PHASE 3B EVIDENCE CAPTURE GREEN" if ok else "PHASE 3B EVIDENCE CAPTURE FAILED")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
