"""Illustrative one-qubit Born-rule verifier; not a calibrated hypothesis test."""
import hashlib
import json
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class Evaluation:
    case_id: str
    passed: bool
    measured_probability: float
    reference_probability: float
    absolute_error: float
    tolerance: float
    evidence_sha256: str

def born_probability(theta_radians: float) -> float:
    if not isinstance(theta_radians, (int, float)) or not math.isfinite(theta_radians):
        raise ValueError("angle must be finite")
    return math.sin(theta_radians / 2) ** 2

def evaluate(case_id: str, theta_radians: float, ones: int, shots: int,
             tolerance: float = 0.1) -> Evaluation:
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("case_id is required")
    if type(ones) is not int or type(shots) is not int:
        raise TypeError("shot counts must be integers")
    if shots <= 0 or not 0 <= ones <= shots:
        raise ValueError("invalid shot counts")
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or not 0 <= tolerance <= 1:
        raise ValueError("invalid tolerance")
    ref = born_probability(theta_radians)
    observed = ones / shots
    error = abs(observed - ref)
    evidence = {"case_id": case_id, "theta_radians": theta_radians, "ones": ones,
                "shots": shots, "tolerance": tolerance, "reference_probability": ref,
                "measured_probability": observed}
    digest = hashlib.sha256(json.dumps(evidence, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()).hexdigest()
    return Evaluation(case_id, error <= tolerance, observed, ref, error, tolerance, digest)
