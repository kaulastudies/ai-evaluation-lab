"""QProof Audit: offline measurement-count sanity and reproducibility report.

This checks small, analytically tractable circuits. It is not device certification.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def analyze(case):
    name = case["id"]
    shots = case["shots"]
    ones = case["ones"]
    theta = case["theta_radians"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("id must be a nonempty string")
    if type(shots) is not int or type(ones) is not int or shots < 1 or not 0 <= ones <= shots:
        raise ValueError("shots must be positive; ones must be an integer in [0, shots]")
    if not isinstance(theta, (int, float)) or not math.isfinite(theta):
        raise ValueError("theta_radians must be finite")
    if shots > 100000:
        raise ValueError("shots above 100000 not supported in this reference implementation")
    p = math.sin(theta / 2) ** 2
    observed = ones / shots
    # Wilson score interval for observed Bernoulli proportion at ~95% confidence.
    z = 1.959963984540054
    den = 1 + z*z / shots
    mid = (observed + z*z/(2*shots)) / den
    half = z * math.sqrt((observed*(1-observed) + z*z/(4*shots))/shots) / den
    # Avoid floating-point cancellation producing tiny nonzero bounds at p=0/1.
    low = 0.0 if ones == 0 else max(0.0, mid-half)
    high = 1.0 if ones == shots else min(1.0, mid+half)
    # Diagnostic flag only: CI exclusion is NOT a corrected multiple-testing decision.
    flag = not (low <= p <= high)
    return {"id": name, "shots": shots, "ones": ones,
            "expected_p1": round(p, 8), "observed_p1": round(observed, 8),
            "wilson_95_interval": [round(low, 8), round(high, 8)],
            "flag": "REVIEW" if flag else "IN_RANGE"}


def audit(payload):
    cases = payload["cases"]
    if not isinstance(cases, list) or not cases or len(cases) > 1000:
        raise ValueError("cases must contain 1..1000 entries")
    if any(not isinstance(c, dict) for c in cases):
        raise ValueError("each case must be an object")
    ids = [c.get("id") for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("case IDs must be unique")
    results = [analyze(c) for c in cases]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {"tool": "QProof Audit", "version": "0.1", "method": "Wilson 95% CI (uncorrected screening)",
            "limitations": "Not hardware certification, quantum advantage, or multiple-testing adjusted",
            "evidence_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "total_cases": len(results), "flagged": sum(r["flag"] == "REVIEW" for r in results),
            "results": results}


def main():
    ap = argparse.ArgumentParser(description="QProof Audit: verify quantum measurement results")
    ap.add_argument("input", type=Path, help="JSON object with cases array")
    ap.add_argument("--output", type=Path, help="write JSON report to file")
    args = ap.parse_args()
    result = audit(json.loads(args.input.read_text(encoding="utf-8")))
    rendered = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
