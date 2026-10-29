# Proposed next experiment for joint review

## Question

Can one isolated Systemia workflow reject a misbound or replayed provider response
after acknowledgement loss, while preserving legitimate same-order recovery?
The current source-exact study supplies a reproducible starting point. Its
controller-origin labels are trusted annotations; the next experiment must make
the evidence origin available through an enforceable provider interface.

## First agree on the trust model

1. Decide whether the adapter promises a trusted response or must defend against
   substitution. The current negative controls deliberately cross that boundary.
2. Define the provider/order namespace across restarts. A previous response for
   the same durable operation can be valid recovery evidence; a response from a
   different operation that reuses the same display ID must not be accepted.
   A new process or evaluation run alone must not invalidate a legitimate receipt.
3. Specify who owns the provider state, request identity, evidence export and
   issuer key, and what a candidate can read or modify. Signing candidate-produced
   output after the fact does not prove provider execution.
4. Agree how complete observation coverage is established. A signed receipt alone
   does not prove absence of additional effects or omitted attempts.

## Bounded implementation proposal

- One synthetic workflow and one order. Reuse the existing Forge provider logic.
- Put the provider behind a separate local process and keep its evidence files
  and any signing key outside candidate-accessible paths. State the actual OS
  boundary; process separation alone is not a sandbox.
- Bind a provider-issued receipt to provider identity, durable operation ID,
  request fingerprint, receipt ID and settlement status. An evaluator-supplied
  challenge can bind an observation to a query without changing the durable
  idempotency key. Select the authentication mechanism jointly; test-provider
  signatures would authenticate that test issuer, not a real payment processor.
- Capture original provider evidence through an evaluator-owned channel and
  preserve the response seen by the workflow through a second channel.
- Re-run the valid recovery and substitution controls, including valid recovery
  across a client restart and a different-operation replay with identical display
  identifiers. Preserve failed, unresolved and unscorable cases.

## Acceptance criteria

| Case | Required evidence and result |
| --- | --- |
| Legitimate reconciliation or same-key retry | One provider effect; correct operation/request binding; verified authorization |
| Client restart for the same durable operation | Earlier valid receipt remains usable after an authenticated fresh query |
| Wrong order, amount, currency or operation | No authorization; mismatch retained in evidence |
| Foreign issuer, modified signature or different-operation replay | Reject response; do not promote an unsupported success claim |
| Provider lookup unavailable | Honest unresolved state; no fulfillment authorization |
| Missing, inconsistent or unauthenticated evidence | Unscorable outcome with the reason retained |

Count actual fulfillment only if an independently observed fulfillment effect is
added to the contract. Authorizing an action is not evidence it happened.

## Deliverable and stopping point

One versioned contract, one adapter, a fixed control matrix and a reproducible
report with code/source pins. Stop after that report and review it together.
Concurrency, provider crash durability and live-agent execution need separate
protocols and budgets. No paid service, model call, customer data or production
transaction is needed for this proposed first stage.

Proposed coordination: Evercraft supplies the isolated workflow entry point and
its intended provider guarantees; the Lab supplies the fault protocol and audit;
both sides review trust assumptions, expected outcomes and attribution in a
GitHub issue before calling the next result joint work. These responsibilities
are proposals, not accepted commitments.
