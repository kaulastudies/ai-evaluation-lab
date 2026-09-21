from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPO_ROOT = PROGRAM_ROOT.parents[1]
MODEL_TRIAL = RUNNER_ROOT / "model_trial.py"
REPAIR = RUNNER_ROOT / "repair.py"

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from engine import canonical_json_hash, load_runtime


class PlanError(RuntimeError):
    pass


def load_plan(path: Path) -> dict[str, Any]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanError(f"Unable to load experiment plan: {exc}") from exc
    validate_plan(plan)
    return plan


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )


def git_output(*args: str) -> str:
    process = git(*args)
    if process.returncode != 0:
        raise PlanError(
            f"git {' '.join(args)} failed: {process.stderr.strip()}"
        )
    return process.stdout.strip()


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not result:
        raise PlanError(f"Cannot create label slug from {value!r}")
    return result


def validate_plan(plan: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "experiment_id",
        "status",
        "baseline_commit",
        "tasks",
        "configurations",
        "execution_policy",
        "claim_boundary",
    }
    missing = sorted(required - set(plan))
    if missing:
        raise PlanError("Experiment plan missing: " + ", ".join(missing))
    if plan["schema_version"] != "1.0.0":
        raise PlanError("Unsupported experiment schema_version")
    if plan["status"] != "PLANNED":
        raise PlanError("Only a PLANNED experiment may be executed")
    if not isinstance(plan["tasks"], list) or not plan["tasks"]:
        raise PlanError("Experiment plan requires at least one task")
    if not isinstance(plan["configurations"], list) or not plan[
        "configurations"
    ]:
        raise PlanError("Experiment plan requires at least one configuration")

    policy = plan["execution_policy"]
    required_policy = {
        "fixed_initial_trial_count": True,
        "stop_initial_trials_on_success": False,
        "preserve_all_outcomes": True,
        "require_clean_worktree": True,
        "stage_before_promotion": True,
    }
    for key, expected in required_policy.items():
        if policy.get(key) is not expected:
            raise PlanError(f"execution_policy.{key} must be {expected}")

    task_ids: set[str] = set()
    for task in plan["tasks"]:
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or task_id in task_ids:
            raise PlanError("Task IDs must be non-empty and unique")
        task_ids.add(task_id)
        task_root, runtime = load_runtime(task_id)
        if task.get("task_version") != runtime["version"]:
            raise PlanError(f"{task_id} task_version does not match runtime")
        if int(task.get("initial_trials", 0)) < 1:
            raise PlanError(f"{task_id} initial_trials must be positive")
        if int(task.get("max_repairs_per_false_green", -1)) < 0:
            raise PlanError(
                f"{task_id} max_repairs_per_false_green must be non-negative"
            )
        if not (task_root / runtime["qualification_path"]).is_file():
            raise PlanError(f"{task_id} qualification evidence is missing")

    configuration_ids: set[str] = set()
    for config in plan["configurations"]:
        config_id = config.get("configuration_id")
        if not isinstance(config_id, str) or config_id in configuration_ids:
            raise PlanError(
                "Configuration IDs must be non-empty and unique"
            )
        configuration_ids.add(config_id)
        if not config.get("provider") or not config.get("expected_model"):
            raise PlanError(
                f"{config_id} requires provider and expected_model"
            )
        if config.get("temperature") != 0:
            raise PlanError(f"{config_id} temperature must be 0")
        if config.get("output_protocol") not in {
            "strict-code-only-v1",
            "strict-code-only-v2",
        }:
            raise PlanError(f"{config_id} has unsupported output_protocol")


def planned_initials(
    plan: dict[str, Any],
    *,
    configuration_id: str | None = None,
) -> list[dict[str, Any]]:
    selected = [
        config
        for config in plan["configurations"]
        if configuration_id is None
        or config["configuration_id"] == configuration_id
    ]
    if not selected:
        raise PlanError(f"Unknown configuration: {configuration_id}")

    attempts: list[dict[str, Any]] = []
    experiment_slug = slug(plan["experiment_id"])
    for task in plan["tasks"]:
        for config in selected:
            for index in range(1, int(task["initial_trials"]) + 1):
                label = (
                    f"{experiment_slug}-{slug(task['task_id'])}-"
                    f"{slug(config['configuration_id'])}-i{index:03d}"
                )
                attempts.append(
                    {
                        "run_label": label,
                        "task_id": task["task_id"],
                        "task_version": task["task_version"],
                        "trial_index": index,
                        "max_repairs": int(
                            task["max_repairs_per_false_green"]
                        ),
                        "configuration": config,
                    }
                )

    labels = [attempt["run_label"] for attempt in attempts]
    if len(labels) != len(set(labels)):
        raise PlanError("Generated run labels are not unique")
    return attempts


def require_executable_state(plan: dict[str, Any]) -> str:
    baseline = plan["baseline_commit"]
    exists = git("cat-file", "-e", f"{baseline}^{{commit}}")
    if exists.returncode != 0:
        raise PlanError(f"Baseline commit is unavailable: {baseline}")
    ancestor = git("merge-base", "--is-ancestor", baseline, "HEAD")
    if ancestor.returncode != 0:
        raise PlanError("HEAD does not descend from the experiment baseline")
    if plan["execution_policy"]["require_clean_worktree"]:
        if git_output("status", "--porcelain"):
            raise PlanError(
                "Live execution requires a clean committed worktree so "
                "source-exact replay can resolve the evaluator version"
            )
    return git_output("rev-parse", "HEAD")


def run_process(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )


def read_record(path: Path, process: subprocess.CompletedProcess[str]) -> dict:
    if not path.is_file():
        raise RuntimeError(
            "Attempt did not emit evaluation.json\n"
            f"stdout:\n{process.stdout}\n"
            f"stderr:\n{process.stderr}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def validate_observed_configuration(
    record: dict[str, Any],
    config: dict[str, Any],
) -> None:
    observed = record["provider"]
    if observed["name"] != config["provider"]:
        raise RuntimeError(
            f"Provider mismatch: {observed['name']} != {config['provider']}"
        )
    if observed["model"] != config["expected_model"]:
        raise RuntimeError(
            f"Model mismatch: {observed['model']} != "
            f"{config['expected_model']}"
        )


def initial_command(
    plan: dict[str, Any],
    attempt: dict[str, Any],
    evidence_dir: Path,
) -> list[str]:
    config = attempt["configuration"]
    candidate_name = load_runtime(attempt["task_id"])[1][
        "candidate_path"
    ].split("/")[-1]
    return [
        sys.executable,
        str(MODEL_TRIAL),
        "--task",
        attempt["task_id"],
        "--provider",
        config["provider"],
        "--label",
        attempt["run_label"],
        "--output-protocol",
        config["output_protocol"],
        "--response-out",
        str(evidence_dir / "model-response.txt"),
        "--candidate-out",
        str(evidence_dir / f"candidate-{candidate_name}"),
        "--out",
        str(evidence_dir / "evaluation.json"),
        "--manifest-out",
        str(evidence_dir / "manifest.json"),
        "--experiment-id",
        plan["experiment_id"],
        "--experiment-plan-sha256",
        canonical_json_hash(plan),
        "--configuration-id",
        config["configuration_id"],
        "--trial-index",
        str(attempt["trial_index"]),
    ]


def repair_command(
    plan: dict[str, Any],
    attempt: dict[str, Any],
    parent_dir: Path,
    evidence_dir: Path,
    repair_index: int,
) -> list[str]:
    config = attempt["configuration"]
    candidate_name = load_runtime(attempt["task_id"])[1][
        "candidate_path"
    ].split("/")[-1]
    label = f"{attempt['run_label']}-repair-{repair_index:02d}"
    return [
        sys.executable,
        str(REPAIR),
        "--task",
        attempt["task_id"],
        "--parent-evidence",
        str(parent_dir),
        "--provider",
        config["provider"],
        "--label",
        label,
        "--output-protocol",
        config["output_protocol"],
        "--response-out",
        str(evidence_dir / "model-response.txt"),
        "--candidate-out",
        str(evidence_dir / f"candidate-{candidate_name}"),
        "--out",
        str(evidence_dir / "evaluation.json"),
        "--manifest-out",
        str(evidence_dir / "manifest.json"),
        "--experiment-id",
        plan["experiment_id"],
        "--experiment-plan-sha256",
        canonical_json_hash(plan),
        "--configuration-id",
        config["configuration_id"],
        "--trial-index",
        str(attempt["trial_index"]),
        "--repair-index",
        str(repair_index),
    ]


def write_logs(
    evidence_dir: Path,
    process: subprocess.CompletedProcess[str],
) -> None:
    (evidence_dir / "runner-stdout.txt").write_text(
        process.stdout,
        encoding="utf-8",
        newline="\n",
    )
    (evidence_dir / "runner-stderr.txt").write_text(
        process.stderr,
        encoding="utf-8",
        newline="\n",
    )


def execute(
    plan: dict[str, Any],
    attempts: list[dict[str, Any]],
    out_root: Path,
) -> dict[str, Any]:
    source_commit = require_executable_state(plan)
    if out_root.exists():
        if not out_root.is_dir() or any(out_root.iterdir()):
            raise PlanError(
                f"Refusing to overwrite non-empty output: {out_root}"
            )
    out_root.mkdir(parents=True, exist_ok=True)

    ledger: dict[str, Any] = {
        "schema_version": "1.0.0",
        "experiment_id": plan["experiment_id"],
        "experiment_plan_sha256": canonical_json_hash(plan),
        "source_commit": source_commit,
        "status": "RUNNING",
        "attempts": [],
    }

    try:
        for attempt in attempts:
            initial_dir = out_root / attempt["run_label"]
            initial_dir.mkdir(parents=True)
            process = run_process(
                initial_command(plan, attempt, initial_dir)
            )
            write_logs(initial_dir, process)
            record = read_record(initial_dir / "evaluation.json", process)
            validate_observed_configuration(
                record,
                attempt["configuration"],
            )
            item = {
                "run_label": record["run_label"],
                "task_id": record["task_id"],
                "attempt_kind": "initial",
                "configuration_id": attempt["configuration"][
                    "configuration_id"
                ],
                "provider": record["provider"]["name"],
                "model": record["provider"]["model"],
                "returncode": process.returncode,
                "final_verdict": record["final_verdict"],
                "false_green": (
                    record.get("evaluation") or {}
                ).get("false_green"),
                "evidence_dir": initial_dir.relative_to(
                    out_root
                ).as_posix(),
            }
            ledger["attempts"].append(item)

            is_false_green = item["false_green"] is True
            if not is_false_green:
                continue

            for repair_index in range(1, attempt["max_repairs"] + 1):
                repair_label = (
                    f"{attempt['run_label']}-repair-{repair_index:02d}"
                )
                repair_dir = out_root / repair_label
                repair_dir.mkdir(parents=True)
                repair_process = run_process(
                    repair_command(
                        plan,
                        attempt,
                        initial_dir,
                        repair_dir,
                        repair_index,
                    )
                )
                write_logs(repair_dir, repair_process)
                repair_record = read_record(
                    repair_dir / "evaluation.json",
                    repair_process,
                )
                validate_observed_configuration(
                    repair_record,
                    attempt["configuration"],
                )
                ledger["attempts"].append(
                    {
                        "run_label": repair_record["run_label"],
                        "task_id": repair_record["task_id"],
                        "attempt_kind": "repair",
                        "configuration_id": attempt["configuration"][
                            "configuration_id"
                        ],
                        "provider": repair_record["provider"]["name"],
                        "model": repair_record["provider"]["model"],
                        "parent_run_label": record["run_label"],
                        "returncode": repair_process.returncode,
                        "final_verdict": repair_record["final_verdict"],
                        "repair_conversion": repair_record[
                            "repair_conversion"
                        ],
                        "evidence_dir": repair_dir.relative_to(
                            out_root
                        ).as_posix(),
                    }
                )
                if repair_record["repair_conversion"] is True:
                    break
    except Exception:
        ledger["status"] = "FAILED"
        (out_root / "batch-ledger.json").write_text(
            json.dumps(ledger, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        raise

    ledger["status"] = "COMPLETE"
    (out_root / "batch-ledger.json").write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--configuration-id")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out-root", type=Path)
    args = parser.parse_args()

    plan = load_plan(args.plan.resolve())
    attempts = planned_initials(
        plan,
        configuration_id=args.configuration_id,
    )
    preview = {
        "schema_version": "1.0.0",
        "mode": "execute" if args.execute else "dry-run",
        "experiment_id": plan["experiment_id"],
        "experiment_plan_sha256": canonical_json_hash(plan),
        "planned_initial_attempts": len(attempts),
        "attempts": attempts,
        "claim_boundary": plan["claim_boundary"],
    }

    if not args.execute:
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return 0

    out_root = args.out_root
    if out_root is None:
        out_root = (
            REPO_ROOT
            / "runs"
            / "live"
            / "rarb"
            / plan["experiment_id"]
        )
    ledger = execute(plan, attempts, out_root.resolve())
    print(json.dumps(ledger, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
