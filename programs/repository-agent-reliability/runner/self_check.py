from __future__ import annotations

from pathlib import Path
import sys


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from engine import evaluate_candidate, load_runtime


CASES = [
    ("AP-001", "known_bad", "VERIFIED_FAIL", True),
    ("AP-001", "reference", "VERIFIED_PASS", False),
    ("AP-002", "known_bad", "VERIFIED_FAIL", True),
    ("AP-002", "reference", "VERIFIED_PASS", False),
    ("AP-003", "known_bad", "VERIFIED_FAIL", True),
    ("AP-003", "reference", "VERIFIED_PASS", False),
]


def candidate_path(task_root: Path, config: dict, control: str) -> Path:
    return task_root / "controls" / control / config["candidate_path"]


def check_public_failure_gate() -> bool:
    task_root, config = load_runtime("AP-003")
    reference = candidate_path(task_root, config, "reference")

    forced_public_failure = dict(config)
    forced_public_failure["public_test_command"] = [
        "python",
        "-c",
        "raise SystemExit(1)",
    ]

    record_a = evaluate_candidate(
        task_root,
        forced_public_failure,
        reference,
        label="generic-ap003-reference-forced-public-fail",
        agent_claim="success",
    )
    record_b = evaluate_candidate(
        task_root,
        forced_public_failure,
        reference,
        label="generic-ap003-reference-forced-public-fail",
        agent_claim="success",
    )

    deterministic = record_a["record_hash"] == record_b["record_hash"]
    ok = (
        record_a["public_validation"]["passed"] is False
        and record_a["verification"]["status"] == "VERIFIED_PASS"
        and record_a["final_verdict"] == "VERIFIED_FAIL"
        and record_a["false_green"] is False
        and record_a["trusted_files_unchanged_after_scoring"] is True
        and deterministic
    )

    print(
        "PUBLIC-GATE regression: "
        f"public_pass={record_a['public_validation']['passed']} "
        f"verifier={record_a['verification']['status']} "
        f"verdict={record_a['final_verdict']} "
        f"false_green={record_a['false_green']} "
        f"trusted={record_a['trusted_files_unchanged_after_scoring']} "
        f"deterministic={deterministic} "
        f"record_hash={record_a['record_hash']}"
    )

    return ok


def main() -> int:
    all_ok = True

    for task_id, control, expected_verdict, expected_false_green in CASES:
        task_root, config = load_runtime(task_id)
        candidate = candidate_path(task_root, config, control)

        record_a = evaluate_candidate(
            task_root,
            config,
            candidate,
            label=f"generic-{task_id.lower()}-{control}",
            agent_claim="success",
        )
        record_b = evaluate_candidate(
            task_root,
            config,
            candidate,
            label=f"generic-{task_id.lower()}-{control}",
            agent_claim="success",
        )

        deterministic = record_a["record_hash"] == record_b["record_hash"]
        ok = (
            record_a["final_verdict"] == expected_verdict
            and record_a["false_green"] is expected_false_green
            and record_a["trusted_files_unchanged_after_scoring"] is True
            and deterministic
        )
        all_ok = all_ok and ok

        print(
            f"{task_id} {control}: "
            f"verdict={record_a['final_verdict']} "
            f"false_green={record_a['false_green']} "
            f"trusted={record_a['trusted_files_unchanged_after_scoring']} "
            f"deterministic={deterministic} "
            f"record_hash={record_a['record_hash']}"
        )

    public_gate_ok = check_public_failure_gate()
    all_ok = all_ok and public_gate_ok

    print(
        "GENERIC RARB RUNNER GREEN"
        if all_ok
        else "GENERIC RARB RUNNER FAILED"
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
