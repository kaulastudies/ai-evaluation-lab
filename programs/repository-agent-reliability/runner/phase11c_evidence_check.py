from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from engine import canonical_json_hash


EXPERIMENT_ID = "phase-11c-nebius-nemotron-pilot-v1"
RUN_LABEL = (
    "phase-11c-nebius-nemotron-pilot-v1-ap-001-"
    "nebius-nemotron-3-super-120b-a12b-i001"
)
SOURCE_COMMIT = "348b3aedf8ce1296645d97db8f4fe31d47878bdd"
MODEL = "nvidia/nemotron-3-super-120b-a12b"
RECORD_HASH = (
    "0302eea657a02410f6067db5913054526"
    "41653257d511d2a79452218e572eab3"
)

PLAN = PROGRAM_ROOT / "experiments" / f"{EXPERIMENT_ID}.json"
RESULT_ROOT = PROGRAM_ROOT / "experiments" / "results" / EXPERIMENT_ID
ATTEMPT_ROOT = (
    PROGRAM_ROOT
    / "tasks"
    / "AP-001"
    / "evidence"
    / "live"
    / "ap001-nebius-nemotron-001"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    promotion = load_json(RESULT_ROOT / "promotion.json")
    plan = load_json(PLAN)
    manifest = load_json(ATTEMPT_ROOT / "manifest.json")
    evaluation = load_json(ATTEMPT_ROOT / "evaluation.json")
    replay = load_json(ATTEMPT_ROOT / "replay.json")
    ledger = load_json(RESULT_ROOT / "batch-ledger.json")
    summary = load_json(RESULT_ROOT / "batch-summary.json")

    artifact_hashes_ok = True
    for filename, expected in promotion["artifact_sha256"].items():
        root = RESULT_ROOT if filename.startswith("batch-") else ATTEMPT_ROOT
        path = root / filename
        artifact_hashes_ok = (
            artifact_hashes_ok
            and path.is_file()
            and sha256_file(path) == expected
        )

    plan_hash = canonical_json_hash(plan)
    observed = evaluation["provider"]
    scored = evaluation["evaluation"]

    checks = {
        "promotion_record": (
            promotion["status"] == "PROMOTED"
            and promotion["experiment_id"] == EXPERIMENT_ID
        ),
        "artifact_hashes": artifact_hashes_ok,
        "experiment_plan_hash": (
            plan_hash == promotion["experiment_plan_sha256"]
            == manifest["experiment"]["experiment_plan_sha256"]
            == ledger["experiment_plan_sha256"]
            == summary["experiment_plan_sha256"]
        ),
        "source_commit": (
            promotion["source_commit"] == SOURCE_COMMIT
            == manifest["source_commit"]
            == evaluation["source_commit"]
            == replay["source_commit"]
            == ledger["source_commit"]
            == summary["source_commit"]
        ),
        "run_identity": (
            manifest["run_label"] == RUN_LABEL
            == evaluation["run_label"]
            == replay["run_label"]
            and manifest["task_id"] == evaluation["task_id"] == "AP-001"
        ),
        "provider_model": (
            manifest["provider"] == observed["name"] == "nebius"
            and manifest["model"] == observed["model"] == MODEL
        ),
        "qualified_verified_pass": (
            manifest["final_verdict"] == evaluation["final_verdict"]
            == "VERIFIED_PASS"
            and manifest["public_tests_passed"] is True
            and manifest["verifier_qualification"] == "QUALIFIED"
            and manifest["trusted_files_unchanged"] is True
            and manifest["false_green"] is False
            and scored["record_hash"] == RECORD_HASH
        ),
        "source_exact_replay": (
            replay["status"] == "SOURCE_EXACT_REPLAY_VERIFIED"
            and replay["stored_record_hash"] == RECORD_HASH
            == replay["replayed_record_hash"]
            and replay["replayed_verdict"] == "VERIFIED_PASS"
            and replay["replay_provider"] == "mock"
            and all(replay["checks"].values())
        ),
        "complete_fixed_batch": (
            ledger["status"] == summary["status"] == "COMPLETE"
            and len(ledger["attempts"]) == 1
            and summary["fixed_initial_trial_count_satisfied"] is True
            and summary["counts"]["planned_initial_attempts"] == 1
            and summary["counts"]["observed_initial_attempts"] == 1
            and summary["counts"]["initial_verified_pass"] == 1
            and summary["counts"]["repair_attempts"] == 0
            and summary["counts"]["ap001_section9_sequences"] == 0
        ),
    }

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    ok = all(checks.values())
    print(
        "PHASE 11C NEBIUS EVIDENCE GREEN"
        if ok
        else "PHASE 11C NEBIUS EVIDENCE FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
