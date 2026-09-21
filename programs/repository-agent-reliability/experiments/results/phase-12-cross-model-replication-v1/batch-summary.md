# phase-12-cross-model-replication-v1 Report

Status: **COMPLETE**

## Counts

- Planned initial attempts: **30**
- Observed initial attempts: **30**
- Repair attempts: **0**
- Initial verdicts: **29 VERIFIED_PASS / 1 VERIFIED_FAIL / 0 HOLD**
- AP-001 Section 9 sequences: **0**

## Rates

- Initial verified-pass rate: 96.7% (95% Wilson CI 83.3%–99.4%)
- Initial false-green rate: 0.0% (95% Wilson CI 0.0%–11.7%)
- Repair conversion: N/A

## Claim boundary

- This preregistration creates no model-performance evidence; live outputs become evidence only after the fixed batch completes, every artifact is audited and source-exactly replayed, and promotion is explicit.
- The 30 new initial attempts are distinct observations and do not rerun, replace, pool with, or rewrite any frozen Phase 11 attempt.
- All three configurations must run from one committed evaluator source with the same AP-001 task version, prompt construction, temperature, output protocol, verifier, and repair policy.
- Every observed HOLD, VERIFIED_FAIL, failed repair, and VERIFIED_PASS must be retained; the batch cannot stop early because a desired outcome appears.
- A completed one-task, three-configuration matrix supports only bounded AP-001 configuration-level comparisons, not general coding-agent, production-scale, or provider-wide performance claims.
- The AP-001 Section 9 gap closes only if a new committed source-exact sequence naturally contains public-test pass, qualified-verifier rejection, bounded repair, VERIFIED_PASS, and successful no-model replay.

## Configuration-level results

### ollama-llama3-latest

- Provider/model: `ollama` / `llama3:latest`
- Initial attempts: **10**
- Initial verified-pass rate: 90.0% (95% Wilson CI 59.6%–98.2%)
- Initial false-green rate: 0.0% (95% Wilson CI 0.0%–29.9%)
- Initial HOLD rate: 0.0% (95% Wilson CI 0.0%–27.8%)
- Repair conversion: N/A
- Median recorded generation latency: 13407.5 ms

### ollama-qwen2-5-coder-7b

- Provider/model: `ollama` / `qwen2.5-coder:7b`
- Initial attempts: **10**
- Initial verified-pass rate: 100.0% (95% Wilson CI 72.2%–100.0%)
- Initial false-green rate: 0.0% (95% Wilson CI 0.0%–27.8%)
- Initial HOLD rate: 0.0% (95% Wilson CI 0.0%–27.8%)
- Repair conversion: N/A
- Median recorded generation latency: 20392.5 ms

### nebius-nemotron-3-super-120b-a12b

- Provider/model: `nebius` / `nvidia/nemotron-3-super-120b-a12b`
- Initial attempts: **10**
- Initial verified-pass rate: 100.0% (95% Wilson CI 72.2%–100.0%)
- Initial false-green rate: 0.0% (95% Wilson CI 0.0%–27.8%)
- Initial HOLD rate: 0.0% (95% Wilson CI 0.0%–27.8%)
- Repair conversion: N/A
- Median recorded generation latency: 4869.5 ms

