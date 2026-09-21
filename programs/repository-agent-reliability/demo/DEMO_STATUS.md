# RARB Demo Status

**Overall: GREEN**

- Generated evidence artifacts match committed evidence: **True**

## Validation checks

- runner_self_check: **PASS**
- source_exact_replay: **PASS**
- source_exact_repair_replay: **PASS**
- metrics_check: **PASS**
- demo_evidence_check: **PASS**
- phase11b_batch_check: **PASS**
- phase11b_evidence_check: **PASS**
- phase11c_nebius_evidence_check: **PASS**

## Evidence snapshot

- Attempts: **21**
- Verdicts: **14 VERIFIED_PASS / 4 VERIFIED_FAIL / 3 HOLD**
- Qualified tasks: **5**
- Critical verifier mutation escapes: **0 / 17**
- Claim-Evidence Gap: **22.2%**
- False-Green Rate: **17.6%**
- Repair Conversion: **50.0%**

## Evidence boundary

- The original AP-001 Section 9 sequence as written, including a successful repair conversion within AP-001 itself.
- Repeated cross-model and cross-provider benchmark evidence with sample sizes sufficient for general performance claims.
- Production-scale runtime evidence, including repeated throughput, reliability, and complete economic-cost measurement.

The status file is a compact demo index. Detailed evidence remains in `metrics/REPORT.md`, `demo/EVIDENCE_BRIEF.md`, and the frozen task evidence directories.
