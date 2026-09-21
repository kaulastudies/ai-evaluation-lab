from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
from typing import Any


RUNNER_ROOT = Path(__file__).resolve().parent

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from batch import load_plan, planned_initials
from engine import canonical_json_hash


class BatchReportError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BatchReportError(f"Unable to load {path}: {exc}") from exc


def wilson_interval(
    numerator: int,
    denominator: int,
    *,
    z: float = 1.959963984540054,
) -> dict[str, float | int | None]:
    if denominator == 0:
        return {
            "value": None,
            "lower_95": None,
            "upper_95": None,
            "numerator": numerator,
            "denominator": denominator,
        }
    p = numerator / denominator
    z2 = z * z
    scale = 1 + z2 / denominator
    center = (p + z2 / (2 * denominator)) / scale
    half = (
        z
        * math.sqrt(
            p * (1 - p) / denominator
            + z2 / (4 * denominator * denominator)
        )
        / scale
    )
    return {
        "value": p,
        "lower_95": max(0.0, center - half),
        "upper_95": min(1.0, center + half),
        "numerator": numerator,
        "denominator": denominator,
    }


def summarize(
    plan: dict[str, Any],
    ledger: dict[str, Any],
    batch_root: Path,
) -> dict[str, Any]:
    if ledger.get("status") != "COMPLETE":
        raise BatchReportError("Batch ledger is not COMPLETE")
    if ledger.get("experiment_id") != plan["experiment_id"]:
        raise BatchReportError("Experiment ID does not match plan")
    if ledger.get("experiment_plan_sha256") != canonical_json_hash(plan):
        raise BatchReportError("Experiment plan hash does not match ledger")

    plan_hash = canonical_json_hash(plan)
    configuration_by_id = {
        config["configuration_id"]: config
        for config in plan["configurations"]
    }
    batch_root = batch_root.resolve()

    observations: list[dict[str, Any]] = []
    for item in ledger.get("attempts", []):
        evidence_dir = (batch_root / item["evidence_dir"]).resolve()
        if evidence_dir != batch_root and batch_root not in evidence_dir.parents:
            raise BatchReportError("Evidence path escapes batch root")
        record = load_json(evidence_dir / "evaluation.json")
        manifest = load_json(evidence_dir / "manifest.json")
        if record["run_label"] != item["run_label"]:
            raise BatchReportError("Ledger run label does not match evidence")
        if manifest["source_commit"] != record["source_commit"]:
            raise BatchReportError("Manifest source commit does not match record")
        experiment = manifest.get("experiment") or {}
        if experiment.get("experiment_id") != plan["experiment_id"]:
            raise BatchReportError("Manifest experiment ID does not match plan")
        if experiment.get("experiment_plan_sha256") != plan_hash:
            raise BatchReportError("Manifest plan hash does not match plan")
        config_id = experiment.get("configuration_id")
        config = configuration_by_id.get(config_id)
        if config is None:
            raise BatchReportError("Manifest configuration is not in plan")
        if manifest["provider"] != config["provider"]:
            raise BatchReportError("Manifest provider does not match plan")
        if manifest["model"] != config["expected_model"]:
            raise BatchReportError("Manifest model does not match plan")
        evaluation = record.get("evaluation")
        expected_hash = (
            None if evaluation is None else evaluation["record_hash"]
        )
        if manifest.get("evaluation_record_hash") != expected_hash:
            raise BatchReportError(
                "Manifest evaluation hash does not match record"
            )
        observations.append(
            {
                "item": item,
                "record": record,
                "manifest": manifest,
            }
        )

    initials = [
        observation
        for observation in observations
        if observation["item"]["attempt_kind"] == "initial"
    ]
    repairs = [
        observation
        for observation in observations
        if observation["item"]["attempt_kind"] == "repair"
    ]
    planned_count = len(planned_initials(plan))
    if len(initials) != planned_count:
        raise BatchReportError(
            f"Expected {planned_count} initial attempts; found {len(initials)}"
        )

    initial_verdicts = Counter(
        observation["record"]["final_verdict"]
        for observation in initials
    )
    initial_public_pass = [
        observation
        for observation in initials
        if (observation["record"].get("evaluation") or {})
        .get("public_validation", {})
        .get("passed")
        is True
    ]
    initial_false_greens = [
        observation
        for observation in initial_public_pass
        if observation["record"]["evaluation"]["false_green"] is True
    ]

    repairs_by_parent: dict[str, list[dict[str, Any]]] = {}
    for observation in repairs:
        parent = observation["record"]["parent"]["run_label"]
        repairs_by_parent.setdefault(parent, []).append(observation)
    converted_parents = {
        parent
        for parent, group in repairs_by_parent.items()
        if any(
            observation["record"]["repair_conversion"] is True
            for observation in group
        )
    }
    false_green_labels = {
        observation["record"]["run_label"]
        for observation in initial_false_greens
    }
    section9_sequences = sorted(false_green_labels & converted_parents)

    configurations = sorted(
        {
            (
                observation["manifest"]["provider"],
                observation["manifest"]["model"],
                observation["manifest"].get("experiment", {}).get(
                    "configuration_id"
                ),
            )
            for observation in initials
        },
        key=lambda item: tuple(str(value) for value in item),
    )

    return {
        "schema_version": "1.0.0",
        "experiment_id": plan["experiment_id"],
        "experiment_plan_sha256": plan_hash,
        "source_commit": ledger["source_commit"],
        "status": "COMPLETE",
        "fixed_initial_trial_count_satisfied": True,
        "counts": {
            "planned_initial_attempts": planned_count,
            "observed_initial_attempts": len(initials),
            "repair_attempts": len(repairs),
            "initial_verified_pass": initial_verdicts.get(
                "VERIFIED_PASS", 0
            ),
            "initial_verified_fail": initial_verdicts.get(
                "VERIFIED_FAIL", 0
            ),
            "initial_hold": initial_verdicts.get("HOLD", 0),
            "initial_false_greens": len(initial_false_greens),
            "repair_episodes": len(repairs_by_parent),
            "repair_episodes_converted": len(converted_parents),
            "ap001_section9_sequences": len(section9_sequences),
        },
        "rates": {
            "initial_verified_pass": wilson_interval(
                initial_verdicts.get("VERIFIED_PASS", 0),
                len(initials),
            ),
            "initial_false_green": wilson_interval(
                len(initial_false_greens),
                len(initial_public_pass),
            ),
            "repair_conversion": wilson_interval(
                len(converted_parents),
                len(repairs_by_parent),
            ),
        },
        "section9_sequence_parent_runs": section9_sequences,
        "observed_configurations": [
            {
                "provider": provider,
                "model": model,
                "configuration_id": configuration_id,
            }
            for provider, model, configuration_id in configurations
        ],
        "claim_boundary": plan["claim_boundary"],
    }


def fmt_rate(rate: dict[str, Any]) -> str:
    if rate["value"] is None:
        return "N/A"
    return (
        f"{rate['value'] * 100:.1f}% "
        f"(95% Wilson CI {rate['lower_95'] * 100:.1f}%–"
        f"{rate['upper_95'] * 100:.1f}%)"
    )


def render_markdown(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    rates = summary["rates"]
    lines = [
        f"# {summary['experiment_id']} Report",
        "",
        f"Status: **{summary['status']}**",
        "",
        "## Counts",
        "",
        f"- Planned initial attempts: **{counts['planned_initial_attempts']}**",
        f"- Observed initial attempts: **{counts['observed_initial_attempts']}**",
        f"- Repair attempts: **{counts['repair_attempts']}**",
        f"- Initial verdicts: **{counts['initial_verified_pass']} VERIFIED_PASS / "
        f"{counts['initial_verified_fail']} VERIFIED_FAIL / "
        f"{counts['initial_hold']} HOLD**",
        f"- AP-001 Section 9 sequences: **{counts['ap001_section9_sequences']}**",
        "",
        "## Rates",
        "",
        f"- Initial verified-pass rate: {fmt_rate(rates['initial_verified_pass'])}",
        f"- Initial false-green rate: {fmt_rate(rates['initial_false_green'])}",
        f"- Repair conversion: {fmt_rate(rates['repair_conversion'])}",
        "",
        "## Claim boundary",
        "",
    ]
    lines.extend(f"- {item}" for item in summary["claim_boundary"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--batch-root", required=True, type=Path)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()

    plan = load_plan(args.plan.resolve())
    batch_root = args.batch_root.resolve()
    ledger = load_json(batch_root / "batch-ledger.json")
    summary = summarize(plan, ledger, batch_root)
    markdown = render_markdown(summary)

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(
            markdown,
            encoding="utf-8",
            newline="\n",
        )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
