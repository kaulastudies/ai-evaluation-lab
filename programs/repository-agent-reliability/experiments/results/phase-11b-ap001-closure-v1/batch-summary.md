# phase-11b-ap001-closure-v1 Report

Status: **COMPLETE**

## Counts

- Planned initial attempts: **10**
- Observed initial attempts: **10**
- Repair attempts: **0**
- Initial verdicts: **9 VERIFIED_PASS / 1 VERIFIED_FAIL / 0 HOLD**
- AP-001 Section 9 sequences: **0**

## Rates

- Initial verified-pass rate: 90.0% (95% Wilson CI 59.6%–98.2%)
- Initial false-green rate: 0.0% (95% Wilson CI 0.0%–29.9%)
- Repair conversion: N/A

## Claim boundary

- This plan does not create evidence until live execution completes and the staged artifacts are audited and committed.
- A successful mock regression is infrastructure validation, not live model evidence.
- One local Ollama configuration is not multi-model evidence.
- The AP-001 Section 9 gap closes only if a new committed source-exact sequence contains public-test pass, qualified-verifier rejection, bounded repair, VERIFIED_PASS, and successful no-model replay.
- Nebius/NVIDIA runtime evidence remains out of scope for this phase.
