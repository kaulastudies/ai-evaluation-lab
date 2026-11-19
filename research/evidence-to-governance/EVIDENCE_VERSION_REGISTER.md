# RARB Evidence Version Register — status at 31 October 2026

**Purpose:** prevent mixing a superseded count, current evidence ledger, phase subsets, or in-progress security changes. This is a **documentary version register**, not an independently executed replay or cryptographic audit.

## Evidence versions

| Source / state | Evidence | Version interpretation |
| --- | --- | --- |
| [11 October self-published technical report](../../publications/verifying-the-verifier-2026.md) | 51 live attempts; 43 VERIFIED_PASS; 5 VERIFIED_FAIL; 3 HOLD | Historical snapshot; its references are pinned to [source commit 70da1933](https://github.com/kaulastudies/ai-evaluation-lab/commit/70da1933a9dd174109fcf012ef8e25703b979fd2). Not the latest total. |
| [Current evidence brief](../../programs/repository-agent-reliability/demo/EVIDENCE_BRIEF.md) | 52 live attempts; 44 VERIFIED_PASS; 5 VERIFIED_FAIL; 3 HOLD | Repository-reported current figure; source observed on [main commit 6049b684](https://github.com/kaulastudies/ai-evaluation-lab/commit/6049b684ea131d832718dc9e6061090b0431f470) on 31 October. |
| [Metrics snapshot](../../programs/repository-agent-reliability/metrics/REPORT.md) | 52 attempts, including 49 initial and 3 repair; 5/48 claim–evidence gap; 3/46 false greens; 0/17 configured mutation escapes | Ledger denominators are **specific**: do not interpret 3/46 as prevalence in all deployed AI code, or 0/17 as complete verification/security correctness. |
| [Main repository README](../../README.md) | Still states 51 attempts / 43 passes at observed main commit 6049b684 | **Known stale summary**, not a different live experiment; [open PR #41](https://github.com/kaulastudies/ai-evaluation-lab/pull/41) proposes the 52/44 correction. Do not state this is merged until verified. |
| [Phase 12 subset](../../programs/repository-agent-reliability/demo/EVIDENCE_BRIEF.md) | 30 AP-001 initial attempts across three fixed configurations; 29 passes, one failure; 30 no-model source-exact replays | **Included within**, not additional to, the 52 headline attempts. Single-task scope. |
| [Security remediation PR #34](https://github.com/kaulastudies/ai-evaluation-lab/pull/34) | Proposed isolation and security-regression changes; reported CI tests | **Open / unmerged** at document preparation. Not a completed independent audit or demonstration of security protections on main. |

### Snapshot pinning conventions

- This register's *documentation observation point* is main SHA **6049b684ea131d832718dc9e6061090b0431f470** on 31 October 2026.
- The historical October 11 publication explicitly cites **70da1933a9dd174109fcf012ef8e25703b979fd2** and should remain available rather than being silently rewritten.
- Commit SHA alone is **not** an artifact-content hash. Before human study launch, inventory the actual task-contract, candidate, verifier, output and case-packet SHA-256 values and re-run historic source-exact replay under the documented environment. That step has **not** been completed for this prospective protocol.
- Do not call the protocol preregistered until a complete rubric/packet set is finalized and publicly timestamped before reviewer recruitment.
- If PR #41 merges or the evidence ledger changes, regenerate and timestamp this register rather than editing old figures without version attribution.

## Pending verification tasks

- [ ] Merge or separately correct the stale README 51/43 summary after conflict review with PR #41.
- [ ] Identify and record the evidence commit that introduced the 52nd attempt, rather than inferring an exact creation date from file prose.
- [ ] Produce complete per-case provenance manifest with SHA-256 hashes for the pilot case packets.
- [ ] Independently re-run the source-exact replay entrypoint in the intended reviewer-study environment and record actual command, versions and results.
- [ ] Verify security PR #34's eventual merge/review state before any security assurance claim.

**Limits:** This register does not introduce new benchmark runs, increase the attempt total or imply third-party endorsement.
