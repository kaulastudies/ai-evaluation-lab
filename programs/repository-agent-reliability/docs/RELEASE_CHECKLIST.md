# RARB v0.1 Release Checklist

This checklist hardens the Repository Agent Reliability Program for review and merge
without changing the frozen benchmark evidence.

## Evidence state

- 5 verifier-qualified benchmark tasks
- 10 committed live attempts
- 4 `VERIFIED_PASS` / 3 `VERIFIED_FAIL` / 3 `HOLD`
- 0 / 17 configured critical verifier mutation escapes
- Repair Conversion: 1 / 2 episodes (50%)
- AP-005 successful bounded repair is source-exact replayable
- AP-003 non-converting repair remains preserved

## Required pre-merge gates

- [ ] repository working tree is clean before the release commit
- [ ] `git diff --check` passes
- [ ] all RARB Python sources compile
- [ ] generic runner self-check passes
- [ ] source-exact initial replay passes
- [ ] source-exact repair replay passes
- [ ] output-protocol regression passes
- [ ] metrics check passes
- [ ] demo evidence check passes
- [ ] one-command demo check passes
- [ ] generated evidence matches committed evidence
- [ ] no credential-like material is detected in the RARB change set
- [ ] no private contractor/customer/project identifiers are detected in RARB assets
- [ ] GitHub pull-request CI passes

## Evidence boundaries that remain after v0.1

- the original AP-001 Section 9 sequence as written, including repair conversion within AP-001;
- repeated multi-model/statistically meaningful benchmark performance;
- Nebius/NVIDIA production-runtime evidence.

These boundaries are intentionally retained. They must not be rewritten as completed
until corresponding evidence exists.
