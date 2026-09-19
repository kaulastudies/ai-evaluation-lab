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

## Generic no-model replay

`replay.py` validates a committed `generic-v1` evidence directory without calling the
model provider again.

The replay verifies:

- raw model-response SHA-256 and byte count;
- candidate artifact identity;
- reconstruction of the admitted candidate from the stored raw response;
- structural admission decision and reason;
- generic engine and model-trial Git blobs against the run's recorded source commit;
- clean local runner files;
- deterministic re-execution of public checks and the qualified task verifier;
- identical evaluation-record hash, final verdict, trusted-boundary result, and
  false-green classification.

This keeps generation evidence separate from deterministic verification replay. The
model does not need to be available for replay.

`replay_check.py` pins the first committed AP-002 live trial as the regression control
for the generic replay layer.
