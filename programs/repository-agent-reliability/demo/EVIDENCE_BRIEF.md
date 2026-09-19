# RARB Demo Evidence Brief

> Verify the evaluation before trusting the verdict.

## What RARB does

RARB treats the coding agent as the system under test. A patch is not accepted because the model says it is done or because public tests happen to pass. The task verifier is qualified first, then the candidate is scored against the frozen contract, and the resulting evidence can be replayed without rerunning model inference.

## Current evidence snapshot

- **8** committed live attempts
- **3 VERIFIED_PASS / 2 VERIFIED_FAIL / 3 HOLD**
- **5** qualified tasks
- **0 / 17** critical verifier mutations escaped
- Claim-Evidence Gap: **40.0%**
- False-Green Rate: **40.0%**
- Initial False-Green Rate: **25.0%**
- Repair Conversion: **0.0%**
- Median recorded generation latency among verified successes: **81.34s**

## The strongest live example: AP-003

1. The initial candidate passed public tests.
2. The qualified verifier rejected it on idempotency gates.
3. RARB classified the run as `VERIFIED_FAIL` and `false_green=true`.
4. Only bounded failed-gate evidence was exposed for repair.
5. Repair attempt 1 was rejected at admission and recorded as `HOLD`.
6. Repair attempt 2 was admitted, again passed public tests, and still failed the qualified verifier.
7. The repair budget was exhausted and the terminal failure was frozen instead of silently rerun.
8. Both repair outcomes are source-exact replayable without model inference.

That is the product behavior: **RARB measures whether a patch deserves to ship; it does not manufacture a passing result.**

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

## Demonstrated

- Verifier qualification with reference, known-bad, and critical mutation controls.
- Public-test false-green detection under a qualified verifier.
- Trusted-boundary checks and deterministic evaluation records.
- Bounded evidence-guided repair with an explicit attempt budget.
- Source-exact no-model replay across historical evaluator versions, including admission HOLD, VERIFIED_PASS, VERIFIED_FAIL, repair HOLD, and terminal repair failure.
- Separately versioned initial-output protocols without rewriting the frozen earlier HOLD.
- Evidence-derived metrics without fabricating missing fields.

## Not yet demonstrated

- A successful bounded repair conversion from VERIFIED_FAIL to VERIFIED_PASS.
- Repeated multi-model or statistically meaningful benchmark performance.
- AP-005 live task evidence.
- Nebius/NVIDIA production-runtime evidence.

## Evidence boundary

These numbers describe the committed RARB evidence set only. They are not claims about general coding-agent performance. The AP-004 v1 HOLD and v2 VERIFIED_PASS are separate observed attempts; this evidence does not by itself establish that the protocol change caused the different outcome. Local Ollama provider billing is reported as zero, but economic execution cost is unmetered and therefore Cost / Verified Success remains N/A.
