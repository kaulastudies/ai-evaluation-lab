# Judge guide

## The problem

A small studio delegates requests for outside workflow and design reviews to two assistants but keeps one $300 allowance. A $180 purchase and a $160 purchase cannot both fit. After the owner approves a permitted purchase, the payment response may disappear even though the provider processed it. The studio needs to know what is reserved, what was paid and what still needs checking.

ProofPay Purchase Desk brings those decisions into one workflow. Its contribution is the application-level connection among owner approval, shared allowance, durable operation identity and provider-checked outcome.

## What is real in this build

The current source uses GitHub, native Next.js on Vercel and Neon/PostgreSQL, with signed owner-session authentication. The [production release](../evidence/business-portal-release-2026-11-08.json) is READY after eight real PostgreSQL checks, migrations, builds and both CI runs passed. Browser checks cover the setup-pending shell only. Owner/PayPal configuration and the authenticated hosted workflow remain separate gates. Use the current [development guide](DEVELOPMENT.md) and [QA report](QA_REPORT.md); there is no mock sign-in or current Sites deployment instruction.

An earlier deployed source, `17cbededf`, completed the [fixed $180 PayPal sandbox diagnostic](../evidence/diagnostic-release-review.json): native buyer approval, capture, held allowance after a dropped response and original-order recovery. It used no model. That historical result does not certify the new Vercel/auth/database implementation. Genuine runtime AI, the combined journey, independent judge access and the required public video remain open.

The selected inference route is Vercel free credit with runtime OIDC, a fixed model and a one-attempt grant cap. Personal OpenAI credits are excluded. A configured credit declaration is not successful model execution. The [Postman collection](../postman/README.md) is an offline-validated development handoff; actual Postman execution is not yet claimed.

| Evidence level | What it can establish |
|---|---|
| Unit or mocked integration test | Specified behaviour under controlled inputs; not a live external service result. |
| Application rehearsal | Interactive workflow, reservation/accounting behaviour and simulated provider recovery. |
| Actual model call | A named configured model produced the recorded proposal; validation is still required. |
| PayPal sandbox run | The sandbox returned an order/capture outcome that the application checked. |
| Production operation | Outside the demonstrated scope of this prototype. |

Current test outcomes should be taken from the generated test output for this checkout. This document does not assign an unverified test count.

## Walk through after owner/database setup

1. In **Business settings**, save a $300 default allowance for this walkthrough, then choose **Start rehearsal**. Confirm the **Rehearsal · simulated** label. The seeded Workflow review ($180) and Design review ($160) are sample proposals, not model output.
2. Choose **Approve & reserve $180.00** for Workflow review. Confirm $180 is reserved and $120 remains available. Attempt to approve Design review and inspect **Over allowance**. **Request an alternative** fills a new request. For a deterministic $90 rehearsal example, enter “Suggest a cheaper Starter review package” and choose **Create sample proposal**. The new proposal does not inherit approval.
3. Choose **Create simulated order** for the approved Workflow review. Select **Drop the capture response**, then **Capture simulated payment**. This deliberately discards a simulated provider response after the provider effect.
4. Confirm the result remains unresolved and the $180 remains reserved. Do not describe the lack of a response as payment failure.
5. Choose **Check simulated outcome**. The original simulated order is checked before the application displays **Simulated payment confirmed**. A missing or contradictory result must not become confirmed.
6. Choose **Check outcome again** and inspect the allowance. The repeated read should not add another $180 spend.
7. Export evidence. Inspect the original operation and provider references, create/capture request IDs, approval digest and `verificationRecords`. Confirmation stores a limited snapshot of the provider fields used by the verifier in the same transaction as the accounting change; the receipt labels its source and mode. These are inspection records, not externally signed proof.

For the external path, use **Connections → Start PayPal sandbox workspace**, then **Ask AI for a proposal**. The current free-credit policy permits only one dispatched model attempt per workspace and one total for the reviewed grant; failures count. Use rehearsal for the two-request allowance example, and do not add model calls merely to stage it. After owner approval, choose **Create PayPal order**, **Open PayPal approval**, **Capture approved order** and **Check PayPal outcome**. Record this path only after actual model and sandbox runs have passed. The top label must read **PayPal sandbox**. Configuration alone does not establish either integration.

Actual process-restart validation must stop and restart the backend while preserving the database and then reconcile the saved operation. A test with a fresh service object establishes a narrower result; refreshing the page only exercises browser reload. State which one was performed.

## Why PayPal and AI are central

The PayPal adapter uses native buyer approval, Orders v2 create/capture and subsequent order lookup. Confirmation requires matching order and operation references, merchant, full amount and currency, a completed order and a single completed final capture. AI interprets a buying request and proposes a catalogue selection; application code validates the SKU and price and enforces authority and allowance. If a cheaper alternative is offered, it is a new proposal requiring approval.

PayPal already supports idempotency for specified APIs within their documented retention limits. ProofPay does not claim to invent that feature. Its scope combines it with application approval, cross-request budget accounting and durable recovery. The current build does not claim Agent Ready, Store Sync, ACP or UCP compatibility.

## Evaluation map

The [official rules](https://paypalaihackathon.devpost.com/rules) give the five criteria equal weight. The table identifies evidence to collect; it does not predict a score or a win.

| Criterion | Evidence to inspect |
|---|---|
| Implementation | Provider adapter, durable ledger, proposal validation and evidence comparison; distinguish mocked and live runs. |
| Design | Owner can understand available, reserved, paid and unresolved amounts and the next permitted action. |
| Impact | A concrete shared-budget purchasing problem; no invented users, savings or revenue. |
| Innovation | Approval and concurrent allowance remain connected to the original payment through interruption. |
| Presentation | An ordinary purchase, an explicit interruption and a readable recovered outcome within a short demonstration. |

## Scope and limitations

The sample catalogue contains Workflow review ($180), Design review ($160) and Starter review ($90). The packages, prices and requests are synthetic; no paid review service is delivered. The initial scope is one controlled merchant and USD. PayPal sandbox capture does not establish production settlement, service delivery or commercial readiness. Rehearsal does not establish even a sandbox capture.

A new workspace snapshots its saved default allowance; $300 is the unconfigured default and the amount used in this walkthrough. It is a per-workspace limit, not account-wide or a bank balance. Approval expires after 15 minutes, but expiry does not release a reservation. Explicit owner renewal is available for expired pre-capture APPROVED or ORDER_READY operations. It preserves purchase, reservation and provider IDs, and invalidates stale dispatch authority. It does not extend PayPal order validity. The owner can cancel a proposed, blocked or approved request before any provider dispatch. Cancellation preserves its record and releases an approved local reservation once. An existing provider order, dispatch, uncertain outcome or confirmed payment cannot be cancelled through this action; it is not a provider cancellation or refund. Uncertain create/capture calls are not automatically retried. A lost create response with no saved order ID requires manual investigation; an unknown outcome keeps its reservation. History selection is blocked while the active workspace has held/uncertain purchases in either mode; a separate explicit simulated reset retains prior history.

The prototype has no webhook receiver, refund execution, fulfillment, subscriptions, multi-provider fallback or production-payment flow. It provides no regulatory compliance assurance or guarantee of duplicate prevention under every failure. Hashes and receipts aid inspection but do not make an underlying claim true. Tests establish only the stated cases and environment. See [architecture and limits](ARCHITECTURE.md) for implementation detail.

Final judging evidence should identify the source commit, reproduction commands, actual model/version, mode, provider references, run date, observed result and known failures. Do not publish credentials in that evidence.

## Current verification checkpoint

The [business increment](../evidence/business-portal-checks-2026-11-08.json) passed 199/199 local tests, types, full lint and both builds; production is READY after eight real PostgreSQL checks, repeat migration and both CI runs passed. The current three-width browser review covers all eight navigation headings in the setup-pending shell, not authenticated records or actions. The preceding 178-test native release and former runtime's 92-, 131- and 151-test results remain separate historical checkpoints. The dependency audit reports zero known findings, including development dependencies, with two parser compatibility checks passed. See [dependency evidence](../evidence/dependency-remediation-2026-11-08-summary.json) and [QA](QA_REPORT.md) for the current migration checks. A zero audit does not establish application security or a working deployment.

The commercial and submission drafts are in [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) and [DEVPOST_STORY.md](DEVPOST_STORY.md). Final Devpost Submit remains held.

A historical [hosted renewal rehearsal](../evidence/hosted-renewal-review.json) waited for the real approval window to expire, observed disabled capture, renewed to version2 without changing the order or $180 reservation, then recovered a dropped simulated capture response after browser reload. It finished with $180 paid, $0 reserved and $120 available. This is simulated-provider evidence.


## Payment operations workspace

The owner interface now has Overview, Purchases, Approvals, Evidence, Controls, Connections, Business settings and Workspace history. Saved business/department labels and the default allowance are snapshotted into new workspaces; later defaults do not rewrite earlier approvals. The department is metadata, not a multi-user role or separate budget. **Purchases → Export CSV** reports all loaded active-workspace purchases, including filtered-out rows, with saved context and mode/source labels. It is unsigned application data, not an invoice or accounting certification. A searchable purchase list opens a focused record with the exact seller, amount, approval and permitted action. Controls show the enforced rules rather than editable placeholders. Connections separates configured services from verified execution.

The historical [hosted workspace review](../evidence/hosted-workspace-review.json) checked all six desktop views, search/filters, retained evidence and cancellation before dispatch. Approving a simulated $90 Starter review changed available/reserved/paid from $120/$0/$180 to $30/$90/$180. Cancelling restored $120/$0/$180; the cancelled request and one cancellation event persisted after reload. A separate [responsive review](../evidence/responsive-review.json) rendered the actual component and CSS in 360px and 390px iframe viewports with synthetic data, plus a 768px tablet spot check. It corrected cramped approval/control cards, contained table overflow and section navigation scroll. This is local layout evidence; physical-device behavior and hosted mobile authentication remain unverified.
