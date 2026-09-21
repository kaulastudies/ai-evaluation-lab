from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPO_ROOT = PROGRAM_ROOT.parents[1]
PLAN = (
    PROGRAM_ROOT
    / "experiments"
    / "phase-11b-ap001-closure-v1.json"
)
MODEL_TRIAL = RUNNER_ROOT / "model_trial.py"
REPAIR = RUNNER_ROOT / "repair.py"
TASK_ROOT = PROGRAM_ROOT / "tasks" / "AP-001"
KNOWN_BAD = (
    TASK_ROOT
    / "controls"
    / "known_bad"
    / "app"
    / "resource_view.py"
)
REFERENCE = (
    TASK_ROOT
    / "controls"
    / "reference"
    / "app"
    / "resource_view.py"
)

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from batch import load_plan, planned_initials
from batch_report import summarize
from engine import canonical_json_hash


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )


def main() -> int:
    plan = load_plan(PLAN)
    attempts = planned_initials(plan)

    with tempfile.TemporaryDirectory(
        prefix="rarb-phase11b-batch-check-"
    ) as td:
        temp = Path(td)
        initial = temp / "initial"
        repair = temp / "repair"
        initial.mkdir()
        repair.mkdir()

        initial_process = run(
            [
                sys.executable,
                str(MODEL_TRIAL),
                "--task",
                "AP-001",
                "--provider",
                "mock",
                "--response-file",
                str(KNOWN_BAD),
                "--label",
                "phase11b-mock-ap001-initial",
                "--output-protocol",
                "strict-code-only-v2",
                "--response-out",
                str(initial / "model-response.txt"),
                "--candidate-out",
                str(initial / "candidate-resource_view.py"),
                "--out",
                str(initial / "evaluation.json"),
                "--manifest-out",
                str(initial / "manifest.json"),
                "--experiment-id",
                plan["experiment_id"],
                "--experiment-plan-sha256",
                canonical_json_hash(plan),
                "--configuration-id",
                "mock-regression-only",
                "--trial-index",
                "1",
            ]
        )

        if initial_process.returncode != 1:
            print(initial_process.stdout)
            print(initial_process.stderr, file=sys.stderr)
            print("PHASE 11B BATCH CHECK FAILED")
            return 1

        repair_process = run(
            [
                sys.executable,
                str(REPAIR),
                "--task",
                "AP-001",
                "--parent-evidence",
                str(initial),
                "--provider",
                "mock",
                "--response-file",
                str(REFERENCE),
                "--label",
                "phase11b-mock-ap001-repair-01",
                "--output-protocol",
                "strict-code-only-v2",
                "--response-out",
                str(repair / "model-response.txt"),
                "--candidate-out",
                str(repair / "candidate-resource_view.py"),
                "--out",
                str(repair / "evaluation.json"),
                "--manifest-out",
                str(repair / "manifest.json"),
                "--experiment-id",
                plan["experiment_id"],
                "--experiment-plan-sha256",
                canonical_json_hash(plan),
                "--configuration-id",
                "mock-regression-only",
                "--trial-index",
                "1",
                "--repair-index",
                "1",
            ]
        )

        if repair_process.returncode != 0:
            print(repair_process.stdout)
            print(repair_process.stderr, file=sys.stderr)
            print("PHASE 11B BATCH CHECK FAILED")
            return 1

        initial_record = json.loads(
            (initial / "evaluation.json").read_text(encoding="utf-8")
        )
        initial_manifest = json.loads(
            (initial / "manifest.json").read_text(encoding="utf-8")
        )
        repair_record = json.loads(
            (repair / "evaluation.json").read_text(encoding="utf-8")
        )
        repair_manifest = json.loads(
            (repair / "manifest.json").read_text(encoding="utf-8")
        )

        report_plan = copy.deepcopy(plan)
        report_plan["tasks"][0]["initial_trials"] = 1
        report_plan["configurations"] = [
            {
                "configuration_id": "mock-regression-only",
                "provider": "mock",
                "expected_model": "synthetic-alpha",
                "temperature": 0,
                "output_protocol": "strict-code-only-v2",
            }
        ]
        report_plan_hash = canonical_json_hash(report_plan)
        report_initial_manifest = copy.deepcopy(initial_manifest)
        report_repair_manifest = copy.deepcopy(repair_manifest)
        report_initial_manifest["experiment"][
            "experiment_plan_sha256"
        ] = report_plan_hash
        report_repair_manifest["experiment"][
            "experiment_plan_sha256"
        ] = report_plan_hash
        (initial / "manifest.json").write_text(
            json.dumps(
                report_initial_manifest,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (repair / "manifest.json").write_text(
            json.dumps(
                report_repair_manifest,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        report_ledger = {
            "schema_version": "1.0.0",
            "experiment_id": report_plan["experiment_id"],
            "experiment_plan_sha256": report_plan_hash,
            "source_commit": initial_record["source_commit"],
            "status": "COMPLETE",
            "attempts": [
                {
                    "run_label": initial_record["run_label"],
                    "task_id": "AP-001",
                    "attempt_kind": "initial",
                    "configuration_id": "mock-regression-only",
                    "evidence_dir": "initial",
                },
                {
                    "run_label": repair_record["run_label"],
                    "task_id": "AP-001",
                    "attempt_kind": "repair",
                    "configuration_id": "mock-regression-only",
                    "parent_run_label": initial_record["run_label"],
                    "evidence_dir": "repair",
                },
            ],
        }
        report = summarize(report_plan, report_ledger, temp)

        labels = [attempt["run_label"] for attempt in attempts]
        checks = {
            "fixed_trial_count": len(attempts) == 10,
            "unique_labels": len(labels) == len(set(labels)),
            "single_preregistered_configuration": all(
                attempt["configuration"]["configuration_id"]
                == "ollama-llama3-latest"
                for attempt in attempts
            ),
            "no_early_stop": (
                plan["execution_policy"][
                    "stop_initial_trials_on_success"
                ]
                is False
            ),
            "initial_false_green": (
                initial_record["final_verdict"] == "VERIFIED_FAIL"
                and initial_record["evaluation"]["public_validation"][
                    "passed"
                ]
                is True
                and initial_record["evaluation"]["false_green"] is True
            ),
            "initial_manifest_replay_fields": (
                initial_manifest["response_bytes"]
                == (initial / "model-response.txt").stat().st_size
                and initial_manifest["candidate_admitted"] is True
                and initial_manifest["evaluation_record_hash"]
                == initial_record["evaluation"]["record_hash"]
            ),
            "repair_converts": (
                repair_record["final_verdict"] == "VERIFIED_PASS"
                and repair_record["repair_conversion"] is True
                and repair_record["repair_context"]["failed_gate_ids"]
                == ["AP001-G02"]
            ),
            "repair_manifest_parent": (
                repair_manifest["parent_record_hash"]
                == initial_record["evaluation"]["record_hash"]
                and repair_manifest["parent_candidate_sha256"]
                == initial_record["candidate_sha256"]
                and repair_manifest["repair_conversion"] is True
            ),
            "experiment_metadata": (
                initial_manifest["experiment"]["experiment_id"]
                == plan["experiment_id"]
                and initial_manifest["experiment"][
                    "experiment_plan_sha256"
                ]
                == canonical_json_hash(plan)
                and repair_manifest["experiment"]["repair_index"] == 1
            ),
            "batch_report_section9": (
                report["counts"]["ap001_section9_sequences"] == 1
                and report["section9_sequence_parent_runs"]
                == [initial_record["run_label"]]
            ),
            "batch_report_intervals": (
                report["rates"]["initial_false_green"]["value"] == 1.0
                and report["rates"]["initial_false_green"][
                    "lower_95"
                ]
                is not None
                and report["rates"]["repair_conversion"]["value"]
                == 1.0
            ),
            "mock_not_live_evidence": not any(
                path.is_dir()
                and "phase11b-mock" in path.name
                for path in (TASK_ROOT / "evidence" / "live").iterdir()
            ),
        }

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    ok = all(checks.values())
    print(
        "PHASE 11B BATCH CHECK GREEN"
        if ok
        else "PHASE 11B BATCH CHECK FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
