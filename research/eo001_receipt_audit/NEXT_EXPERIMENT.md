# Systemia integration handoff

The local provider experiment is implemented in [durable/](durable/README.md).
The [Systemia mapping report](systemia/README.md) now records independent Lab
execution of Evercraft's deterministic candidate and the actual native recovery
CLI on isolated synthetic state. Source pins and full public evidence are retained.
A live Systemia agent evaluation and joint acceptance have not occurred.

Jesse supplied the native recovery entry point in
[issue #1705](https://github.com/jgaethle10/forge-operator/issues/1705), then added
the wire-compatible candidate in
[PR #1744](https://github.com/jgaethle10/forge-operator/pull/1744).
The Lab reviewed and ran commit `171a49b2a5cf81ff8922ebe2c69a182e91c1bd54`.
The [coordination issue text](systemia/COORDINATION_ISSUE_DRAFT.md) is prepared
but has not been published or accepted as joint scope.

## Jesse's questions and the current evidence

| Question | Completed Lab work | Remaining joint work |
| --- | --- | --- |
| Can evidence be authenticated independently? | Provider-issued Ed25519 receipts; pinned Evercraft candidate verifies them; native signed claims checked with a separate Lab serializer and verifier | Agree on authoritative provider truth, key ownership and evidence export |
| Does state survive a process failure? | Actual kills before commit and after commit/before acknowledgement; new-process reconciliation and same-key retry | Map those boundaries onto the isolated Systemia workflow |
| Do concurrent retries duplicate an effect? | Three eight-worker same-key rounds and one eight-worker payload-conflict round | Agree whether the real adapter's concurrency and idempotency guarantees match this protocol |
| How does a live agent respond? | Executable adapter, nine Lab scripted controls and four independently run Evercraft candidate cases; native recovery CLI tested in fourteen cases | Select an isolated real decision worker, model/configuration and run budget; retain raw proposals separately from guard decisions |

## Findings to review first

The original source-exact Forge study found that a deduplicated effect does not
by itself validate the response used to authorize fulfillment. The new suite
addresses that boundary in a separate Lab reference provider. It does not claim
that these changes have been implemented in Forge or Systemia.

The replay rule is explicit: an earlier receipt for the same durable operation
can be valid after a restart. A fresh authenticated query binds that receipt to
the current observation. Responses for a different operation, issuer, store or
request, or an old response reused against a new challenge, are rejected. An
ephemeral client run ID must not substitute for durable operation identity.

Signatures do not prove complete execution history. The suite checks its signed
closing snapshot against an evaluator-owned read-only database capture and full
request inventory. It still trusts the host and provider, and does not claim a
secure sandbox for an arbitrary candidate process.

## Proposed first joint run

1. Review the [completed contract mapping](systemia/README.md) and the native
   `recovery-hold` / `recovery-observe` boundary. A native signed observation is
   an attestation only; the tested CLI does not release the hold.
2. Agree the namespaces and trust anchors. The deterministic candidate already
   speaks the Lab wire contract, but native Systemia observations are a distinct
   protocol and must not be converted into Lab settlement proof or retry authority.
3. Agree on durable operation identity, trusted issuer, query freshness and the
   evidence retained independently of the agent. Identify candidate access to
   the key or provider store before executing untrusted code.
4. Freeze one model/configuration and a small complete attempt matrix covering
   ordinary success, lost acknowledgement, unresolved lookup, same-key retry,
   mismatched response and concurrent retries. Publish failures and incomplete
   attempts alongside successful recovery.
5. Independently score evidence validity, authorized behavior and actual task
   completion. Count fulfillment only if an independently observed delivery
   effect is added; current code measures authorization.

The added counterexample signs `completed` while the independent synthetic
oracle has zero effects and zero provider calls. Signature verification succeeds,
but the claim is contradicted and Systemia remains quarantined. This confirms the
documented trust boundary; it is not an observed bypass. A later guarded model
run must report the raw proposed action and any guard override separately, so a
safe final workflow does not hide an unsafe model proposal.

## Suggested ownership and stopping point

Evercraft would provide the isolated workflow and explain its guarantees. The
Lab would provide the fault protocol, evidence checks and reproducible report.
Both sides would agree the scope and criteria in an AI Evaluation Lab issue.
These are proposed responsibilities, not accepted commitments.

Stop after one fixed experiment and a joint review. Provider authentication,
single-host process durability and concurrency are implemented for the local
reference service. Production deployment, arbitrary-code containment, real
payments and model-performance conclusions need separate evidence. No paid
engagement or open-ended development commitment is implied.
