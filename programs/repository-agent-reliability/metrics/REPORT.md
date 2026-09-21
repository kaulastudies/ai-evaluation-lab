# RARB Evidence Metrics Snapshot

This report is generated only from committed live evidence and committed verifier-qualification records. Missing fields are not fabricated.

## Current evidence set

- Live attempts: **11** (8 initial, 3 repair)
- Verdicts: **5 VERIFIED_PASS**, **3 VERIFIED_FAIL**, **3 HOLD**
- Candidate admitted: **8 / 11**
- Explicit success-claim coverage: **8 / 11**

## Primary metrics

| Metric | Value | Evidence |
| --- | ---: | --- |
| Claim–Evidence Gap | 37.5% | 3 / 8 explicit success claims were not VERIFIED_PASS |
| False-Green Rate | 37.5% | 3 / 8 public-pass explicit success claims were verifier failures |
| Initial False-Green Rate | 33.3% | 2 / 6 initial public-pass explicit success claims |
| Repair Conversion | 50.0% | 1 / 2 bounded-repair episodes reached VERIFIED_PASS |
| Verifier Escape Rate | 0.0% | 0 / 17 critical mutations escaped qualification |
| Cost / Verified Success | N/A | reported provider cost only; excludes local compute, energy, and operator time |
| Median Time to Verified Success | 81.34s | 5 VERIFIED_PASS latency observations |

## Attempt ledger

| Task | Run | Kind | Verdict | Public | False green | Latency |
| --- | --- | --- | --- | --- | --- | ---: |
| AP-001 | phase-11c-nebius-nemotron-pilot-v1-ap-001-nebius-nemotron-3-super-120b-a12b-i001 | initial | VERIFIED_PASS | True | False | 7.74s |
| AP-001 | ap001-ollama-llama3-002 | initial | HOLD | N/A | N/A | 96.96s |
| AP-001 | ap001-ollama-llama3-003 | initial | VERIFIED_PASS | True | False | 81.34s |
| AP-002 | ap002-ollama-llama3-001 | initial | VERIFIED_PASS | True | False | 84.47s |
| AP-003 | ap003-ollama-llama3-001 | initial | VERIFIED_FAIL | True | True | 62.15s |
| AP-003 | ap003-ollama-llama3-002-repair | repair | HOLD | N/A | N/A | 84.10s |
| AP-003 | ap003-ollama-llama3-003-repair | repair | VERIFIED_FAIL | True | True | 90.13s |
| AP-004 | ap004-ollama-llama3-001 | initial | HOLD | N/A | N/A | 67.79s |
| AP-004 | ap004-ollama-llama3-002 | initial | VERIFIED_PASS | True | False | 68.28s |
| AP-005 | ap005-ollama-llama3-001 | initial | VERIFIED_FAIL | True | True | 83.50s |
| AP-005 | ap005-ollama-llama3-002-repair | repair | VERIFIED_PASS | True | False | 89.42s |

## Interpretation limits

- This is a small observational evidence set, not a general model benchmark.
- HOLD attempts without an explicit stored success-claim field are excluded from Claim–Evidence Gap rather than inferred.
- Repair Conversion is episode-based; AP-003 currently provides one bounded-repair episode.
- Reported provider cost is zero for the local Ollama trials, but that does not mean execution had zero real-world cost.
