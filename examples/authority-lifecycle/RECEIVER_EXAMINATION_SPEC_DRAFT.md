# Synthetic payment receiver: proposed examination specification

12 November 2026 · Version 0.1 · **DRAFT FOR AGREEMENT — NOT FROZEN — NOT EXECUTED**

Purpose: determine whether one agreed synthetic payment operation is governed by current authority at the receiver's commitment point, whether preserved standing permits continuation, and what can be established after an uncertain response.

This is a proposed examination contract following the [completed public evidence map](HARMONIC_FOUR_QUESTION_MAP.md). It contains no new implementation, tests or results. The candidate receiver interface and regression artifacts have not been inspected. No assertion about that receiver's behavior, production equivalence or independent reproducibility is made.

## 1. Target and disclosure agreement

The scope is one existing synthetic receiver, one exact operation and the existing evidence applicable to it. The operation is **not yet selected**: V114's refund fixture does not establish the candidate receiver's API or transaction semantics.

| Field to freeze | Required agreement | Current state |
| --- | --- | --- |
| Target identity | Receiver revision/digest, dependencies, runtime configuration, existing regression suite revision and reproduction command | Unspecified |
| Exact operation | Native action name; immutable request fields, actor/tenant, accounts or recipient, amount representation and currency if applicable; operation ID and idempotency-key scope | Unspecified |
| Authority source | Grant/mandate identity, issuer and trust basis, scope, versions, expiry, delegation if supported, and how the receiver acquires current authority | Unspecified |
| Interface | Existing submit, revoke/change and outcome-query interfaces; response meanings, errors and identity correlation | Unspecified; no endpoint names assumed |
| Consequence | Exact durable effect and accounting invariant; committed transaction boundary; whether settlement means only local synthetic state | Unspecified |
| Examination access | Which source, commands, retained artifacts and read-only outcome observations can be examined independently | Unspecified |
| Disclosure | What may be shared, with whom, where it may be retained, any redactions, and whether findings/artifacts may be published | Unagreed |

This public draft contains only proposed method and references to already public work. It does not authorize disclosure of candidate code, traces, identifiers or results. Target-specific material stays in the mutually agreed location under the agreed disclosure terms. Redactions and their effect on reviewability must be recorded.

## 2. Ordering and observation contract

Use operation identity **O**, an authority change's effective point **R**, and the receiver's durable commit point **C** as analytical labels, not assumed API fields.

- Agree what makes revocation effective and what establishes that it precedes or follows commitment. Receipt time or wall-clock timestamps alone are insufficient without the relevant ordering guarantees.
- For **R before C**, the proposed requirement is no committed effect under the revoked authority. Specify any different contractual semantics before freezing; do not reinterpret them after observing a result.
- For **C before R**, preserve the committed effect as historical fact. Revocation is not evidence of rollback. Reversal or compensation, if supported, is a separate operation and effect.
- If order cannot be established from available evidence, report the ordering question as unresolved.
- Define the observation window, pending-work closure, query consistency/freshness, crash/restart durability model, and the permitted retry/delivery schedule. No load, latency or availability target is implied.

A successful authorization decision, an execution permit, receiver acceptance, durable commitment and caller acknowledgment are separate observations. Agree which of them the existing interface exposes.

## 3. Proposed criteria and existing-evidence review

These are criteria for agreement, not claims that the cases exist or have passed. First identify matching existing regressions and retained artifacts; mark unavailable coverage explicitly. Additional cases require a later decision.

| ID | Condition to examine using existing evidence | Proposed acceptance criterion | Evidence needed |
| --- | --- | --- | --- |
| C1 — Authority and binding | One authorized operation; applicable receiptless, invalid-receipt or payload-change controls where supported | The defined receiver path checks the agreed authority and exact operation before the consequential write. Authorized execution produces the defined effect; an invalid request produces none. | Authority input/version and verification evidence correlated with O; actual receiver state and accounting invariant; path inventory for the claimed boundary. |
| C2 — Revocation ordering | The same pending O encounters effective revocation before commit; retain any existing commit-before-revocation control separately | R-before-C prevents commitment under revoked authority, including retries through the examined paths. C-before-R is reported as already committed, not retroactively prevented. | Evidence establishing R/C order and durable effect state. An upstream refusal alone does not establish receiver enforcement. |
| C3 — Preserved standing | A declared unrelated change occurs while O remains authorized | The same pending O, original authority grant and immutable payload can complete under the agreed delivery conditions, without a replacement grant. Fresh verification of unchanged authority is allowed. | Pre/post authority relationship, unchanged operation identity and payload, the unrelated change, and the resulting committed effect. An independent unchanged-authority trial is insufficient. |
| C4 — Commitment evidence | Existing successful, refused and relevant recovery cases | The reported effect matches the defined durable state and accounting invariant. A signature or HTTP response is not the sole proof of settlement. | Read-only state observation or an agreed authoritative outcome source, tied to O and the declared durability model. Provider-controlled evidence remains identified as such. |
| C5 — Ambiguous outcome | An existing interrupted/lost-response case, plus any available lookup-unavailable case | Caller claims stay within its evidence at that time. Unknown remains unknown until resolved. Recovery identifies the original O; permitted retries produce no additional payment effect under the agreed idempotency contract. | Caller-visible trace, evaluator observations kept separate, committed state, lookup results and their freshness, all attempts and cumulative effect cardinality. |
| C6 — Recovery closure | Existing retry, restart or reconciliation evidence relevant to C2/C5 | Recovered state and operation identity remain consistent; no prohibited later effect appears within the agreed coverage. Pending work is accounted for before concluding non-execution. | Existing recovery trace, durable state before/after where available, outstanding-work status and the bounded observation window. |

If retries, delegation, restart or reconciliation are unsupported or not observable, narrow the examination accordingly. Do not infer those capabilities from a field name or include them silently in a successful verdict. One payment may involve multiple ledger rows; freeze the actual accounting invariant rather than equating one row with one payment.

## 4. Evidence sufficiency and independence

Before freezing, inventory each artifact's original revision, source, collection method and SHA-256 digest. Preserve originals; retain derivatives and redaction lineage separately. Hashes bind bytes, not truth or completeness.

For each criterion identify whether the evaluator can execute the existing case, inspect the receiver's outcome independently of the caller, and establish the relevant ordering. A provider-supplied transcript supports document review; it is not an independent rerun. A separate read-only database connection improves observation separation but does not create an independent administrative trust domain.

For outcome classification:

- **Confirmed committed:** the agreed authoritative evidence establishes O's defined durable effect.
- **Confirmed non-execution:** evidence establishes no committed effect and closes or bounds possible later execution under the agreed contract. Absence from an incomplete/stale log is insufficient.
- **Unresolved:** neither conclusion is justified. Receipt verification, authorization and acknowledgment status remain separately reportable.

Record what the caller knew when it claimed success or failure. Later evaluator knowledge does not retroactively justify that claim. An uncertain response alone does not authorize a blind retry; the frozen operation and idempotency contract determine whether retry is safe.

## 5. Criteria freeze and verdict rules

Freeze only after both sides agree:

1. Exact receiver/operation/interface revisions and disclosure terms.
2. Authority semantics, R/C ordering mechanism, accounting invariant and durability/observation boundaries.
3. Which existing cases support C1–C6, what is independently executable or inspectable, and which claims remain outside scope.
4. Permitted actions, synthetic-only environment, execution limits, stopping conditions and evidence retention.
5. Per-criterion acceptance rules and any exclusions, before interpreting a subsequent examination's results.

No credentials, real payments or production access are part of this draft. Any later execution uses the agreed synthetic environment.

Record each criterion as supported, violated, unresolved or not examined, with the exact evidence and limitations. A required positive control that cannot complete prevents an overall supported finding; negative outcomes alone do not establish discrimination. An observed unauthorized committed effect defeats the corresponding enforcement criterion. Missing evidence is not a pass.

An overall **SUPPORTED FOR EXAMINED BOUNDARY** requires every in-scope criterion to be supported and the required positive controls to succeed. A demonstrated criterion violation yields **DEFEATED FOR EXAMINED BOUNDARY**; otherwise incomplete required evidence yields **UNRESOLVED**. State any narrower supported subclaims separately. No aggregate result implies deployment-wide or production assurance.

After freezing, changes to code, criteria, fixtures or configuration create a versioned successor/attempt with lineage. Preserve the prior record and explain the change; do not replace an inconvenient result.

## 6. Current handoff

**Prepared:** proposed criteria, evidence requirements, disclosure fields and freeze rules.

**Pending agreement:** the actual candidate interface/revision, disclosure boundary, existing regression inventory and independently observable outcome.

**Not performed:** candidate access or execution, new tests, receiver implementation, private-artifact publication or production validation.

The immediate next step is to agree the interface and disclosure boundaries, then map the existing receiver evidence to these proposed criteria. Any need for additional material or implementation is decided after that review.
