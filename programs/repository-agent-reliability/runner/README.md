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

`replay.py` performs **source-exact no-model replay** for committed `generic-v1`
candidate evidence.

Generation provenance remains frozen in the evidence directory, while deterministic
verification is reproduced from the run's recorded `source_commit`. Replay creates a
temporary detached Git worktree at that commit and invokes that commit's own
`model_trial.py` with the frozen raw response through the mock provider. No model
inference occurs.

The replay verifies:

- raw model-response SHA-256 and byte count;
- committed candidate artifact identity;
- reconstruction and structural admission of the candidate;
- task context, prompt, and output-protocol hashes;
- exact source commit, engine blob, and model-trial blob;
- deterministic re-execution of public checks and the qualified task verifier under
  the historical evaluator implementation;
- identical evaluation-record hash, final verdict, trusted-boundary result, and
  false-green classification.

The current HEAD evaluator is deliberately **not** required to match the historical
runner. This allows the evaluator to evolve without making old evidence unreplayable.

`replay_check.py` pins both an historical `VERIFIED_PASS` (AP-002) and an historical
false-green `VERIFIED_FAIL` (AP-003) as source-exact replay regression controls.

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

## Public validation as an acceptance gate

A candidate cannot receive `VERIFIED_PASS` when the configured public validation fails.

Verdict precedence is:

1. trusted-boundary violation => `HOLD`;
2. public validation failure => `VERIFIED_FAIL`;
3. otherwise use the qualified verifier result.

`self_check.py` includes a regression case where the AP-003 reference candidate passes
the qualified verifier while public validation is deliberately forced to fail. The
expected final verdict is `VERIFIED_FAIL`. Source-exact replay separately proves that
historical evidence remains replayable under the evaluator version recorded at the
original run.
