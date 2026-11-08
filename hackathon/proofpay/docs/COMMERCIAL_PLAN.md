# ProofPay commercial plan

Decision draft · 8 November 2026 · current local verification: 92/92 tests passed

Build a paid, narrow integration business first: help a software team connect its purchase approvals and shared allowance to a recoverable PayPal operation. The larger opportunity is a reusable service for controlling financial actions across agent applications. Customer demand, willingness to pay, repeatability and that expansion path are hypotheses. No customer, revenue, partnership, market share or valuation is established by this prototype.

## Initial customer and purchase trigger

The first buyer to test is the CTO or engineering lead of a small B2B services software company with an existing PayPal merchant integration. A useful qualification profile is 5–30 engineers, a named release within 90 days, and a workflow in which several users or assistants request purchases against one customer's allowance. These numbers define a prospect filter; they are not measured market data.

Start with one cooperating merchant selling a fixed catalogue of digital services to business teams. A studio purchasing workflow and design reviews is the demonstration, not evidence that studios want this product. The customer's engineering team buys the integration and maintenance; the studio owner uses the approval interface. Finance or operations helps define the allowance and acceptable evidence.

The purchase trigger is concrete: the team can create a PayPal order, but cannot yet explain how its application handles competing requests, changed approval details or an ambiguous capture result. Ask for a release ticket, architecture diagram, incident record or existing test that establishes the work. General interest in AI payments does not qualify a lead.

The first integration keeps one merchant, USD, explicit owner approval and native PayPal buyer approval. The current merchant-credential model is not a general-purpose wallet that buys from arbitrary sellers. Multi-merchant onboarding, delegated access and marketplace fund flows would be separate products and integrations.

## Workflow and the case for PayPal

An assistant proposes an allowed service. Application code validates the item and price. The owner approves the exact purchase, and the application reserves the available allowance. PayPal provides buyer approval and payment execution. If the application loses the capture response, it retains the reservation and checks the original order before recording payment. A new proposal needs its own approval.

PayPal already provides substantial agent-commerce infrastructure. Agent Ready supports ACP and UCP integration paths, including a UCP path through Orders v2. Store Sync connects merchant catalogues and order management to AI shopping; its current documentation restricts eligibility to physical goods sold to US customers in USD. Our digital-services demonstration does not claim Store Sync compatibility. [1][2]

The commercial question is whether a reusable application layer can help more teams finish these workflows without writing and maintaining the same approval, reservation and recovery code. A possible PayPal ecosystem benefit is more integrations that reach a working payment and remain understandable when the application fails. That is our hypothesis, not a statement that PayPal lacks these capabilities or needs to buy ProofPay. Measure partner integration time, unresolved-operation handling and developer adoption before making that case.

PayPal's AP2 work already addresses signed intent and payment mandates. ProofPay's stored approval digest is an application record, not an AP2 mandate, PayPal attestation or cryptographic proof of authorization. Protocol compatibility would need its own implementation and verification. [3]

## Alternatives a buyer can choose today

Primary sources checked on 8 November 2026. Vendor descriptions establish documented capabilities; they do not establish our comparative performance. No competitor was independently benchmarked for this plan.

| Alternative | Documented strength | Consequence for ProofPay |
|---|---|---|
| PayPal APIs plus the customer's own application | Supported APIs provide request idempotency; PayPal documents recovery from a capture timeout using the same request ID within its retention period. [4] | Compare against a competent implementation that already uses idempotency, database transactions and provider lookups. Ordinary duplicate-request handling is not our differentiation. |
| PayPal Agent Ready, Store Sync and agent tooling | Merchant acceptance, product discovery, checkout and callable payment functions are already covered across PayPal's products. [1][2][5] | Sell a specific application integration benefit. Do not present a checkout wrapper or tool list as a new category. |
| Stripe Link wallet and Issuing for agents | Link supports approved agent spend requests and credentials scoped by amount, currency and merchant. Issuing supports customized agent spending workflows. [6] | Owner approval and restricted credentials alone are not a defensible claim. A buyer already using Stripe may have little reason to switch. |
| Ramp agent finance | Ramp describes agent identities, owners, budgets, approvers, merchant restrictions and recorded actions, with agent payment options. [7] | Do not position ProofPay as the first system that governs agent spending. Ask whether a customer needs an embedded PayPal workflow outside its existing finance stack. |
| Temporal plus a provider adapter | Temporal documents durable agent execution and the distinction between execution state and external payment effects, including idempotency-based reconciliation. [8] | Restart recovery alone is not unique. A customer with mature orchestration may prefer building the remaining domain logic itself. |

Public documentation cannot prove that a competitor lacks a particular edge case. Run the same agreed scenarios against the buyer's actual alternative. If the alternative is sufficient and cheaper to maintain, recommend it and record the lost opportunity honestly.

## What could become defensible

The present contribution is a coherent implementation joining owner approval, an atomic shared reservation, durable dispatch identity and checked provider evidence. The combined local suite passed 92 of 92 tests, including 17 approval-renewal tests, 20 pre-dispatch cancellation tests and two AI-provenance tests. TypeScript, full ESLint and a clean dependency install also passed; the updated Worker production build passed. Hosted rehearsal has exercised budget refusal and response-loss reconciliation. Genuine PayPal OAuth and provider-adapter create/GET checks passed separately; actual buyer approval/capture and external-model execution remain unfinished. Encrypted API-key provisioning failed without returning a usable key, so it did not enable a model call. These establish bounded engineering progress, not a commercial advantage.

Approval renewal is implemented in the backend and owner interface, with its service behavior validated locally. It permits explicit owner reapproval only for an expired `APPROVED` or `ORDER_READY` operation. It retains the purchase details, order and request IDs, and existing reservation while updating the approval version, digest and expiry. Conditional state/version checks protect dispatch from stale approval. Renewal is unavailable for uncertain, capture-dispatched, confirmed or verification-failed operations. It neither releases funds nor extends an expired PayPal order's validity. A separate hosted rehearsal observed expiry, disabled capture, renewal with the same order and reservation, and response-loss recovery after browser reload. This is simulated-provider UI evidence, not a real-provider renewal outcome.

| Hypothesis | Evidence needed | What would weaken it |
|---|---|---|
| A reusable PayPal integration saves release work | Two teams implement the same agreed workflow with recorded engineering hours and compare against their scoped in-house estimate or implementation. | Each customer needs a different state machine or the saved work is small. |
| Operation-level evidence shortens investigation | A reviewer unfamiliar with the implementation identifies owner approval, held allowance and provider outcome from a receipt and reproduces the decision. | Reviewers still need database access and an engineer to explain every case. |
| A maintained failure-case suite creates continuing value | Customers rerun the suite after provider, model and application changes and renew for that maintenance. | Tests are copied once and nobody needs ongoing service. |
| A common contract can cover more financial actions | A second paid workflow reuses the core approval and evidence contract while preserving provider-specific semantics. | The common abstraction hides essential provider differences or increases integration time. |

Potential long-term assets are tested adapters, accumulated failure cases, dependable migration practices and distribution through integration partners. None is a moat today. Open source makes implementation inspectable and also makes copying possible. Do not assume access to customer transaction data, a data network effect or exclusivity.

## Pilot offer and pricing experiments

Offer a four-week, sandbox-only integration pilot for one workflow. The customer supplies a named engineer, test merchant/buyer access through a secure setup, its approval rules and the baseline to compare. Deliver a working integration branch, an owner walkthrough, repeatable fault tests, redacted operation receipts and a written decision on whether further deployment work is justified. No production payments or money custody are included.

The pilot should first prove the normal path and one lost-capture-response path with genuine model and PayPal sandbox calls. It should also exercise competing approvals, mismatched evidence and repeated reconciliation. Preserve failed runs. Agree the acceptance cases before implementation; a screenshot or configured credential is insufficient.

These are proposed prices to test, not published prices or revenue:

| Offer hypothesis | Scope | Test |
|---|---|---|
| $2,500 fixed pilot | One four-week sandbox workflow; at most 20 delivery hours; 50% at start and 50% on agreed acceptance. | Will two qualified teams pay for this scope rather than request free consulting? |
| $499/month continuation | One workflow, maintained adapter/test suite and bounded support; usage limit to be set from pilot costs. | Will a customer renew after it can inspect and run the code itself? |
| $1,499/month team service | Several workflows, operating visibility and contracted support, only after those features exist. | Is there repeated operational work worth the additional spend? |

Keep PayPal fees and model usage separate. Do not charge for repeated reconciliation reads of the same operation: that would discourage checking uncertain outcomes. If usage pricing is introduced, define the billable operation precisely and prevent retries from becoming new charges.

Illustrative delivery economics: 20 hours at an assumed $75 internal hourly cost consumes $1,500 of a $2,500 pilot, leaving $1,000 before infrastructure, sales effort and overhead. At 40 hours, the pilot loses money on delivery alone. For a $499 monthly plan and a target 75% contribution margin, hosting, model subsidies and support together must stay below $124.75 per month. Neither cost nor margin has been measured. Time tracking is part of the experiment.

Do not use a percentage of payment volume to justify revenue today. ProofPay has no established processing role, commercial terms or transaction volume.

## Success, stop conditions and the next 90 days

The numerical thresholds below are management decisions for this experiment, not observed results. Start the clock when a working external sandbox flow is available and the owner elects to begin customer discovery. This document does not authorize or send outreach.

| Period | Work and deliverable | Continue only if |
|---|---|---|
| Days 1–10 | Finish genuine model + PayPal sandbox normal/recovery runs, maintain exact evidence, test a fresh reviewer setup and document current limits. Prepare a five-question discovery guide and one pilot scope. | A second person can reproduce the supported flow; failures remain visible and no unsupported confirmation is reported. |
| Days 11–30 | Hold 10 qualified discovery conversations after outreach authorization. Ask about a current release, existing implementation, manual investigation time, buying authority and budget. Seek three concrete pilot scopes and two paid commitments. | At least six conversations reveal a current workflow problem, three provide a specific implementation case, and two accept a paid pilot or procurement-backed commitment. Interest alone does not pass. |
| Days 31–60 | Deliver the first two pilots; measure integration hours, reviewer investigation time, support load and completed acceptance cases. Address release blockers found in those workflows. | Both pilots meet the agreed bounded cases, at least one customer reports a measured reduction in release/investigation effort, and delivery fits the planned cost envelope. |
| Days 61–90 | Complete a third pilot if the first two justify it. Offer continuation to the completed pilots. Package shared code and tests; keep bespoke work explicit. | At least two customers pay to continue at a tested price, recurring costs fit the agreed margin target, and a substantial shared implementation serves more than one customer. |

Measure investigation time with the same documented task and reviewer profile before and after; use at least five fault cases per pilot and report individual outcomes. A target to test is median time below ten minutes and at least a 50% improvement over the customer's baseline. This is an acceptance hypothesis, not a savings claim. Record every incorrect confirmation, reservation error and extra provider dispatch. Any such failure blocks rollout until understood and corrected; zero failures in a small suite is not a general safety guarantee.

Stop or narrow the product if ten qualified conversations produce fewer than three concrete problems, or if no team will pay after three scoped proposals. Rework the business model if a pilot routinely exceeds 20 delivery hours or customers only value a one-time code handoff. Stop expansion if the buyer's existing PayPal, Stripe, Ramp or orchestration setup already solves the agreed problem adequately. If demand exists only for integration services, run a services business rather than report unearned software recurring revenue.

Before any production proposal, resolve actual gaps for that customer's workflow. Current examples include post-dispatch cancellation needs, unknown-create investigation, stronger hosted access verification and operating procedures. Hosted rehearsal has verified approval renewal; it does not establish recovery of an upstream-expired PayPal order. Pre-dispatch cancellation has separate local race and accounting tests. Add authenticated webhooks, refunds or account-wide budgets only when required by the chosen workflow. Current application receipts are not externally signed. There is no production-readiness claim.

## Expansion and scale assumptions

Expand in stages: one PayPal workflow; then repeated deployment for the same buyer profile; then another requested action such as refund approval; then a second provider only when a paying customer needs it. Every additional action needs its own authorization, state and evidence contract. Provider interoperability is a future hypothesis, not a current feature. A channel through agencies, software platforms or payment integration partners is worth testing after direct pilots establish repeatability; there is no partnership today.

The ambition can be large while the arithmetic stays honest:

| Assumed customers | Assumed average monthly revenue per customer | Implied annual recurring revenue | What must be true |
|---:|---:|---:|---|
| 100 | $499 | $598,800 | A small repeatable product with low support burden. |
| 1,000 | $1,499 | $17,988,000 | Multi-team value and a repeatable acquisition channel. |
| 4,000 | $2,100 | $100,800,000 | Enterprise-grade operation, expansion revenue and broad distribution. |
| 33,334 | $2,500 | $1,000,020,000 | A much larger category and distribution system than the present initial segment establishes. |

Each row is customers × monthly revenue × 12. It excludes churn, discounts, sales costs and delivery costs. It is not a forecast, market-size estimate or evidence that those customers exist. A billion-dollar company valuation cannot be derived responsibly from this prototype or an arbitrary revenue multiple. The next credible milestone is two paid, useful pilots; the next is repeat purchases or renewals with measured economics.

## Sources and evidence

1. [PayPal Agent Ready overview](https://developer.paypal.com/agent-ready/overview/), live page updated 13 October 2026; checked 8 November. The live page includes three integration paths; older search snippets omit the PayPal Orders v2 path.
2. [PayPal Store Sync overview](https://developer.paypal.com/store-sync/overview), checked 8 November 2026.
3. [PayPal: Agent Payments Protocol](https://developer.paypal.com/community/blog/PayPal-Agent-Payments-Protocol/), 16 September 2025; checked 8 November 2026. Describes protocol intent and potential integrations, not proof of ProofPay support.
4. [PayPal idempotency](https://developer.paypal.com/api/rest/reference/idempotency/), updated 11 August 2026; checked 8 November. API-specific support and retention apply.
5. [PayPal Agent Toolkit quickstart](https://developer.paypal.com/ai-tools/toolkit/), checked during the official-resources review; no toolkit integration is claimed by ProofPay.
6. [Stripe: Giving agents the ability to pay](https://stripe.com/blog/giving-agents-the-ability-to-pay), 29 April 2026; checked 8 November.
7. [Ramp: Finance for companies that run on agents](https://agents.ramp.com/), checked 8 November 2026; product claims are Ramp's own.
8. [Temporal: Agent memory and state](https://docs.temporal.io/ai/featured/memory-state-stripe), page records verification on 26 October 2026; checked 8 November.

Project evidence: [independent review summary](../evidence/independent-review-summary.json), [TAP output](../evidence/independent-review.tap), [architecture](ARCHITECTURE.md), and master handoff v1.3 for the separately observed hosted rehearsal and sandbox create/GET probe. Attach the final source commit and refreshed evidence hashes before publishing this checkpoint. Preserve the distinction between controlled local tests and observed external-service results.
