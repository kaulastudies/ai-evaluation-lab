from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
from typing import Any


METRICS_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = METRICS_ROOT.parent
TASKS_ROOT = PROGRAM_ROOT / "tasks"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def discover_attempts() -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []

    for live_root in sorted(TASKS_ROOT.glob("AP-*/evidence/live")):
        task_id = live_root.parents[1].name

        for evidence_dir in sorted(
            path for path in live_root.iterdir() if path.is_dir()
        ):
            manifest_path = evidence_dir / "manifest.json"
            evaluation_path = evidence_dir / "evaluation.json"

            if not manifest_path.is_file() or not evaluation_path.is_file():
                continue

            manifest = load_json(manifest_path)
            record = load_json(evaluation_path)
            evaluation = record.get("evaluation")
            provider = record.get("provider") or {}

            attempt_kind = record.get("attempt_kind", "initial")
            final_verdict = record.get(
                "final_verdict",
                manifest.get("final_verdict"),
            )
            candidate_admission = record.get("candidate_admission") or {}

            agent_claimed_success = None
            public_passed = None
            false_green = None
            trusted_unchanged = None
            evaluation_record_hash = None

            if evaluation is not None:
                agent_claimed_success = evaluation.get(
                    "agent_claimed_success"
                )
                public_validation = evaluation.get("public_validation") or {}
                public_passed = public_validation.get("passed")
                false_green = evaluation.get("false_green")
                trusted_unchanged = evaluation.get(
                    "trusted_files_unchanged_after_scoring"
                )
                evaluation_record_hash = evaluation.get("record_hash")

            attempts.append(
                {
                    "task_id": task_id,
                    "run_label": record.get(
                        "run_label",
                        manifest.get("run_label"),
                    ),
                    "attempt_kind": attempt_kind,
                    "source_commit": record.get(
                        "source_commit",
                        manifest.get("source_commit"),
                    ),
                    "provider": provider.get(
                        "name",
                        manifest.get("provider"),
                    ),
                    "model": provider.get(
                        "model",
                        manifest.get("model"),
                    ),
                    "latency_ms": provider.get(
                        "latency_ms",
                        manifest.get("latency_ms"),
                    ),
                    "input_tokens": provider.get(
                        "input_tokens",
                        manifest.get("input_tokens"),
                    ),
                    "output_tokens": provider.get(
                        "output_tokens",
                        manifest.get("output_tokens"),
                    ),
                    "estimated_cost_usd": provider.get(
                        "estimated_cost_usd",
                        manifest.get("estimated_cost_usd"),
                    ),
                    "candidate_admitted": candidate_admission.get(
                        "accepted",
                        manifest.get("candidate_admitted"),
                    ),
                    "agent_claimed_success": agent_claimed_success,
                    "public_tests_passed": public_passed,
                    "false_green": false_green,
                    "trusted_files_unchanged": trusted_unchanged,
                    "final_verdict": final_verdict,
                    "evaluation_record_hash": evaluation_record_hash,
                    "parent_record_hash": (
                        (record.get("parent") or {}).get("record_hash")
                        or manifest.get("parent_record_hash")
                    ),
                    "repair_conversion": record.get(
                        "repair_conversion",
                        manifest.get("repair_conversion"),
                    ),
                    "terminal": manifest.get("terminal", False),
                    "evidence_path": evidence_dir.relative_to(
                        PROGRAM_ROOT
                    ).as_posix(),
                }
            )

    return attempts


def verifier_qualification_metrics() -> dict[str, Any]:
    tasks = []
    total = 0
    rejected = 0
    known_bad_total = 0
    known_bad_rejected = 0

    for path in sorted(
        TASKS_ROOT.glob("AP-*/evidence/verifier-qualification.json")
    ):
        record = load_json(path)
        critical_total = int(
            record.get("critical_mutations_total", 0)
        )
        critical_rejected = int(
            record.get("critical_mutations_rejected", 0)
        )
        total += critical_total
        rejected += critical_rejected

        known_bad_total += 1
        if record.get("known_bad_rejected") is True:
            known_bad_rejected += 1

        tasks.append(
            {
                "task_id": record["task_id"],
                "status": record.get("status"),
                "critical_mutations_total": critical_total,
                "critical_mutations_rejected": critical_rejected,
                "critical_mutation_escapes": (
                    critical_total - critical_rejected
                ),
                "known_bad_rejected": record.get(
                    "known_bad_rejected"
                ),
                "reference_passed": record.get("reference_passed"),
            }
        )

    escapes = total - rejected
    return {
        "tasks": tasks,
        "qualified_tasks": sum(
            1 for item in tasks if item["status"] == "QUALIFIED"
        ),
        "tasks_total": len(tasks),
        "critical_mutations_total": total,
        "critical_mutations_rejected": rejected,
        "critical_mutation_escapes": escapes,
        "verifier_escape_rate": pct(escapes, total),
        "known_bad_controls_total": known_bad_total,
        "known_bad_controls_rejected": known_bad_rejected,
    }


def aggregate() -> dict[str, Any]:
    attempts = discover_attempts()
    verdict_counts = Counter(
        attempt["final_verdict"] for attempt in attempts
    )
    kind_counts = Counter(
        attempt["attempt_kind"] for attempt in attempts
    )

    explicit_claims = [
        attempt
        for attempt in attempts
        if attempt["agent_claimed_success"] is not None
    ]
    explicit_success_claims = [
        attempt
        for attempt in explicit_claims
        if attempt["agent_claimed_success"] is True
    ]
    claimed_success_not_verified = [
        attempt
        for attempt in explicit_success_claims
        if attempt["final_verdict"] != "VERIFIED_PASS"
    ]

    false_green_population = [
        attempt
        for attempt in explicit_success_claims
        if attempt["public_tests_passed"] is True
    ]
    false_greens = [
        attempt
        for attempt in false_green_population
        if attempt["false_green"] is True
    ]

    initial_false_green_population = [
        attempt
        for attempt in false_green_population
        if attempt["attempt_kind"] == "initial"
    ]
    initial_false_greens = [
        attempt
        for attempt in initial_false_green_population
        if attempt["false_green"] is True
    ]

    repair_attempts = [
        attempt
        for attempt in attempts
        if attempt["attempt_kind"] == "repair"
    ]
    repair_episode_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for attempt in repair_attempts:
        parent_hash = attempt.get("parent_record_hash")
        if parent_hash:
            repair_episode_groups[parent_hash].append(attempt)

    converted_episodes = sum(
        1
        for group in repair_episode_groups.values()
        if any(
            attempt["final_verdict"] == "VERIFIED_PASS"
            and attempt["repair_conversion"] is True
            for attempt in group
        )
    )

    known_cost_attempts = [
        attempt
        for attempt in attempts
        if attempt["estimated_cost_usd"] is not None
    ]
    total_reported_cost = sum(
        float(attempt["estimated_cost_usd"])
        for attempt in known_cost_attempts
    )

    economic_cost_complete = (
        len(known_cost_attempts) == len(attempts)
        and all(
            attempt["provider"] not in {"ollama"}
            for attempt in attempts
        )
    )

    verified_passes = verdict_counts.get("VERIFIED_PASS", 0)

    verified_success_latencies = [
        float(attempt["latency_ms"])
        for attempt in attempts
        if attempt["final_verdict"] == "VERIFIED_PASS"
        and attempt["latency_ms"] is not None
    ]

    qualification = verifier_qualification_metrics()

    summary = {
        "schema_version": "1.0.0",
        "program": "repository-agent-reliability",
        "scope": (
            "committed live model attempts and committed verifier "
            "qualification evidence"
        ),
        "attempts": attempts,
        "counts": {
            "attempts_total": len(attempts),
            "initial_attempts": kind_counts.get("initial", 0),
            "repair_attempts": kind_counts.get("repair", 0),
            "verified_pass": verdict_counts.get("VERIFIED_PASS", 0),
            "verified_fail": verdict_counts.get("VERIFIED_FAIL", 0),
            "hold": verdict_counts.get("HOLD", 0),
            "candidate_admitted": sum(
                1
                for attempt in attempts
                if attempt["candidate_admitted"] is True
            ),
            "explicit_claim_coverage": len(explicit_claims),
            "public_test_observations": sum(
                1
                for attempt in attempts
                if attempt["public_tests_passed"] is not None
            ),
            "false_green_count": len(false_greens),
            "repair_episodes": len(repair_episode_groups),
            "repair_episodes_converted": converted_episodes,
        },
        "metrics": {
            "claim_evidence_gap": {
                "value": pct(
                    len(claimed_success_not_verified),
                    len(explicit_success_claims),
                ),
                "numerator": len(claimed_success_not_verified),
                "denominator": len(explicit_success_claims),
                "definition": (
                    "Among attempts with an explicit agent success claim, "
                    "the share that did not end VERIFIED_PASS."
                ),
                "coverage_note": (
                    "Attempts without an explicit stored success-claim field "
                    "are excluded rather than inferred."
                ),
            },
            "false_green_rate": {
                "value": pct(
                    len(false_greens),
                    len(false_green_population),
                ),
                "numerator": len(false_greens),
                "denominator": len(false_green_population),
                "definition": (
                    "Among explicit success claims whose public tests passed, "
                    "the share rejected by the qualified verifier."
                ),
            },
            "initial_false_green_rate": {
                "value": pct(
                    len(initial_false_greens),
                    len(initial_false_green_population),
                ),
                "numerator": len(initial_false_greens),
                "denominator": len(initial_false_green_population),
                "definition": (
                    "False-Green Rate restricted to non-repair attempts."
                ),
            },
            "repair_conversion": {
                "value": pct(
                    converted_episodes,
                    len(repair_episode_groups),
                ),
                "numerator": converted_episodes,
                "denominator": len(repair_episode_groups),
                "definition": (
                    "Share of bounded-repair episodes with at least one "
                    "VERIFIED_PASS repair."
                ),
            },
            "verifier_escape_rate": {
                "value": qualification["verifier_escape_rate"],
                "numerator": qualification[
                    "critical_mutation_escapes"
                ],
                "denominator": qualification[
                    "critical_mutations_total"
                ],
                "definition": (
                    "Critical verifier-qualification mutations that escaped "
                    "detection divided by critical mutations exercised."
                ),
            },
            "cost_per_verified_success_usd": {
                "value": (
                    total_reported_cost / verified_passes
                    if verified_passes and economic_cost_complete
                    else None
                ),
                "reported_cost_usd_total": total_reported_cost,
                "economic_cost_complete": economic_cost_complete,
                "verified_successes": verified_passes,
                "cost_coverage_attempts": len(known_cost_attempts),
                "attempts_total": len(attempts),
                "definition": (
                    "Reported provider cost divided by VERIFIED_PASS count "
                    "when every attempt has a reported cost."
                ),
                "coverage_note": (
                    "Local-provider cost fields do not meter hardware, "
                    "energy, or operator time."
                ),
            },
            "median_time_to_verified_success_ms": {
                "value": (
                    statistics.median(verified_success_latencies)
                    if verified_success_latencies
                    else None
                ),
                "observations": len(verified_success_latencies),
                "definition": (
                    "Median recorded model-generation latency among "
                    "VERIFIED_PASS attempts."
                ),
            },
        },
        "verifier_qualification": qualification,
    }

    return summary


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def fmt_number(value: float | None, suffix: str = "") -> str:
    if value is None:
        return "N/A"
    if float(value).is_integer():
        return f"{int(value)}{suffix}"
    return f"{value:.1f}{suffix}"


def render_markdown(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    metrics = summary["metrics"]

    lines = [
        "# RARB Evidence Metrics Snapshot",
        "",
        "This report is generated only from committed live evidence and "
        "committed verifier-qualification records. Missing fields are not "
        "fabricated.",
        "",
        "## Current evidence set",
        "",
        f"- Live attempts: **{counts['attempts_total']}** "
        f"({counts['initial_attempts']} initial, "
        f"{counts['repair_attempts']} repair)",
        f"- Verdicts: **{counts['verified_pass']} VERIFIED_PASS**, "
        f"**{counts['verified_fail']} VERIFIED_FAIL**, "
        f"**{counts['hold']} HOLD**",
        f"- Candidate admitted: **{counts['candidate_admitted']} / "
        f"{counts['attempts_total']}**",
        f"- Explicit success-claim coverage: "
        f"**{counts['explicit_claim_coverage']} / "
        f"{counts['attempts_total']}**",
        "",
        "## Primary metrics",
        "",
        "| Metric | Value | Evidence |",
        "| --- | ---: | --- |",
    ]

    metric_rows = [
        (
            "Claim–Evidence Gap",
            fmt_pct(metrics["claim_evidence_gap"]["value"]),
            (
                f"{metrics['claim_evidence_gap']['numerator']} / "
                f"{metrics['claim_evidence_gap']['denominator']} "
                "explicit success claims were not VERIFIED_PASS"
            ),
        ),
        (
            "False-Green Rate",
            fmt_pct(metrics["false_green_rate"]["value"]),
            (
                f"{metrics['false_green_rate']['numerator']} / "
                f"{metrics['false_green_rate']['denominator']} "
                "public-pass explicit success claims were verifier failures"
            ),
        ),
        (
            "Initial False-Green Rate",
            fmt_pct(metrics["initial_false_green_rate"]["value"]),
            (
                f"{metrics['initial_false_green_rate']['numerator']} / "
                f"{metrics['initial_false_green_rate']['denominator']} "
                "initial public-pass explicit success claims"
            ),
        ),
        (
            "Repair Conversion",
            fmt_pct(metrics["repair_conversion"]["value"]),
            (
                f"{metrics['repair_conversion']['numerator']} / "
                f"{metrics['repair_conversion']['denominator']} "
                "bounded-repair episodes reached VERIFIED_PASS"
            ),
        ),
        (
            "Verifier Escape Rate",
            fmt_pct(metrics["verifier_escape_rate"]["value"]),
            (
                f"{metrics['verifier_escape_rate']['numerator']} / "
                f"{metrics['verifier_escape_rate']['denominator']} "
                "critical mutations escaped qualification"
            ),
        ),
        (
            "Cost / Verified Success",
            (
                "N/A"
                if metrics["cost_per_verified_success_usd"]["value"] is None
                else (
                    "$"
                    + f"{metrics['cost_per_verified_success_usd']['value']:.4f}"
                )
            ),
            (
                "reported provider cost only; excludes local compute, "
                "energy, and operator time"
            ),
        ),
        (
            "Median Time to Verified Success",
            (
                "N/A"
                if metrics["median_time_to_verified_success_ms"]["value"]
                is None
                else (
                    f"{metrics['median_time_to_verified_success_ms']['value'] / 1000:.2f}s"
                )
            ),
            (
                f"{metrics['median_time_to_verified_success_ms']['observations']} "
                "VERIFIED_PASS latency observations"
            ),
        ),
    ]

    for name, value, evidence in metric_rows:
        lines.append(f"| {name} | {value} | {evidence} |")

    lines.extend(
        [
            "",
            "## Attempt ledger",
            "",
            "| Task | Run | Kind | Verdict | Public | False green | "
            "Latency |",
            "| --- | --- | --- | --- | --- | --- | ---: |",
        ]
    )

    for attempt in summary["attempts"]:
        public = attempt["public_tests_passed"]
        false_green = attempt["false_green"]
        latency = attempt["latency_ms"]
        lines.append(
            "| "
            + " | ".join(
                [
                    attempt["task_id"],
                    attempt["run_label"],
                    attempt["attempt_kind"],
                    str(attempt["final_verdict"]),
                    (
                        "N/A"
                        if public is None
                        else str(bool(public))
                    ),
                    (
                        "N/A"
                        if false_green is None
                        else str(bool(false_green))
                    ),
                    (
                        "N/A"
                        if latency is None
                        else f"{float(latency) / 1000:.2f}s"
                    ),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- This is a small observational evidence set, not a "
            "general model benchmark.",
            "- HOLD attempts without an explicit stored success-claim field "
            "are excluded from Claim–Evidence Gap rather than inferred.",
            "- Repair Conversion is episode-based; AP-003 currently provides "
            "one bounded-repair episode.",
            "- Reported provider cost is zero for the local Ollama trials, "
            "but that does not mean execution had zero real-world cost.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()

    summary = aggregate()

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    markdown = render_markdown(summary)
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
