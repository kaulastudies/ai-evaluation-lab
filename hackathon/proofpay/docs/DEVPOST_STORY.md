# ProofPay Devpost draft

Prepared 8 November 2026 with 72 passing local tests and locally validated approval renewal. This file prepares text only. The existing Devpost entry remains the entry to use. **Do not click final Submit.** The user's instruction to hold final submission remains in force even after every technical task is complete.

The copy below is accurate at this checkpoint. Refresh its verification paragraph after the production build and genuine model and sandbox capture tests. Attach the final source version and evidence hashes. Do not convert planned outcomes into accomplishments or remove the limitations simply to shorten the story.

## Project name

ProofPay Purchase Desk

## Short pitch

An AI-assisted purchase desk that connects owner approval, a shared allowance and payment evidence, with a PayPal sandbox adapter and explicit recovery when a response is lost.

## Project story — copy-ready checkpoint

### Inspiration

A payment timeout leaves a practical question: did the purchase fail, or did only the response disappear? An assistant's confident answer cannot settle it.

We built ProofPay around a small studio with a $300 allowance for outside review work. Two assistants request packages costing $180 and $160. Both requests may be reasonable, but they cannot both fit. The owner needs to approve a purchase, know what remains available and understand what happened if the payment response is lost.

### What it does

ProofPay keeps the purchase proposal, owner approval, allowance reservation and payment outcome in one operation record. The owner can see available, reserved, paid and unresolved amounts and take the next permitted action.

The sample catalogue contains Workflow review ($180), Design review ($160) and Starter review ($90). These are synthetic digital-service packages; the demonstration does not deliver a paid service. After $180 is approved and reserved, the competing $160 request is blocked. A cheaper option becomes a new proposal requiring its own approval.

The PayPal sandbox path creates an order and sends the buyer to PayPal for native approval before capture. If a capture response is lost, ProofPay retains the reservation and checks the original order. It records payment only when the expected operation, merchant, amount, currency and completed capture match. Repeated verification does not create a new capture request.

### How we built it

The application uses TypeScript, React/Vinext, a Cloudflare Worker and D1. Server-owned catalogue data determines price and currency. An HTTPS model adapter requests a catalogue SKU and explanation, then validates the result independently. The model has no payment credentials, cannot approve itself and cannot declare a payment complete.

Approval binds the purchase details and expiry to the operation. An atomic database update reserves the shared allowance. Separate create and capture request IDs are stored before dispatch. The PayPal integration uses OAuth and Orders v2 create, capture and order lookup. PayPal buyer approval remains separate from the application's owner approval.

Explicit owner reapproval renews an expired approval before capture dispatch. The implementation retains the same purchase, order, request IDs and reservation, and updates the approval version, digest and expiry. Conditional state/version checks reject stale dispatch authority. Reapproval is restricted to expired `APPROVED` or `ORDER_READY` operations; it does not reopen uncertain, capture-dispatched, confirmed or verification-failed operations. These service behaviors have passed local tests; hosted renewal remains a separate check.

Confirmation stores a limited snapshot of the checked provider fields together with the accounting change. The owner can export the operation, request IDs, approval digest and verification records. These are application observations, not signed PayPal attestations.

Rehearsal is a separate, visibly labelled mode. It uses deterministic proposals and a persisted simulated provider. Missing external configuration never silently turns a sandbox action into rehearsal.

### Challenges we addressed

The difficult boundary is between a durable application decision and an external payment effect. A missing response must not free the allowance or invite a second purchase. We also needed competing approvals to use one atomic reservation decision rather than separately reading an outdated balance.

We tested the service code used by the application, including two OS processes contending for allowance and a fresh process reopening persisted state after response loss. Provider fields are checked against the approved operation; a plausible-looking response or model message is insufficient.

### What we have verified

The combined local suite passed 72 of 72 tests. It uses SQLite with a D1-contract adapter, synthetic provider/model records and mocked HTTP. It covers process race/restart cases, approval and owner checks, provider mismatches, receipt privacy and atomic confirmation, including 17 renewal tests and two AI-provenance tests. The provenance checks validate retained provider/model identifiers and exclude unrelated response data; they do not establish an actual model invocation. TypeScript, full ESLint and a clean dependency install also passed. The updated Worker production build passed and the private deployment succeeded.

The private hosted application separately completed a labelled rehearsal: it reserved $180, blocked $160, retained the reservation after a simulated capture response was dropped, and reconciled to $180 paid with $120 available. Repeated reconciliation left one simulated capture and one confirmation. A later $90 rehearsal purchase completed normally. Browser reload was observed in the hosted run; backend process restart was tested locally.

We also verified genuine PayPal sandbox OAuth and create/GET calls through the actual provider adapter. The order remained awaiting buyer action. That separate probe used a synthetic proposal and did not capture payment or write a hosted purchase receipt. A secure, encrypted API-key provisioning attempt failed before returning a usable key; no genuine model call resulted. Genuine model execution and the complete PayPal buyer-approval/capture path remain unfinished at this checkpoint.

### What we learned

Provider idempotency, application approval and a shared budget solve different parts of the problem. PayPal already supplies idempotency for supported APIs. Our contribution is the implemented connection between those controls and an inspectable operation record, rather than a claim to have invented payment retry handling.

An unresolved result also needs a useful product experience: keep the amount reserved, explain why, and offer verification of the original order. Hiding uncertainty behind a success or failure message makes the owner's next decision harder.

### What's next

Verify renewal in the hosted interface. Complete and record the genuine model-to-PayPal sandbox flow, including a normal capture and the labelled response-loss case. Verify judge access and make the demonstration reproducible from the public source.

The commercial hypothesis is that small engineering teams embedding PayPal purchasing would pay to reduce their own approval, recovery and investigation work. We plan to test that with a scoped paid pilot; there are no customers, revenue or savings claims yet.

The current scope is one merchant, USD and a per-workspace allowance. There is no production-payment mode, webhook receiver, refund execution, fulfillment or approval-revocation/release API. Approval renewal does not release the reservation, extend PayPal's order validity or recover an upstream-expired order. Unknown create results without a saved order ID need manual investigation. Receipts are not externally signed, and the project makes no general exactly-once or production-safety guarantee.

## Technology and project links

Suggested tags based on implemented code: TypeScript, React, Vinext, Cloudflare Workers, Cloudflare D1, PayPal REST APIs, PayPal Orders v2, Drizzle ORM, SQLite.

Add a named model/provider tag only after an actual invocation is recorded. Do not add PayPal Agent Toolkit, MCP, Agent Ready, Store Sync, ACP, UCP, AP2 or optional sponsor tools as implemented integrations. Coding assistance is a separate disclosure from runtime AI.

- [Public ProofPay source on the project branch](https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay)
- [Draft pull request #53](https://github.com/kaulastudies/ai-evaluation-lab/pull/53)
- [Private owner deployment](https://proofpay-purchase-desk.kaulastudies.chatgpt.site) — not an independently accessible judge demo at this checkpoint.
- [Setup instructions](../README.md)
- [Independent test evidence](../evidence/independent-review-summary.json)
- [Architecture and limits](ARCHITECTURE.md)

The application source was added during the hackathon within the existing AI Evaluation Lab repository. The source audit found no earlier ProofPay implementation to reuse. Preserve the starter and dependency notices, and describe the event-period application work without claiming that the parent repository or every dependency was newly created. Attach the final reviewed commit and matching evidence hashes before publishing this story.

## Evidence update gate before final review

| Item | Required update before claiming completion |
|---|---|
| Approval renewal | Local service validation passed, including 17 renewal tests. Add the hosted UI result and final source/evidence references; do not equate local fixtures with an actual PayPal renewal outcome. |
| Actual model | Record the provider/model identifier, date, request, validated output and corresponding operation without secrets. A configured key or coding assistant does not establish runtime inference. |
| Normal sandbox capture | Record native buyer approval, the order/capture references, matched provider fields and the hosted receipt. The existing create/GET probe is not this evidence. |
| Lost-response sandbox case | Record the injected response drop, held allowance, original-order lookup, final checked outcome and repeated reconciliation. Keep simulated evidence separate. |
| Restart claim | Identify whether the result is local process restart, browser reload or hosted backend restart. Claim only the one actually performed. |
| Tests and source | The combined local result is 72/72. Record the final source version, evidence hashes and passing production-build outcome; rerun relevant checks if code changes. |
| Judge access | Supply a tested hosted route or a fresh, complete setup path. The private owner deployment alone is insufficient. |
| Video | Add the actual public YouTube URL after recording; keep it under three minutes and align its claims with the same source version. |
| Team | Invite Prof. Nithya Ravi Kumar through the existing draft once a verified delivery address/channel is available. Check acceptance separately; do not attribute work in advance. |
| Final submission | Remains on hold by the user's explicit instruction. Updating this file, tests or draft fields does not authorize clicking Submit. |

When the actual-model, normal-sandbox-capture and lost-response rows pass, replace the checkpoint's unfinished-integration paragraph with the specific observed result and evidence link. Update the hosted renewal result separately. Do not prewrite a successful outcome or use the commercial plan's targets as accomplishments.

The official [rules](https://paypalaihackathon.devpost.com/rules) require a functional build or complete run instructions, public licensed source and a public YouTube demonstration. Rechecked on 8 November: section 4 requires PayPal sandbox integration plus an AI tool/model/platform of the entrant's choice. The [event requirements](https://paypalaihackathon.devpost.com/) explicitly allow a PayPal API, and the [resources page](https://paypalaihackathon.devpost.com/resources) lists REST alongside Toolkit and MCP. Neither Toolkit nor MCP is mandatory. The [FAQ](https://paypalaihackathon.devpost.com/details/faqs) also confirms that sponsor tools are optional. Final eligibility and judging remain with the organizers.
