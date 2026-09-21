from __future__ import annotations

from pathlib import Path
import sys


METRICS_ROOT = Path(__file__).resolve().parent

if str(METRICS_ROOT) not in sys.path:
    sys.path.insert(0, str(METRICS_ROOT))

from aggregate import aggregate


def close(a: float | None, b: float) -> bool:
    return a is not None and abs(a - b) < 1e-12


def main() -> int:
    summary = aggregate()
    counts = summary["counts"]
    metrics = summary["metrics"]
    qualification = summary["verifier_qualification"]

    checks = {
        "attempts_total": counts["attempts_total"] == 51,
        "initial_attempts": counts["initial_attempts"] == 48,
        "repair_attempts": counts["repair_attempts"] == 3,
        "verdict_distribution": (
            counts["verified_pass"] == 43
            and counts["verified_fail"] == 5
            and counts["hold"] == 3
        ),
        "candidate_admitted": counts["candidate_admitted"] == 48,
        "explicit_claim_coverage": (
            counts["explicit_claim_coverage"] == 48
        ),
        "claim_evidence_gap": (
            metrics["claim_evidence_gap"]["numerator"] == 5
            and metrics["claim_evidence_gap"]["denominator"] == 48
            and close(
                metrics["claim_evidence_gap"]["value"],
                5 / 48,
            )
        ),
        "false_green_rate": (
            metrics["false_green_rate"]["numerator"] == 3
            and metrics["false_green_rate"]["denominator"] == 46
            and close(
                metrics["false_green_rate"]["value"],
                3 / 46,
            )
        ),
        "initial_false_green_rate": (
            metrics["initial_false_green_rate"]["numerator"] == 2
            and metrics["initial_false_green_rate"]["denominator"] == 44
            and close(
                metrics["initial_false_green_rate"]["value"],
                2 / 44,
            )
        ),
        "repair_conversion": (
            metrics["repair_conversion"]["numerator"] == 1
            and metrics["repair_conversion"]["denominator"] == 2
            and metrics["repair_conversion"]["value"] == 0.5
        ),
        "verifier_escape_rate": (
            qualification["qualified_tasks"] == 5
            and qualification["tasks_total"] == 5
            and qualification["critical_mutation_escapes"] == 0
            and qualification["critical_mutations_total"] == 17
            and metrics["verifier_escape_rate"]["value"] == 0.0
        ),
        "cost_coverage": (
            metrics["cost_per_verified_success_usd"][
                "cost_coverage_attempts"
            ]
            == 40
            and metrics["cost_per_verified_success_usd"][
                "reported_cost_usd_total"
            ]
            == 0.0
            and metrics["cost_per_verified_success_usd"][
                "economic_cost_complete"
            ]
            is False
            and metrics["cost_per_verified_success_usd"]["value"] is None
        ),
        "median_verified_latency": (
            metrics["median_time_to_verified_success_ms"][
                "observations"
            ]
            == 43
            and metrics["median_time_to_verified_success_ms"][
                "value"
            ]
            == 13398.0
        ),
    }

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    ok = all(checks.values())
    print(
        "PHASE 9C METRICS GREEN"
        if ok
        else "PHASE 9C METRICS FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
