# Judge guide

## The problem

A small studio delegates requests for outside workflow and design reviews to two assistants but keeps one $300 allowance. A $180 purchase and a $160 purchase cannot both fit. After the owner approves a permitted purchase, the payment response may disappear even though the provider processed it. The studio needs to know what is reserved, what was paid and what still needs checking.

ProofPay Purchase Desk brings those decisions into one workflow. Its contribution is the application-level connection among owner approval, shared allowance, durable operation identity and provider-checked outcome.

## What is real in this build

The interface, durable application service, rehearsal provider and external adapters are implemented. No actual PayPal sandbox transaction or runtime model call has been verified in the current build session. Use the application's displayed mode and evidence record to distinguish rehearsal from external integrations. A simulated capture is a rehearsal outcome; it must never be described as a PayPal-confirmed payment.

The hosted Site is private to the owner and is not ready for independent judge access. Hosted UI verification and external-service runs remain separate requirements. Portable local setup is in the [README](../README.md); the managed local preview currently lacks simulated sign-in.

| Evidence level | What it can establish |
|---|---|
| Unit or mocked integration test | Specified behaviour under controlled inputs; not a live external service result. |
| Application rehearsal | Interactive workflow, reservation/accounting behaviour and simulated provider recovery. |
| Actual model call | A named configured model produced the recorded proposal; validation is still required. |
| PayPal sandbox run | The sandbox returned an order/capture outcome that the application checked. |
| Production operation | Outside the demonstrated scope of this prototype. |

Current test outcomes should be taken from the generated test output for this checkout. This document does not assign an unverified test count.

## Walk through the product

1. Choose **Start $300 rehearsal**. Confirm the **Rehearsal · simulated** label. The seeded Workflow review ($180) and Design review ($160) are sample proposals, not model output.
2. Choose **Approve & reserve $180.00** for Workflow review. Confirm $180 is reserved and $120 remains available. Attempt to approve Design review and inspect **Over allowance**. **Request an alternative** fills a new request. For a deterministic $90 rehearsal example, enter “Suggest a cheaper Starter review package” and choose **Create sample proposal**. The new proposal does not inherit approval.
3. Choose **Create simulated order** for the approved Workflow review. Select **Drop the capture response**, then **Capture simulated payment**. This deliberately discards a simulated provider response after the provider effect.
4. Confirm the result remains unresolved and the $180 remains reserved. Do not describe the lack of a response as payment failure.
5. Choose **Check simulated outcome**. The original simulated order is checked before the application displays **Simulated payment confirmed**. A missing or contradictory result must not become confirmed.
6. Choose **Check outcome again** and inspect the allowance. The repeated read should not add another $180 spend.
7. Export evidence. Inspect the original operation and provider references, create/capture request IDs, approval digest and `verificationRecords`. Confirmation stores a limited snapshot of the provider fields used by the verifier in the same transaction as the accounting change; the receipt labels its source and mode. These are inspection records, not externally signed proof.

For the external path, use **Connections → Start PayPal sandbox workspace**, then **Ask AI for a proposal**. After owner approval, choose **Create PayPal order**, **Open PayPal approval**, **Capture approved order** and **Check PayPal outcome**. Record this path only after actual model and sandbox runs have passed. The top label must read **PayPal sandbox**. Configuration alone does not establish either integration.

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

The $300 allowance is per workspace, not account-wide. Approval expires after 15 minutes, but expiry does not release a reservation. There is no revocation, renewal or release API. Uncertain create/capture calls are not automatically retried. A lost create response with no saved order ID requires manual investigation; an unknown outcome keeps its reservation. Sandbox workspace switching is blocked while funds remain held.

The prototype has no webhook receiver, refund execution, fulfillment, subscriptions, multi-provider fallback or production-payment flow. It provides no regulatory compliance assurance or guarantee of duplicate prevention under every failure. Hashes and receipts aid inspection but do not make an underlying claim true. Tests establish only the stated cases and environment. See [architecture and limits](ARCHITECTURE.md) for implementation detail.

Final judging evidence should identify the source commit, reproduction commands, actual model/version, mode, provider references, run date, observed result and known failures. Do not publish credentials in that evidence.
