from __future__ import annotations

from pathlib import Path
import sys


METRICS_ROOT = Path(__file__).resolve().parent

if str(METRICS_ROOT) not in sys.path:
    sys.path.insert(0, str(METRICS_ROOT))

from aggregate import aggregate


def main() -> int:
    summary = aggregate()
    counts = summary["counts"]
    metrics = summary["metrics"]
    qualification = summary["verifier_qualification"]

    checks = {
        "attempts_total": counts["attempts_total"] == 6,
        "initial_attempts": counts["initial_attempts"] == 4,
        "repair_attempts": counts["repair_attempts"] == 2,
        "verdict_distribution": (
            counts["verified_pass"] == 2
            and counts["verified_fail"] == 2
            and counts["hold"] == 2
        ),
        "explicit_claim_coverage": (
            counts["explicit_claim_coverage"] == 4
        ),
        "claim_evidence_gap": (
            metrics["claim_evidence_gap"]["numerator"] == 2
            and metrics["claim_evidence_gap"]["denominator"] == 4
            and metrics["claim_evidence_gap"]["value"] == 0.5
        ),
        "false_green_rate": (
            metrics["false_green_rate"]["numerator"] == 2
            and metrics["false_green_rate"]["denominator"] == 4
            and metrics["false_green_rate"]["value"] == 0.5
        ),
        "initial_false_green_rate": (
            metrics["initial_false_green_rate"]["numerator"] == 1
            and metrics["initial_false_green_rate"]["denominator"] == 3
        ),
        "repair_conversion": (
            metrics["repair_conversion"]["numerator"] == 0
            and metrics["repair_conversion"]["denominator"] == 1
            and metrics["repair_conversion"]["value"] == 0.0
        ),
        "verifier_escape_rate": (
            qualification["critical_mutation_escapes"] == 0
            and qualification["critical_mutations_total"] == 9
            and metrics["verifier_escape_rate"]["value"] == 0.0
        ),
        "cost_coverage": (
            metrics["cost_per_verified_success_usd"][
                "cost_coverage_attempts"
            ]
            == 6
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
            == 2
            and metrics["median_time_to_verified_success_ms"][
                "value"
            ]
            == 82907.5
        ),
    }

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    ok = all(checks.values())
    print(
        "PHASE 7A METRICS GREEN"
        if ok
        else "PHASE 7A METRICS FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
