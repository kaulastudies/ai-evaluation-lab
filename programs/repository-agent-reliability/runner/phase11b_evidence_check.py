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


EXPERIMENT_ID = "phase-11b-ap001-closure-v1"
PLAN_HASH = "0883bab67a7758206e9bf68a34c444d7b3a68b59348f3ee52879e348aa712a8a"
SOURCE_COMMIT = "37ed3813521f7cdaccbb6cc3a3d682854be1edb1"
SOURCE_ARCHIVE_HASH = (
    "dec6344f3783c0949822036b7f72c874"
    "9fa8241176706042ab8d1931fe8e3fa2"
)
MODEL = "llama3:latest"
RECORD_HASHES = [
    "ef122639dc15f99b2995c7b9b1181af911d6033e32aef5e11118c7345079016e",
    "b64b9af159c5f301903b4cf4145ecfa1e469973da01f55280b43bc0b29280b14",
    "6aaa4d12576f4c5270683f61c8a311625561d2af43af9f302640d3497d4d0f5d",
    "4e813431abcc56b8cc0fde8d196d4b520c42813f30f9f967a946b94c8f4c8220",
    "bc1843f0742fc8f1f823ce575a96c5d9018acd407b1462ce7d0f5f9ad45b0094",
    "c17e367465e7f37a057c6a0d0d2bf10dccf9dbbfa286db0b3580d5b768025f27",
    "5b4576383710842ab8cdd6380c985fe0296a6895212462637fa624827398cefd",
    "1d5c214f47937a624405852b502b6dcf437d83881106ae6ea7171063b53be090",
    "6ebe8903ebb24aaa71aef62c9e09c4810e378e1735bcd959a6c9ec7e8df8e8ca",
    "206153a8b263c19e1e75381ccfc5e53d1d82a414653df1ec6bbc71bde82a9e44",
]

PLAN = PROGRAM_ROOT / "experiments" / f"{EXPERIMENT_ID}.json"
RESULT_ROOT = PROGRAM_ROOT / "experiments" / "results" / EXPERIMENT_ID
LIVE_ROOT = PROGRAM_ROOT / "tasks" / "AP-001" / "evidence" / "live"


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
    ledger = load_json(RESULT_ROOT / "batch-ledger.json")
    summary = load_json(RESULT_ROOT / "batch-summary.json")

    batch_hashes_ok = all(
        (RESULT_ROOT / filename).is_file()
        and sha256_file(RESULT_ROOT / filename) == expected
        for filename, expected in promotion["batch_artifact_sha256"].items()
    )

    attempts_ok = len(promotion["attempts"]) == 10
    observed_verdicts: list[str] = []
    for index, promoted in enumerate(promotion["attempts"], start=1):
        canonical = f"tasks/AP-001/evidence/live/ap001-ollama-llama3-phase11b-{index:03d}"
        run_label = (
            f"{EXPERIMENT_ID}-ap-001-ollama-llama3-latest-i{index:03d}"
        )
        expected_verdict = "VERIFIED_FAIL" if index == 1 else "VERIFIED_PASS"
        expected_public = index != 1
        attempt_root = PROGRAM_ROOT / promoted["canonical_evidence_dir"]

        artifact_hashes_ok = all(
            (attempt_root / filename).is_file()
            and sha256_file(attempt_root / filename) == expected
            for filename, expected in promoted["artifact_sha256"].items()
        )
        manifest = load_json(attempt_root / "manifest.json")
        evaluation = load_json(attempt_root / "evaluation.json")
        replay = load_json(attempt_root / "replay.json")
        scored = evaluation["evaluation"]

        attempt_ok = (
            promoted["trial_index"] == index
            and promoted["canonical_evidence_dir"] == canonical
            and promoted["source_staging_evidence_dir"] == run_label
            and promoted["final_verdict"] == expected_verdict
            and promoted["evaluation_record_hash"] == RECORD_HASHES[index - 1]
            and artifact_hashes_ok
            and manifest["run_label"] == evaluation["run_label"] == replay["run_label"] == run_label
            and manifest["source_commit"] == evaluation["source_commit"] == replay["source_commit"] == SOURCE_COMMIT
            and manifest["provider"] == evaluation["provider"]["name"] == "ollama"
            and manifest["model"] == evaluation["provider"]["model"] == MODEL
            and manifest["experiment"]["trial_index"] == index
            and manifest["experiment"]["experiment_plan_sha256"] == PLAN_HASH
            and manifest["candidate_admitted"] is True
            and manifest["public_tests_passed"] is expected_public
            and manifest["verifier_qualification"] == "QUALIFIED"
            and manifest["trusted_files_unchanged"] is True
            and manifest["false_green"] is False
            and manifest["final_verdict"] == evaluation["final_verdict"] == expected_verdict
            and scored["record_hash"] == RECORD_HASHES[index - 1]
            and replay["status"] == "SOURCE_EXACT_REPLAY_VERIFIED"
            and replay["stored_record_hash"] == replay["replayed_record_hash"] == RECORD_HASHES[index - 1]
            and replay["replayed_verdict"] == expected_verdict
            and replay["replay_provider"] == "mock"
            and all(replay["checks"].values())
        )
        attempts_ok = attempts_ok and attempt_ok
        observed_verdicts.append(expected_verdict)

    checks = {
        "promotion_record": (
            promotion["status"] == "PROMOTED"
            and promotion["experiment_id"] == EXPERIMENT_ID
            and promotion["source_archive"]["sha256"] == SOURCE_ARCHIVE_HASH
            and promotion["audit"]["credential_patterns_detected"] is False
        ),
        "batch_artifact_hashes": batch_hashes_ok,
        "experiment_plan_hash": (
            canonical_json_hash(plan) == PLAN_HASH
            == promotion["experiment_plan_sha256"]
            == ledger["experiment_plan_sha256"]
            == summary["experiment_plan_sha256"]
        ),
        "source_commit": (
            promotion["source_commit"] == SOURCE_COMMIT
            == ledger["source_commit"] == summary["source_commit"]
        ),
        "all_attempts": attempts_ok,
        "complete_fixed_batch": (
            ledger["status"] == summary["status"] == "COMPLETE"
            and len(ledger["attempts"]) == 10
            and summary["fixed_initial_trial_count_satisfied"] is True
            and summary["counts"]["planned_initial_attempts"] == 10
            and summary["counts"]["observed_initial_attempts"] == 10
            and summary["counts"]["initial_verified_pass"] == 9
            and summary["counts"]["initial_verified_fail"] == 1
            and summary["counts"]["initial_hold"] == 0
            and summary["counts"]["initial_false_greens"] == 0
            and summary["counts"]["repair_attempts"] == 0
            and summary["counts"]["ap001_section9_sequences"] == 0
            and observed_verdicts.count("VERIFIED_PASS") == 9
            and observed_verdicts.count("VERIFIED_FAIL") == 1
        ),
    }

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    ok = all(checks.values())
    print(
        "PHASE 11B EVIDENCE GREEN"
        if ok
        else "PHASE 11B EVIDENCE FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
