# Harmonic receiver boundary: four-question evidence map

12 November 2026 · Status: **PUBLIC EVIDENCE MAPPED / RECEIVER CONTRACT NOT YET AGREED**

This map answers the four scope questions using only the already examined public raw-versus-governed example, public API contract and preserved V114 execution-boundary material. It adds no implementation, tests or execution results. It carries forward the [initial assessment](HARMONIC_SCOPE_ASSESSMENT.md) and its [12 November reproduction record](harmonic-public-review/REPRODUCTION.json).

All Harmonic source references below are pinned to `3ce2c49139f65a87e4a5339c7e90560078922be4`. The previous run recorded **26 existing tests passed**, the HTTP demo's **1 raw / 0 governed revoked / 1 authorized control** consequence counts, and matching checksums for four V114 files. Those results are not reruns performed for this map.

## Evidence classes

- **Reproduced:** executed locally in the recorded public-source review. Unit-test stubs and actual loopback HTTP consequences remain distinguishable.
- **Historical:** the preserved V114 result and its inspectable frozen test. The private implementation needed to rerun V114 is absent. Checksum agreement establishes byte consistency against the supplied manifest, not independent attestation of execution.
- **Source observation:** a conclusion from inspected code, without a newly executed case.
- **Missing coverage:** the selected material does not establish the property. This is neither a failed test nor a claim that Harmonic's production system lacks the control.

## Four-question map

| Question | Reproduced behavior and source observations | Preserved V114 evidence | Missing coverage |
| --- | --- | --- | --- |
| **1. What authority does the receiver verify, and where does that decision bind the consequential write?** | The adapter requires refresh and receipt-verification callbacks, admits only the matching reference allow disposition, and controls whether `execute` is invoked ([P1]). Its helper checks packet/operation hashes and expiry, not a cryptographic signature. The HTTP sink validates the fictional payload and appends to memory; it does not require a receipt or reject revoked authority ([P2]). Thus the reproduced gate is before dispatch, not enforced by the receiver against all callers. | `constitutedExecutor` passes the receipt, trusted public key, expected service and exact execution payload to `verifyExecutorRequest`; the synthetic effect counter increments only after success ([H1]). The record reports one positive effect and no effects from six unauthorized cases ([H2]). | Independent execution of that verifier; independently authenticated current authority at commitment; durable receiver settlement; exhaustive effect-capable path coverage. Receipt verification and binding do not alone establish these properties. |
| **2. If authority changes before commitment, what establishes ordering and the receiver's response?** | The demo sets revocation before dispatch: raw execution records an unjustified effect; the adapter suppresses governed dispatch ([P3]). The existing `effect-time revalidation change forces a second evaluation and blocks changed authority` test observes two evaluations and zero executor calls using a stub evaluator ([P4]). | `expired_permit` rejects an already expired signed permit; `governance_refusal` prevents minting/forwarding; `payload_tamper_after_permit` rejects a changed payload ([H3]). These are separate frozen cases, not a concurrent revocation/commit experiment. | Effective revocation event versus durable commit order; change after the last refresh or after permit issuance; fencing/transaction semantics; treatment of an effect committed before revocation. No atomic revocation-to-commit conclusion follows from these cases. |
| **3. Can the same pending operation survive an unrelated change without fresh authorization?** | The HTTP control starts an independent active-authority trial and records one justified release ([P5]). The existing `explicit reference allow executes once after revalidation and binding verification` test records one invocation ([P6]). Both establish positive execution under unchanged authority. | `valid_current_permit_positive_control` records exactly one synthetic effect ([H4]). It supplies a current permitting governance fixture. | A controlled unrelated change between pending authorization and commitment, with the same operation, original grant and payload preserved. Neither positive control proves this stronger continuation property. |
| **4. When acknowledgment fails, what can be established about the effect, and what may the caller claim or retry?** | Source observation: the adapter catches an exception from the awaited executor and returns `executed: false` ([P7]). That value cannot by itself distinguish failure before effect from commitment followed by response failure. The existing unavailable/HTTP-error/invalid-JSON tests fail during evaluation and assert zero executor calls ([P8]); they do not inject lost acknowledgment after a receiver effect. | The frozen cases inspect an in-process effect counter and returned responses. They do not examine acknowledgment loss, restart, reconciliation or reuse of a still-valid permit ([H1], [H2]). | Durable operation identity and authoritative status lookup; recovery after uncertain acceptance; effect cardinality across retries; evidence available to the caller at claim time. Timeout or `executed: false` alone establishes neither no effect nor that another delivery is safe. |

## Reading the boundary correctly

The [public API contract][C1] separates a governance determination from downstream execution. Public reference `stable / allow` and `blocked / deny` retain their native meaning; they are not relabeled as sovereign-runtime determinations.

V114 supports the preserved **receipt-verification and execution-gating contract within its examined synthetic boundary**. Its fixture supplies governance dispositions and evidence identifiers, with persistence disabled; it is not a live governance decision or durable database settlement round trip. Its own [archive description][H5] preserves those limits. This map does not extend its historical result.

The Lab's SQLite receiver cases are separate Lab evidence. They are not Harmonic's receiver implementation, cannot fill a Harmonic evidence gap, and have not been composed with the public adapter or V114. Any separately supplied Harmonic receiver and regression evidence require their own revision, interface and scope assessment.

## Contract decisions after this map

The following are fields to agree before a subsequent examination, not already accepted criteria or requests for additional implementation:

| Decision | What the receiver contract must make explicit |
| --- | --- |
| Exact operation and authority | Immutable operation/payload identity, authority source and version, receipt trust model, and which routes can produce the effect. |
| Commitment and invalidation | Observable commit point; when revocation becomes effective; ordering evidence and treatment of already committed work. |
| Preserved standing | Which change is unrelated, why authority survives it, and how the same pending operation is recognized without replacement authorization. |
| Outcome and recovery | Evidence sufficient for confirmed commitment or confirmed non-execution; unresolved-state handling; permitted retries, idempotency and reconciliation. |

A later examination should record authority disposition, observed effect, evidence sufficiency and caller-claim justification separately. Missing outcome evidence remains unresolved; a historical permit or a signed receipt alone is not proof of commitment.

**Current completion:** the four questions are mapped against the selected public evidence. The next step is agreement on the exact receiver contract and acceptance criteria. No private access, new material or implementation is needed to complete this mapping, and no production assurance is asserted.

[P1]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/guard.js#L13-L84
[P2]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/run.js#L51-L68
[P3]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/run.js#L82-L100
[P4]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/guard.test.js#L83-L101
[P5]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/run.js#L101-L115
[P6]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/guard.test.js#L103-L111
[P7]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/guard.js#L82-L84
[P8]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/guard.test.js#L55-L67
[H1]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/evidence/examinations/v114-execution-boundary/V114_TEST.js#L94-L127
[H2]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/evidence/examinations/v114-execution-boundary/V114_RESULT.json
[H3]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/evidence/examinations/v114-execution-boundary/V114_TEST.js#L176-L225
[H4]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/evidence/examinations/v114-execution-boundary/V114_TEST.js#L166-L174
[H5]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/evidence/examinations/v114-execution-boundary/README.md
[C1]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/docs.html#L39-L66
