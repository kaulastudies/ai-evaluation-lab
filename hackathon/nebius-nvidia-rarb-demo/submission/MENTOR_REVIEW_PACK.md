# Research review pack for Prof. Nithya Ravi Kumar

Prepared by the ProofGate project team on October 29, 2026.

**Purpose:** give Prof. Nithya Ravi Kumar a substantive role in reviewing the study, the verifier and the public claims. This document is prepared for her review; it is not authored or approved by her. All review decisions are pending.

## 1. Methodology and next-study design

The current evidence covers five synthetic repository tasks. Phase 12 fixes AP-001, three configurations and ten trials per configuration. It records 29 passes out of 30 and 30 matching historical replays. The Nemotron configuration passed ten of ten trials on that task.

### Decisions requested

- Is the task contract sufficiently precise to support each pass/fail decision?
- Are comparisons limited to the exact model, prompt, provider, task and settings that were run?
- Which task characteristics are missing: stateful behavior, multi-file changes, dependency interaction, ambiguous requirements, or external effects?
- What additional evidence would be needed before recommending the system for an engineering workflow?

### Proposed next study

Freeze two additional repository-task contracts before collecting model outcomes. Select different failure classes, qualify each verifier using reference and faulty controls, and preregister the model configurations and a fixed trial count. Separate initial attempts from repair attempts. Retain every PASS, FAIL and HOLD; record request timing, token usage and incomplete cost fields. Keep prompts and generation settings alongside each result.

**Deliverable:** a one-page assessment identifying design weaknesses, one prioritized task expansion and the evidence needed to address it. The task selection and trial budget remain subject to review; no new study results are claimed.

## 2. Verifier qualification and held-out challenge

Start with the browser demo's six AP-005 controls: the reference, known-bad implementation and four mutations. All six pass the public test; the independent verifier accepts the reference and rejects the five faulty controls. These fixed cases establish sensitivity to the supplied faults, not completeness.

The following cases are **proposed tests**, not executed results:

| Challenge | Behavior to preserve | Potential weakness to inspect |
| --- | --- | --- |
| Duplicate identifiers with distinct values | Row count, order and distinct records | Deduplication hidden by otherwise correct values |
| `0`, `False` and `None` in separate records | Value and type distinctions required by the contract | Truthiness-based defaulting or numeric coercion |
| Absent note, empty note and explicit null | Contract-defined distinctions between optional-field states | Normalization that collapses distinct states |
| Interleaved active and inactive records | Required record inclusion and ordering | Filtering that silently drops valid records |
| Repeated calls on the same input | Stable output without mutating source objects | In-place edits that affect later calls |
| Empty input and a single record | Boundary behavior specified by the contract | Assumptions that only hold for multi-row examples |

Before implementing any case, compare its expected behavior with the frozen task contract. If the contract does not specify it, record the ambiguity instead of inventing a failure condition. Keep accepted held-out cases out of model prompts. Record reference, known-bad and mutation outcomes separately from model trials.

**Deliverable:** a reviewed challenge matrix with accepted cases, rejected cases and reasons; then a separate execution report after implementation. No outcomes should be entered before execution.

## 3. Claim-to-evidence audit

| Public claim | Evidence to inspect | Required limit |
| --- | --- | --- |
| 52 attempts: 44 PASS, 5 FAIL, 3 HOLD | Canonical RARB ledger and generated `evidence.json` | Aggregate across the published task/provider records |
| Five qualified verifiers, zero critical mutation escapes out of 17 | Qualification artifacts and controls | Only these supplied mutations; no claim of universal bug detection |
| Nemotron Phase 12: ten of ten AP-001 passes | Nebius generation records, manifests and gate reports | One task and one fixed configuration; not a model ranking |
| AP-005 false-green repaired successfully | Parent failure, bounded diagnostics and child repair artifacts | Archived repair is Ollama, not Nemotron |
| Browser checks execute Python now | Exported browser report, candidate and verifier hashes | Current bundled verifier, not full historical replay or new inference |
| Local source-exact replay reproduces the verdict | Replay output and evaluator commit | Reuses recorded model output; does not generate a new candidate |
| New Nemotron repair action is implemented | `serve.py`, repair runner and transport tests | Live-service result still pending a configured key |

Read the [judge instructions](JUDGE_TESTING.md), [submission draft](DEVPOST_DRAFT.md), [canonical evidence brief](../../../programs/repository-agent-reliability/demo/EVIDENCE_BRIEF.md) and [recorded team roles](../TEAM.md). For each claim, record supported, needs revision, or unsupported, plus the exact artifact inspected and the reason.

**Deliverable:** an annotated claim audit. The reviewer should explicitly check attribution, missing observations and the distinction between a result and a planned experiment.

## 4. Demonstration and product review

1. Open the public demo without an account or API key.
2. Execute the false-green and identify the difference between public tests and the independent verdict.
3. Execute the archived repair and explain what changed without implying a new model call.
4. Execute the zero mutation and the six-control suite; inspect the failed gates.
5. Execute the archived Nemotron candidate and locate its provider and source evidence.
6. Read the local runtime instructions and distinguish new generation, bounded repair and historical replay.

Record unclear labels, unsupported statements and missing reproducibility steps. Prioritize corrections that would change a judge's understanding of what actually ran.

**Deliverable:** a short review with the three most important corrections and a recommendation to proceed, revise, or collect more evidence. This is a requested review, not a completed sign-off.

## Feedback form

- Reviewer: Prof. Nithya Ravi Kumar
- Review date: pending
- Artifacts and commit inspected: pending
- Methodology findings: pending
- Verifier coverage findings: pending
- Claims to correct: pending
- Demo or reproducibility issues: pending
- Proposed next experiment: pending
- Recommendation and reasons: pending

Rama Chandra will record actual feedback and resulting changes with their source and date. The contributor record will be updated to reflect work completed, with no backdated review or approval.
