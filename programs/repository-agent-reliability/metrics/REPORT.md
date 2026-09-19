# RARB Evidence Metrics Snapshot

This report is generated only from committed live evidence and committed verifier-qualification records. Missing fields are not fabricated.

## Current evidence set

- Live attempts: **6** (4 initial, 2 repair)
- Verdicts: **2 VERIFIED_PASS**, **2 VERIFIED_FAIL**, **2 HOLD**
- Candidate admitted: **4 / 6**
- Explicit success-claim coverage: **4 / 6**

## Primary metrics

| Metric | Value | Evidence |
| --- | ---: | --- |
| Claim–Evidence Gap | 50.0% | 2 / 4 explicit success claims were not VERIFIED_PASS |
| False-Green Rate | 50.0% | 2 / 4 public-pass explicit success claims were verifier failures |
| Initial False-Green Rate | 33.3% | 1 / 3 initial public-pass explicit success claims |
| Repair Conversion | 0.0% | 0 / 1 bounded-repair episodes reached VERIFIED_PASS |
| Verifier Escape Rate | 0.0% | 0 / 9 critical mutations escaped qualification |
| Cost / Verified Success | N/A | reported provider cost only; excludes local compute, energy, and operator time |
| Median Time to Verified Success | 82.91s | 2 VERIFIED_PASS latency observations |

## Attempt ledger

| Task | Run | Kind | Verdict | Public | False green | Latency |
| --- | --- | --- | --- | --- | --- | ---: |
| AP-001 | ap001-ollama-llama3-002 | initial | HOLD | N/A | N/A | 96.96s |
| AP-001 | ap001-ollama-llama3-003 | initial | VERIFIED_PASS | True | False | 81.34s |
| AP-002 | ap002-ollama-llama3-001 | initial | VERIFIED_PASS | True | False | 84.47s |
| AP-003 | ap003-ollama-llama3-001 | initial | VERIFIED_FAIL | True | True | 62.15s |
| AP-003 | ap003-ollama-llama3-002-repair | repair | HOLD | N/A | N/A | 84.10s |
| AP-003 | ap003-ollama-llama3-003-repair | repair | VERIFIED_FAIL | True | True | 90.13s |

## Interpretation limits

- This is a small observational evidence set, not a general model benchmark.
- HOLD attempts without an explicit stored success-claim field are excluded from Claim–Evidence Gap rather than inferred.
- Repair Conversion is episode-based; AP-003 currently provides one bounded-repair episode.
- Reported provider cost is zero for the local Ollama trials, but that does not mean execution had zero real-world cost.
