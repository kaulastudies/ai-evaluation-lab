from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPO_ROOT = PROGRAM_ROOT.parents[1]
EXPERIMENT_ID = "phase-12-cross-model-replication-v1"
PLAN = PROGRAM_ROOT / "experiments" / f"{EXPERIMENT_ID}.json"
RESULT_ROOT = PROGRAM_ROOT / "experiments" / "results" / EXPERIMENT_ID
LIVE_ROOT = PROGRAM_ROOT / "tasks" / "AP-001" / "evidence" / "live"

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from batch import load_plan, model_environment, planned_initials
from batch_report import summarize
from engine import canonical_json_hash


EXPECTED_CONFIGURATIONS = [
    (
        "ollama-llama3-latest",
        "ollama",
        "llama3:latest",
        "OLLAMA_MODEL",
    ),
    (
        "ollama-qwen2-5-coder-7b",
        "ollama",
        "qwen2.5-coder:7b",
        "OLLAMA_MODEL",
    ),
    (
        "nebius-nemotron-3-super-120b-a12b",
        "nebius",
        "nvidia/nemotron-3-super-120b-a12b",
        "NEBIUS_MODEL",
    ),
]


def synthetic_record(
    *,
    run_label: str,
    provider: str,
    model: str,
    verdict: str,
    public_passed: bool | None,
    false_green: bool | None,
    record_hash: str | None,
    parent: str | None = None,
    repair_conversion: bool | None = None,
) -> dict[str, Any]:
    evaluation = None
    if public_passed is not None:
        evaluation = {
            "public_validation": {"passed": public_passed},
            "false_green": false_green,
            "record_hash": record_hash,
        }
    record: dict[str, Any] = {
        "run_label": run_label,
        "source_commit": "synthetic-source",
        "provider": {
            "name": provider,
            "model": model,
            "latency_ms": 100,
            "input_tokens": 10,
            "output_tokens": 5,
            "estimated_cost_usd": 0.0 if provider == "ollama" else None,
        },
        "evaluation": evaluation,
        "final_verdict": verdict,
    }
    if parent is not None:
        record["parent"] = {"run_label": parent}
        record["repair_conversion"] = repair_conversion
    return record


def write_observation(
    root: Path,
    *,
    directory: str,
    record: dict[str, Any],
    config: dict[str, Any],
    plan_hash: str,
    attempt_kind: str,
) -> dict[str, Any]:
    evidence = root / directory
    evidence.mkdir()
    experiment = {
        "experiment_id": EXPERIMENT_ID,
        "experiment_plan_sha256": plan_hash,
        "configuration_id": config["configuration_id"],
        "trial_index": 1,
    }
    if attempt_kind == "repair":
        experiment["repair_index"] = 1
    evaluation = record.get("evaluation")
    manifest = {
        "source_commit": record["source_commit"],
        "run_label": record["run_label"],
        "provider": config["provider"],
        "model": config["expected_model"],
        "experiment": experiment,
        "evaluation_record_hash": (
            None if evaluation is None else evaluation["record_hash"]
        ),
    }
    (evidence / "evaluation.json").write_text(
        json.dumps(record, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    item = {
        "run_label": record["run_label"],
        "attempt_kind": attempt_kind,
        "evidence_dir": directory,
    }
    if attempt_kind == "repair":
        item["parent_run_label"] = record["parent"]["run_label"]
    return item


def synthetic_report_check(plan: dict[str, Any]) -> bool:
    report_plan = copy.deepcopy(plan)
    report_plan["tasks"][0]["initial_trials"] = 1
    plan_hash = canonical_json_hash(report_plan)
    configs = report_plan["configurations"]

    with tempfile.TemporaryDirectory(prefix="rarb-phase12a-report-") as td:
        root = Path(td)
        items: list[dict[str, Any]] = []
        records = [
            synthetic_record(
                run_label="phase12a-synthetic-llama3",
                provider="ollama",
                model="llama3:latest",
                verdict="VERIFIED_PASS",
                public_passed=True,
                false_green=False,
                record_hash="a" * 64,
            ),
            synthetic_record(
                run_label="phase12a-synthetic-qwen",
                provider="ollama",
                model="qwen2.5-coder:7b",
                verdict="HOLD",
                public_passed=None,
                false_green=None,
                record_hash=None,
            ),
            synthetic_record(
                run_label="phase12a-synthetic-nemotron",
                provider="nebius",
                model="nvidia/nemotron-3-super-120b-a12b",
                verdict="VERIFIED_FAIL",
                public_passed=True,
                false_green=True,
                record_hash="b" * 64,
            ),
        ]
        for index, (config, record) in enumerate(
            zip(configs, records, strict=True),
            start=1,
        ):
            items.append(
                write_observation(
                    root,
                    directory=f"initial-{index}",
                    record=record,
                    config=config,
                    plan_hash=plan_hash,
                    attempt_kind="initial",
                )
            )

        repair = synthetic_record(
            run_label="phase12a-synthetic-nemotron-repair-01",
            provider="nebius",
            model="nvidia/nemotron-3-super-120b-a12b",
            verdict="VERIFIED_PASS",
            public_passed=True,
            false_green=False,
            record_hash="c" * 64,
            parent=records[2]["run_label"],
            repair_conversion=True,
        )
        items.append(
            write_observation(
                root,
                directory="repair-1",
                record=repair,
                config=configs[2],
                plan_hash=plan_hash,
                attempt_kind="repair",
            )
        )
        ledger = {
            "schema_version": "1.0.0",
            "experiment_id": EXPERIMENT_ID,
            "experiment_plan_sha256": plan_hash,
            "source_commit": "synthetic-source",
            "status": "COMPLETE",
            "attempts": items,
        }
        report = summarize(report_plan, ledger, root)

    summaries = report["configuration_summaries"]
    return (
        len(summaries) == 3
        and summaries[0]["counts"]["initial_verified_pass"] == 1
        and summaries[1]["counts"]["initial_hold"] == 1
        and summaries[2]["counts"]["initial_false_greens"] == 1
        and summaries[2]["counts"]["repair_episodes_converted"] == 1
        and summaries[2]["counts"]["ap001_section9_sequences"] == 1
        and summaries[0]["measures"]["generation_latency_ms"][
            "median"
        ]
        == 100
        and report["counts"]["planned_initial_attempts"] == 3
    )


def main() -> int:
    plan = load_plan(PLAN)
    attempts = planned_initials(plan)
    configurations = [
        (
            config["configuration_id"],
            config["provider"],
            config["expected_model"],
            next(iter(model_environment(config))),
        )
        for config in plan["configurations"]
    ]
    preview = subprocess.run(
        [
            sys.executable,
            str(RUNNER_ROOT / "batch.py"),
            "--plan",
            str(PLAN),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    preview_payload = (
        json.loads(preview.stdout) if preview.returncode == 0 else {}
    )
    split_attempt = subprocess.run(
        [
            sys.executable,
            str(RUNNER_ROOT / "batch.py"),
            "--plan",
            str(PLAN),
            "--configuration-id",
            "ollama-llama3-latest",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    policy = plan["execution_policy"]
    analysis = plan["analysis_plan"]
    labels = [attempt["run_label"] for attempt in attempts]
    live_phase12 = [
        path
        for path in LIVE_ROOT.iterdir()
        if path.is_dir() and "phase12" in path.name.lower()
    ]
    checks = {
        "baseline_is_phase11b_merge": (
            plan["baseline_commit"]
            == "8503cf9eb71ac634642424521bf148fd0fc5958e"
        ),
        "fixed_three_configuration_matrix": (
            configurations == EXPECTED_CONFIGURATIONS
            and len(attempts) == 30
            and len(labels) == len(set(labels))
        ),
        "same_task_and_protocol": all(
            attempt["task_id"] == "AP-001"
            and attempt["task_version"] == "0.1.0"
            and attempt["configuration"]["temperature"] == 0
            and attempt["configuration"]["output_protocol"]
            == "strict-code-only-v2"
            for attempt in attempts
        ),
        "non_stopping_preservation_policy": (
            policy["fixed_initial_trial_count"] is True
            and policy["stop_initial_trials_on_success"] is False
            and policy["preserve_all_outcomes"] is True
            and policy["run_all_configurations_in_one_batch"] is True
            and policy["require_single_source_commit"] is True
        ),
        "bounded_repair_policy": (
            plan["tasks"][0]["max_repairs_per_false_green"] == 2
            and policy["stop_repairs_after_conversion"] is True
        ),
        "configuration_level_analysis": (
            analysis["report_by_configuration"] is True
            and analysis["pool_configurations_for_performance_claims"]
            is False
            and analysis["confidence_interval"]
            == "two-sided 95% Wilson"
            and "do not impute" in analysis["missing_cost_policy"]
        ),
        "dry_run_lists_all_attempts": (
            preview.returncode == 0
            and preview_payload.get("mode") == "dry-run"
            and preview_payload.get("planned_initial_attempts") == 30
            and len(preview_payload.get("attempts", [])) == 30
        ),
        "split_execution_blocked": split_attempt.returncode != 0,
        "per_configuration_report": synthetic_report_check(plan),
        "no_phase12_results_committed": (
            not RESULT_ROOT.exists() and not live_phase12
        ),
        "claim_boundary_preserved": (
            any(
                "creates no model-performance evidence" in item
                for item in plan["claim_boundary"]
            )
            and any(
                "not general coding-agent" in item
                for item in plan["claim_boundary"]
            )
            and any(
                "Section 9 gap closes only if" in item
                for item in plan["claim_boundary"]
            )
        ),
    }

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"experiment_plan_sha256: {canonical_json_hash(plan)}")

    ok = all(checks.values())
    print(
        "PHASE 12A PREREGISTRATION GREEN"
        if ok
        else "PHASE 12A PREREGISTRATION FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
