# ProofQ Verify API — local developer preview

A minimal JSON verification endpoint built on QProof Audit. This is a **loopback-only developer preview**, not a hosted production API.

## Start

From repository root with Python 3.12+:

```bash
python -m research.futureproof_eval.proofq_api
```

`GET http://127.0.0.1:8765/health`

`POST http://127.0.0.1:8765/v1/quantum/audit`

```bash
curl -X POST http://127.0.0.1:8765/v1/quantum/audit -H "Content-Type: application/json" -d '{"cases":[{"id":"zero","theta_radians":0,"ones":0,"shots":100}]}'
```

Reports include the case results and a canonical input SHA-256. Hashes are not digital signatures and do not prove a trusted data origin.

## Service limits and safety

- Loopback only; no remote exposure.
- No authentication, authorization, billing, rate limit or persistent storage; **do not deploy publicly**.
- Payload capped at 128 KiB, 1000 cases maximum, 100000 shots/case.
- The JSON root contains only `cases`; every case contains exactly `id`, `theta_radians`, `ones`, and `shots`. IDs are unique nonempty strings. Counts are integers, excluding booleans; angles must be finite representable numbers, excluding booleans.
- Duplicate JSON keys, NaN/Infinity constants, unexpected fields and invalid identities are rejected. Invalid scientific input returns HTTP 400.
- Only single-qubit `Ry(theta)` preparation and computational-basis measurements are supported.
- Wilson intervals provide **uncorrected screening flags**, not confirmatory statistical decisions or hardware certification.
- The service does not execute quantum circuits; it analyzes user-supplied counts.

## Next production gates

Move to authenticated service hosting, strict structured JSON schema, audit trail with consent and retention policy, per-client isolation, quotas, tests against actual simulator backends, calibrated significance levels and operational monitoring.

## Verification update — 30 October 2026

The current branch has 20 tests covering the core verifier, audit, HTTP error handling and an independent Qiskit 2.6.1 ideal-state reference at ten angles. This cross-check verifies the ideal probability calculation; it does not establish sampling calibration, hardware performance or production security.

Run the dependency-free core tests with:

```bash
python -m unittest research.futureproof_eval.test_verifier research.futureproof_eval.test_qproof_audit research.futureproof_eval.test_proofq_api -v
```

For the additional reference tests, install `qiskit==2.6.1`, then run `python -m unittest research.futureproof_eval.test_qiskit_reference -v`. CI runs both. The HTTP service still has no authentication, concurrency quota or slow-client deadline and must remain a local developer preview. A hosted pilot is not offered.
