# RARB v0.1 Release Checklist

Release state: **MERGED AND CI-GREEN**

RARB v0.1 was merged through PR #13 at commit
`556ca9653aa6e6ea5de0778890b2efe098cff618`. This checklist records the completed
release gates without changing the frozen benchmark evidence.

## v0.1 release evidence snapshot

- 5 verifier-qualified benchmark tasks
- 10 committed live attempts
- 4 `VERIFIED_PASS` / 3 `VERIFIED_FAIL` / 3 `HOLD`
- 0 / 17 configured critical verifier mutation escapes
- Repair Conversion: 1 / 2 episodes (50%)
- AP-005 successful bounded repair is source-exact replayable
- AP-003 non-converting repair remains preserved

## Post-release Phase 11C evidence expansion

- 11 committed live attempts
- 5 `VERIFIED_PASS` / 3 `VERIFIED_FAIL` / 3 `HOLD`
- one preregistered Nebius/NVIDIA AP-001 initial attempt
- provider/model: Nebius Token Factory / `nvidia/nemotron-3-super-120b-a12b`
- verdict: `VERIFIED_PASS`
- source-exact no-model replay: verified
- original AP-001 Section 9 repair sequence: still open

## Phase 12A preregistration

- 30 new AP-001 initial attempts fixed before execution
- 10 trials each for Ollama `llama3:latest`, Ollama `qwen2.5-coder:7b`, and
  Nebius/NVIDIA `nvidia/nemotron-3-super-120b-a12b`
- one source commit, task version, temperature, output protocol, verifier, and repair
  policy across all configurations
- full non-stopping batch required; split configuration execution rejected
- per-configuration Wilson intervals, repair outcomes, latency, token, and reported-cost
  coverage preregistered
- Phase 12 promoted initial attempts: **30**
- prior Phase 11 evidence remains frozen and unchanged

## Post-release Phase 11B evidence expansion

- 21 total committed live attempts after promotion
- 14 `VERIFIED_PASS` / 4 `VERIFIED_FAIL` / 3 `HOLD`
- fixed 10/10 planned AP-001 local Ollama initial trials completed
- Phase 11B outcome: 9 `VERIFIED_PASS` / 1 public-test `VERIFIED_FAIL`
- false-greens: 0 / 9 public-test passes
- repair attempts: 0, because no false-green was eligible
- all 10 attempts passed independent source-exact no-model replay
- dedicated Phase 11B evidence-integrity gate: green
- original AP-001 Section 9 repair sequence: still open

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
- general cross-task or provider-wide performance evidence beyond the bounded
  single-task Phase 12 matrix;
- production-scale runtime, reliability, and complete economic-cost evidence.

The narrower Nebius/NVIDIA connectivity and repository-task execution gap is closed by
the Phase 11C pilot. Phase 11B adds repeated evidence for one local configuration only.
Phase 12 adds bounded AP-001 evidence across three configurations with ten trials each.
It does not close the broader cross-task/provider-wide or production-scale boundaries
above.

## Phase 12 evidence promotion record

- [x] fixed 30-attempt batch completed without rerunning frozen attempts
- [x] source archive SHA-256, size, ZIP integrity, and secret scan verified
- [x] 30 manifests, evaluations, responses, candidates, logs, and replays audited
- [x] 30 source-exact no-model replays verified
- [x] single llama3 failure preserved without normalization
- [x] promotion hashes recorded in `promotion.json`
- [x] dedicated Phase 12 evidence-integrity gate added
- [x] aggregate and demo evidence updated from committed attempts
- [x] AP-001 Section 9 explicitly remains open
- [x] claims bounded to one task, three configurations, ten trials each
