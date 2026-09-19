# RARB Demo Status

**Overall: GREEN**

- Generated evidence artifacts match committed evidence: **True**

## Validation checks

- runner_self_check: **PASS**
- source_exact_replay: **PASS**
- source_exact_repair_replay: **PASS**
- metrics_check: **PASS**
- demo_evidence_check: **PASS**

## Evidence snapshot

- Attempts: **6**
- Verdicts: **2 VERIFIED_PASS / 2 VERIFIED_FAIL / 2 HOLD**
- Qualified tasks: **4**
- Critical verifier mutation escapes: **0 / 13**
- Claim-Evidence Gap: **50.0%**
- False-Green Rate: **50.0%**
- Repair Conversion: **0.0%**

## Evidence boundary

- A successful bounded repair conversion from VERIFIED_FAIL to VERIFIED_PASS.
- Repeated multi-model or statistically meaningful benchmark performance.
- AP-004 and AP-005 live task evidence.
- Nebius/NVIDIA production-runtime evidence.

The status file is a compact demo index. Detailed evidence remains in `metrics/REPORT.md`, `demo/EVIDENCE_BRIEF.md`, and the frozen task evidence directories.
