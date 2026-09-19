# Generic RARB runner

This directory contains the task-generic execution layer for Repository Agent
Reliability Program tasks.

Each task supplies a small `runtime.json` adapter describing its candidate path,
model-visible files, public-test command, verifier path, qualification evidence,
trusted paths, and structural admission contract.

The generic runner owns:

- model-context construction;
- strict machine-output protocol;
- structural candidate admission;
- temporary workspace materialization;
- public validation;
- qualified-verifier execution;
- trusted-boundary snapshot comparison;
- deterministic evaluation records;
- `VERIFIED_PASS`, `VERIFIED_FAIL`, and `HOLD` semantics.

Task-specific verifier logic stays inside each task. AP-001's original frozen runner is
retained because its historical evidence and replay artifacts bind to that implementation.
New tasks should use this generic runner rather than copying AP-001's runner directory.
