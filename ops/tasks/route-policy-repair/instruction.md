<!-- LAB-CANARY: RAMA-EVAL-LAB-ROUTE-POLICY-2026-09-V1 -->

# Repair the privacy-aware route policy

Repair `/app/router.py`.

The module exposes `route_batch(tasks)`. Each input task is a dictionary with:

- `id`: arbitrary string; IDs may repeat
- `privacy`: `public`, `confidential`, or `restricted`
- `complexity`: `low` or `high`
- `task_type`: arbitrary string
- `local_confidence`: number from 0 to 1
- `local_available`: boolean
- `cloud_available`: boolean

Return one decision for every input task in the same input order. Do not mutate the input list or task dictionaries.

Each decision must contain:

- `id`
- `position`
- `route`: `local`, `cloud`, or `blocked`
- `reason_code`
- `policy_version`: exactly `R1`

Apply these rules in this precedence order.

## Sensitive tasks

`confidential` and `restricted` tasks must never route to cloud.

Route to `local` only when local execution is available and `local_confidence >= 0.65`; otherwise return `blocked`.

## Deterministic task types

`arithmetic`, `regex`, and `schema_validation` route to `local` when local execution is available.

If local execution is unavailable, return `blocked`. Do not use cloud fallback.

## Other public tasks

Prefer `local` when it is available and `local_confidence >= 0.80`.

Otherwise use `cloud` when cloud is available.

If cloud is unavailable but local is available, use `local`.

If neither is available, return `blocked`.

## Reason codes

- `SENSITIVE_LOCAL`
- `SENSITIVE_BLOCKED`
- `DETERMINISTIC_LOCAL`
- `DETERMINISTIC_BLOCKED`
- `PUBLIC_LOCAL_CONFIDENT`
- `PUBLIC_CLOUD_ESCALATION`
- `PUBLIC_LOCAL_FALLBACK`
- `NO_PROVIDER`

The implementation must be deterministic.
