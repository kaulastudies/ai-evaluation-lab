# RARB v0.1 Release Checklist

Release state: **MERGED AND CI-GREEN**

RARB v0.1 was merged through PR #13 at commit
`556ca9653aa6e6ea5de0778890b2efe098cff618`. This checklist records the completed
release gates without changing the frozen benchmark evidence.

## Evidence state

- 5 verifier-qualified benchmark tasks
- 10 committed live attempts
- 4 `VERIFIED_PASS` / 3 `VERIFIED_FAIL` / 3 `HOLD`
- 0 / 17 configured critical verifier mutation escapes
- Repair Conversion: 1 / 2 episodes (50%)
- AP-005 successful bounded repair is source-exact replayable
- AP-003 non-converting repair remains preserved

## Required pre-merge gates

- [x] repository working tree was clean before the release commit
- [x] `git diff --check` passed
- [x] all RARB Python sources compiled
- [x] generic runner self-check passed
- [x] source-exact initial replay passed
- [x] source-exact repair replay passed
- [x] output-protocol regression passed
- [x] metrics check passed
- [x] demo evidence check passed
- [x] one-command demo check passed
- [x] generated evidence matched committed evidence
- [x] no credential-like material was detected in the RARB change set
- [x] no private contractor/customer/project identifiers were detected in RARB assets
- [x] GitHub pull-request and post-merge `main` CI passed

The successful post-merge runs were `ci` run 31 and
`evaluation-operations-gates` run 17. Historical release evidence remains attached to
the merge commit and PR; these boxes are a status record, not newly generated evidence.

## Evidence boundaries that remain after v0.1

- the original AP-001 Section 9 sequence as written, including repair conversion within AP-001;
- repeated multi-model/statistically meaningful benchmark performance;
- Nebius/NVIDIA production-runtime evidence.

These boundaries are intentionally retained. They must not be rewritten as completed
until corresponding evidence exists.
