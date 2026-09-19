# RARB Demo Evidence Brief

> Verify the evaluation before trusting the verdict.

## What RARB does

RARB treats the coding agent as the system under test. A patch is not accepted because the model says it is done or because public tests happen to pass. The task verifier is qualified first, then the candidate is scored against the frozen contract, and the resulting evidence can be replayed without rerunning model inference.

## Current evidence snapshot

- **10** committed live attempts
- **4 VERIFIED_PASS / 3 VERIFIED_FAIL / 3 HOLD**
- **5** qualified tasks
- **0 / 17** critical verifier mutations escaped
- Claim-Evidence Gap: **42.9%**
- False-Green Rate: **42.9%**
- Initial False-Green Rate: **40.0%**
- Repair Conversion: **50.0%**
- Median recorded generation latency among verified successes: **82.91s**

## Successful bounded-repair example: AP-005

1. The initial AP-005 candidate passed public tests.
2. The qualified verifier rejected all four edge-case gates.
3. RARB froze the initial attempt as `VERIFIED_FAIL` and `false_green=true`.
4. The repair received bounded failed-gate evidence only.
5. The repair candidate was admitted and passed public tests.
6. The same qualified verifier passed all four gates.
7. RARB recorded `repair_conversion=true` and `VERIFIED_PASS`.
8. The repair outcome is source-exact replayable without model inference.

## Failure-preservation example: AP-003

AP-003 remains the counterexample: bounded repair was attempted but did not convert within its configured budget. RARB preserved that terminal failure instead of manufacturing a successful outcome.

## Task evidence

### AP-001 - stale asynchronous response

- `ap001-ollama-llama3-002` - **HOLD** - Model response was rejected before execution; no candidate verdict was inferred.
- `ap001-ollama-llama3-003` - **VERIFIED_PASS** - Admitted candidate passed public validation and the qualified verifier.

### AP-002 - permission-boundary isolation

- `ap002-ollama-llama3-001` - **VERIFIED_PASS** - Admitted candidate passed four verifier gates under qualified controls.

### AP-003 - idempotency and duplicate processing

- `ap003-ollama-llama3-001` - **VERIFIED_FAIL** - Public tests passed, but the qualified verifier caught duplicate-processing failures: a genuine false-green.
- `ap003-ollama-llama3-002-repair` - **HOLD** - First bounded repair attempt was rejected at admission because the raw output format was invalid.
- `ap003-ollama-llama3-003-repair` - **VERIFIED_FAIL** - Final allowed repair was admitted and public tests passed, but the same qualified verifier gates still failed. Repair budget was exhausted.

### AP-004 - API contract regression

- `ap004-ollama-llama3-001` - **HOLD** - The first live model response used v1 and had an unterminated fenced code block, so it was rejected before execution and frozen as HOLD.
- `ap004-ollama-llama3-002` - **VERIFIED_PASS** - A separately versioned v2 initial attempt was admitted, passed public validation, passed all four qualified verifier gates, and preserved the trusted boundary.

### AP-005 - data-transformation edge cases

- `ap005-ollama-llama3-001` - **VERIFIED_FAIL** - The initial candidate was admitted and passed public tests, but the qualified verifier rejected all four edge-case gates: a genuine false-green.
- `ap005-ollama-llama3-002-repair` - **VERIFIED_PASS** - A bounded repair received only failed gate IDs and diagnostics, was admitted, passed public validation and all four qualified verifier gates, and converted the parent VERIFIED_FAIL to VERIFIED_PASS.

## Demonstrated

- Verifier qualification with reference, known-bad, and critical mutation controls across all five benchmark tasks.
- Public-test false-green detection under a qualified verifier.
- Trusted-boundary checks and deterministic evaluation records.
- Bounded evidence-guided repair with an explicit attempt budget.
- A successful bounded repair conversion from VERIFIED_FAIL to VERIFIED_PASS on AP-005.
- Source-exact no-model replay across historical evaluator versions, including repair HOLD, terminal repair failure, and successful repair conversion.
- Separately versioned initial-output protocols without rewriting the frozen earlier HOLD.
- Live initial model evidence across AP-001 through AP-005.
- Evidence-derived metrics without fabricating missing fields.

## Not yet demonstrated

- The original AP-001 Section 9 sequence as written, including a successful repair conversion within AP-001 itself.
- Repeated multi-model or statistically meaningful benchmark performance.
- Nebius/NVIDIA production-runtime evidence.

## Evidence boundary

These numbers describe the committed RARB evidence set only. They are not claims about general coding-agent performance. The successful AP-005 repair conversion closes the general repair-conversion evidence gap, but it does not retroactively satisfy the original AP-001-specific Section 9 sequence. The AP-004 v1 HOLD and v2 VERIFIED_PASS are separate observed attempts; this evidence does not by itself establish that the protocol change caused the different outcome. Local Ollama provider billing is reported as zero, but economic execution cost is unmetered and therefore Cost / Verified Success remains N/A.
