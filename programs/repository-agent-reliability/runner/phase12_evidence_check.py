from __future__ import annotations

from collections import Counter
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


EXPERIMENT_ID = "phase-12-cross-model-replication-v1"
PLAN_HASH = "97ab476246d131c672f00c75fb1aabb391f2c31b98c9e6af47f139834637eeba"
SOURCE_COMMIT = "257cb7a3510a05e124e279a32357befa51b2f7f4"
ARCHIVE_SHA256 = "a0344076f2ad5efedf48e602ef27049e3d1892a74b746d77163b74c3163c8a7d"
ARCHIVE_BYTES = 224074
ARCHIVE_FILES = 213
FAIL_RUN = (
    "phase-12-cross-model-replication-v1-ap-001-"
    "ollama-llama3-latest-i001"
)
FAIL_GATES = ["AP001-G03", "AP001-G01", "AP001-G02"]

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
    plan = load_json(PLAN)
    promotion = load_json(RESULT_ROOT / "promotion.json")
    ledger = load_json(RESULT_ROOT / "batch-ledger.json")
    summary = load_json(RESULT_ROOT / "batch-summary.json")

    artifact_hashes_ok = all(
        (RESULT_ROOT / name).is_file()
        and sha256_file(RESULT_ROOT / name) == expected
        for name, expected in promotion["batch_artifact_sha256"].items()
    )

    attempt_checks: list[bool] = []
    run_labels: list[str] = []
    configuration_counts: Counter[str] = Counter()
    verdicts: Counter[str] = Counter()
    replay_statuses: Counter[str] = Counter()
    failure_preserved = False

    for item in promotion["attempts"]:
        evidence = PROGRAM_ROOT / item["canonical_evidence_dir"]
        manifest = load_json(evidence / "manifest.json")
        record = load_json(evidence / "evaluation.json")
        replay = load_json(evidence / "replay.json")
        scored = record["evaluation"]

        files_ok = all(
            (evidence / name).is_file()
            and sha256_file(evidence / name) == expected
            for name, expected in item["artifact_sha256"].items()
        )
        run = item["run_label"]
        config_id = manifest["experiment"]["configuration_id"]
        run_labels.append(run)
        configuration_counts[config_id] += 1
        verdicts[record["final_verdict"]] += 1
        replay_statuses[replay["status"]] += 1

        failed_gates = [
            gate["id"]
            for gate in scored["verification"]["gates"]
            if gate["passed"] is False
        ]

        if run == FAIL_RUN:
            failure_preserved = (
                record["candidate_admission"]["accepted"] is True
                and scored["agent_claimed_success"] is True
                and scored["public_validation"]["passed"] is False
                and scored["public_validation"]["returncode"] == 1
                and record["final_verdict"] == "VERIFIED_FAIL"
                and scored["false_green"] is False
                and failed_gates == FAIL_GATES
                and replay["status"] == "SOURCE_EXACT_REPLAY_VERIFIED"
            )

        attempt_checks.append(
            files_ok
            and manifest["run_label"] == run == record["run_label"] == replay["run_label"]
            and manifest["source_commit"] == SOURCE_COMMIT
            and record["source_commit"] == SOURCE_COMMIT
            and replay["source_commit"] == SOURCE_COMMIT
            and manifest["experiment"]["experiment_id"] == EXPERIMENT_ID
            and manifest["experiment"]["experiment_plan_sha256"] == PLAN_HASH
            and manifest["verifier_qualification"] == "QUALIFIED"
            and manifest["trusted_files_unchanged"] is True
            and scored["trusted_files_unchanged_after_scoring"] is True
            and scored["record_hash"] == item["evaluation_record_hash"]
            and replay["stored_record_hash"] == item["evaluation_record_hash"]
            and replay["replayed_record_hash"] == item["evaluation_record_hash"]
            and replay["replayed_verdict"] == record["final_verdict"]
            and replay["replay_provider"] == "mock"
            and all(replay["checks"].values())
            and replay["status"] == "SOURCE_EXACT_REPLAY_VERIFIED"
            and replay["replay_report_sha256"] == item["replay_report_hash"]
        )

    counts = summary["counts"]
    config_summary = {
        item["configuration_id"]: item for item in summary["configuration_summaries"]
    }

    checks = {
        "promotion_record": (
            promotion["status"] == "PROMOTED"
            and promotion["experiment_id"] == EXPERIMENT_ID
        ),
        "archive_identity": (
            promotion["source_archive"]["sha256"] == ARCHIVE_SHA256
            and promotion["source_archive"]["bytes"] == ARCHIVE_BYTES
            and promotion["source_archive"]["files"] == ARCHIVE_FILES
        ),
        "plan_hash": (
            canonical_json_hash(plan) == PLAN_HASH
            == promotion["experiment_plan_sha256"]
            == ledger["experiment_plan_sha256"]
            == summary["experiment_plan_sha256"]
        ),
        "source_commit": (
            promotion["source_commit"] == SOURCE_COMMIT
            == ledger["source_commit"]
            == summary["source_commit"]
        ),
        "batch_artifact_hashes": artifact_hashes_ok,
        "thirty_exact_attempts": (
            len(promotion["attempts"]) == 30
            and len(run_labels) == len(set(run_labels)) == 30
            and all(attempt_checks)
        ),
        "configuration_matrix": (
            configuration_counts
            == Counter({
                "ollama-llama3-latest": 10,
                "ollama-qwen2-5-coder-7b": 10,
                "nebius-nemotron-3-super-120b-a12b": 10,
            })
        ),
        "batch_outcomes": (
            counts["planned_initial_attempts"] == 30
            and counts["observed_initial_attempts"] == 30
            and counts["initial_verified_pass"] == 29
            and counts["initial_verified_fail"] == 1
            and counts["initial_hold"] == 0
            and counts["initial_false_greens"] == 0
            and counts["repair_attempts"] == 0
            and counts["ap001_section9_sequences"] == 0
            and verdicts == Counter({"VERIFIED_PASS": 29, "VERIFIED_FAIL": 1})
        ),
        "configuration_outcomes": (
            config_summary["ollama-llama3-latest"]["counts"]["initial_verified_pass"] == 9
            and config_summary["ollama-llama3-latest"]["counts"]["initial_verified_fail"] == 1
            and config_summary["ollama-qwen2-5-coder-7b"]["counts"]["initial_verified_pass"] == 10
            and config_summary["nebius-nemotron-3-super-120b-a12b"]["counts"]["initial_verified_pass"] == 10
        ),
        "all_source_exact_replays": (
            replay_statuses == Counter({"SOURCE_EXACT_REPLAY_VERIFIED": 30})
        ),
        "single_failure_preserved": failure_preserved,
        "section9_remains_open": counts["ap001_section9_sequences"] == 0,
        "claim_boundary": (
            any("one-task" in item.lower() or "one task" in item.lower()
                for item in promotion["claim_boundary"])
            and any("three" in item.lower() and "configuration" in item.lower()
                for item in promotion["claim_boundary"])
            and any("general coding-agent" in item.lower()
                for item in promotion["claim_boundary"])
        ),
    }

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    ok = all(checks.values())
    print(
        "PHASE 12 EVIDENCE INTEGRITY GREEN"
        if ok
        else "PHASE 12 EVIDENCE INTEGRITY FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
