# Production-relevant receiver evaluation: proposed scope

12 November 2026 · Status: **INITIAL PROPOSAL / PUBLIC SCENARIO NOW SELECTED**

**Update:** the selected starting point is Harmonic's public `examples/raw-vs-governed/`, API contract and preserved V114 examination. The completed [initial scope assessment](HARMONIC_SCOPE_ASSESSMENT.md) records fresh reproduction of existing public checks and distinguishes dispatch gating, receiver enforcement and production limits. The proposal below is retained as preselection context; its awaiting-scenario entries are historical, not current requests. No additional tests or private access are required for that initial assessment.

The original proposal below defines a production-facing evaluation contract for **one existing synthetic scenario**. It adds no tests, execution results or production assurance claim. At the time of the proposal, no external scenario had been selected; the update above supersedes that intake status.

Existing coverage: [evidence map at a fixed revision](https://github.com/kaulastudies/ai-evaluation-lab/blob/5723a2e20539eafc0145d5bb2c52e5454d83535b/examples/authority-lifecycle/EVIDENCE_MAP.md). The A, R and U references below refer to that map.

## Decision the review should support

Can an independent evaluator establish whether the selected receiver respects the agreed authority at the consequential commit point, preserves authorized work after unrelated changes, and accurately distinguishes confirmed, failed and unresolved outcomes?

The scenario should represent a real operational boundary. Its production applicability depends on documented equivalence of the authority path, queue/retry behavior, commit mechanism and observation path. Each difference remains an explicit limit.

## Minimum intake

An existing scenario description plus its retained evidence is sufficient to begin an asynchronous scope review. The following details can be established from that material or resolved as questions:

| Needed detail | What must be identified | Current status |
| --- | --- | --- |
| Scenario and operation | Scenario ID/revision; immutable request/payload; actor, resource and intended effect; operation and idempotency identifiers | Awaiting scenario |
| System boundary | Authority owner, dispatcher, queue, receiver, delegates and final consequential write; who controls each | Awaiting interface description |
| Authority semantics | Which authority version governs commit; revocation's effective point; treatment of queued, delegated and already committed actions | Must be agreed |
| Outcome evidence | Read-only receiver observation, authoritative event stream or other effect evidence; provenance, coverage and access limits | Awaiting retained evidence |
| Reproduction envelope | Versions/configuration, synthetic environment, permitted actions, observation window and stopping conditions | Scope review only |

Credentials, signing keys and production secrets are not needed for this initial review. Private material stays in an agreed private workspace; this public note contains only the proposed method.

## Review questions and acceptance conditions

These are candidate criteria to agree against the selected scenario, not claims that the current suites already cover an external system.

| Boundary | Proposed acceptance condition | Existing material to reuse |
| --- | --- | --- |
| Standing-preserving change | The same queued request reaches its intended commit under agreed delivery conditions after a change that leaves its authority intact. Preserve the original grant and payload without fresh authorization; report delay or suppression separately. | A1, A2; global-invalidation negative control |
| Revocation before commitment | If revocation is effective before the defined commit point, the selected action produces no consequential effect within the agreed observation coverage. A denial response alone is insufficient evidence. | R1, R2; enqueue-only negative control |
| Stale or delegated authority | Document whether cached grants, old versions, delegation and retry paths reach the same enforcement point. Identify any path whose outcome cannot be independently observed. | R1 delegation control; external behavior remains untested |
| Duplicate or ambiguous delivery | Correlate retries to the same operation and immutable payload. Check effect cardinality under the agreed idempotency semantics; retain unresolved status until sufficient evidence is available. | U1, U2; duplicate-delivery case |
| Ordering and partial failure | Distinguish revocation effective, dispatch, receipt and commit events. Use causal/transaction ordering or an agreed ordering mechanism; account for clock uncertainty. If order is indeterminate, leave that ordering claim unresolved. | R2 and U2 as local boundary examples |
| Outcome claims | Assess a workflow's success claim using evidence it actually possessed at that time. Record later evaluator knowledge separately. | U3: safe uncertainty and unsupported-success controls |
| Recovery and containment | Identify retry, cancellation, reconciliation and compensation behavior separately. Record residual work and subsequent writes over the declared window; cancellation acknowledgement is not proof that all effects stopped. | Existing local retry/rollback cases; external cleanup remains untested |

Any grace period or bounded-staleness rule must be explicit before evaluation. Do not silently weaken the revocation condition to accommodate an observed result. Numeric latency, availability, load and recovery thresholds remain **unset** until the receiver's contract and intended use are known; existing counts are not production SLO estimates.

## Evidence preservation and independent review

1. Preserve received originals with scenario/revision identifiers and an inventory of hashes. Hashes bind bytes; they do not establish truth or completeness.
2. Work from copies. Keep redacted or normalized derivatives separate, with a mapping to their originals and the effect of omissions on reviewability.
3. Link each observation to its operation, receiver, authority version where available, and causal/event position. Distinguish workflow-visible responses from evaluator-only observations.
4. State who controls every evidence source. A separately read log controlled by the same provider is not automatically independent of that provider. Where effects cannot be observed independently, narrow the conclusion.
5. Keep conflicting and missing records. Absence of a row supports a no-effect conclusion only within justified coverage, freshness and observation bounds; silence or missing telemetry stays unresolved.

Report separate fields for **authority disposition**, **observed effect**, **evidence sufficiency**, and **justification of the workflow's claim**. A committed effect can coexist with an unjustified success claim; safe unresolved behavior can coexist with a committed effect.

## Bounded deliverable and next gate

The first deliverable is a short, non-executing assessment: interface/boundary map, event sequence, claim-to-evidence matrix, reusable controls, evidence gaps and a proposed acceptance contract. Review an existing scenario first; create no additional tests yet.

Before any later execution, agree the exact revision/environment, observable effect, authority semantics, permitted actions, limits and retained artifacts. If the available material cannot support an independent conclusion, report the gap rather than manufacturing a verdict.

Any later synthetic result applies only to the selected scenario and demonstrated boundary. Production assurance would require separately scoped evidence of deployment equivalence and relevant operational conditions. No live-system assessment or deployment approval is asserted by this proposal.
