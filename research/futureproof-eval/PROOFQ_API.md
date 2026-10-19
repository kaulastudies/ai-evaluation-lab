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
- Only single-qubit `Ry(theta)` preparation and computational-basis measurements are supported.
- Wilson intervals provide **uncorrected screening flags**, not confirmatory statistical decisions or hardware certification.
- The service does not execute quantum circuits; it analyzes user-supplied counts.

## Next production gates

Move to authenticated service hosting, strict structured JSON schema, audit trail with consent and retention policy, per-client isolation, quotas, tests against actual simulator backends, calibrated significance levels and operational monitoring.
