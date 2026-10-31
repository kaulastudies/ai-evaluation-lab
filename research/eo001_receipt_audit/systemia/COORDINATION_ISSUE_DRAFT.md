# EO-001: agree Systemia recovery evidence and authority boundaries

Historical draft. The current coordination discussion is published in
[Lab issue #35](https://github.com/kaulastudies/ai-evaluation-lab/issues/35),
linked to Evercraft #1705. Use that issue for updates and scope agreement.
This retained draft does not establish accepted scope or speak for Evercraft.

References:

- Lab PR #30: https://github.com/kaulastudies/ai-evaluation-lab/pull/30
- Evercraft issue #1705: https://github.com/jgaethle10/forge-operator/issues/1705
- Evercraft candidate PR #1744: https://github.com/jgaethle10/forge-operator/pull/1744
- Lab execution report: [systemia/README.md](README.md)

## Proposed bounded question

Can we independently distinguish an authenticated observation, an established
synthetic effect, and permission to resume interrupted work without allowing any
one of these to substitute for the others?

## Completed independent baseline

The Lab has run the pinned Evercraft candidate through four synthetic provider
faults and exercised the actual native recovery CLI in fourteen cases. A valid
signature on a false completed claim is admitted as attestation only: the native
hold remains, no effect is established, and completion/retry are rejected. The
report retains source pins, public observations, state snapshots and verdicts.
These are Lab-observed results; joint review has not yet been recorded.

## Contract to agree before expansion

- Preserve Lab operation/request/idempotency identity alongside Systemia mission,
  goal, work, attempt, attempt key and predeclared provider identity.
- Keep the Lab issuer and native observer trust anchors separate. No candidate
  may configure trust, possess signing keys or alter the host-owned request.
- Verify Lab challenge freshness and native hold/expiry freshness as distinct
  rules. A valid observation cannot release a native hold by itself.
- Retain candidate-visible history separately from evaluator-only oracle state.
  Missing evidence remains missing; later oracle knowledge cannot justify an
  earlier success claim.
- Publish separate results for evidence integrity, behavior under uncertainty
  and task completion, with untested or unobserved outcomes marked unknown.
- Agree the authority that could eventually establish provider truth and release
  a hold. This experiment intentionally grants no such release authority.

## Proposed acceptance cases

Use the committed four-case candidate baseline and fourteen native cases as the
review packet. Require all missing, altered, foreign and replayed evidence cases
to remain held. Require the authentic-but-false completion counterexample to be
identified as contradicted while preserving quarantine. Review failures and
unresolved cases alongside confirmations. Do not infer fulfillment from an
authorization verdict.

## Next gate: real agent decisions

Only after agreement on the contract, select one isolated decision entry point
with explicit model/runtime identity, configuration and a bounded run budget.
Record every raw model proposal, deterministic guard decision, host action and
timeout/error. Score the model and the guarded workflow separately. A model that
proposes an unsafe retry but is blocked by a guard has not itself passed a safe
decision test. No paid hosted model or production environment is assumed.

Stop after one agreed matrix and review the evidence together. No real payments,
production mission changes, customer data, external dispatch, funded commitment
or accepted partnership is included.
