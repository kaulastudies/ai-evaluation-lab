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

## Bounded evidence-guided repair

`repair.py` implements the RARB repair protocol for a committed `VERIFIED_FAIL`
attempt.

A repair prompt may contain only the task brief, the failed candidate, public tests,
the writable candidate path, failed gate IDs, and bounded diagnostics. It does not load
or expose verifier source, qualification controls, mutations, or the reference
solution.

Repair records retain the parent evaluation-record hash and parent candidate hash,
record the bounded-evidence hash, run the replacement candidate through the same
structural admission and qualified-verifier path, and emit `repair_conversion=true`
only when a parent `VERIFIED_FAIL` becomes `VERIFIED_PASS`.

`repair_check.py` uses the AP-003 false-green evidence as a deterministic regression
control. Its mock response is supplied out-of-band to exercise the repair machinery;
it is not included in the repair prompt.

## Strict repair-output protocol v2

`repair.py` supports `strict-code-only-v2` for a bounded repair retry after an otherwise
valid repair response is rejected for output formatting.

Version 2 does not add verifier evidence or broaden model context. It strengthens only
the machine-output contract. The raw model response must begin with the configured
top-level class, contain zero backticks, contain no Markdown/prose prefix, and be a
complete Python file. These conditions are enforced before candidate unwrapping and
structural admission.

A format retry remains a separate model attempt with its own source commit, prompt hash,
response hash, admission result, and final verdict. The earlier `HOLD` remains immutable
evidence and is never rewritten or normalized into a candidate.
