# Systemia integration handoff

The Lab-side local experiment is implemented in [durable/](durable/README.md).
It is ready for technical review and adapter mapping. A joint Systemia/live-agent
evaluation has not yet occurred, so no percentage of overall collaboration
completion is claimed.

## Jesse's questions and the current evidence

| Question | Completed Lab work | Remaining joint work |
| --- | --- | --- |
| Can evidence be authenticated independently? | Provider-issued Ed25519 receipts, fresh signed observations, public-key verifier, signed closing manifest and separate SQL read | Agree on Systemia's authoritative provider, key ownership and evidence export |
| Does state survive a process failure? | Actual kills before commit and after commit/before acknowledgement; new-process reconciliation and same-key retry | Map those boundaries onto the isolated Systemia workflow |
| Do concurrent retries duplicate an effect? | Three eight-worker same-key rounds and one eight-worker payload-conflict round | Agree whether the real adapter's concurrency and idempotency guarantees match this protocol |
| How does a live agent respond? | Executable bounded workflow adapter and nine scripted behavior controls | Supply the workflow entry point, model/configuration, credentials if needed and agreed run budget; execute and publish actual attempts |

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

1. Identify one isolated workflow entry point and its intended provider guarantees.
2. Map it to the [implemented adapter contract](durable/adapter_contract.json),
   or document the minimal change needed for a persistent workflow.
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
