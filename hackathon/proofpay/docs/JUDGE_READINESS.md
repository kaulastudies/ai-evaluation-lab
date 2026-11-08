# ProofPay judge readiness

Reviewed **8 November 2026**, including the release owner's 151-test local result and [verified PayPal sandbox diagnostic](../evidence/diagnostic-release-review.json) on deployed source `17cbededf`. Earlier rehearsal/QA artifacts retain their own source checkpoints. This is an internal assessment, not an organizer decision or prize prediction. **Final Devpost submission remains on hold at the owner's instruction.**

ProofPay has now completed a genuine buyer-approved PayPal sandbox capture and recovered its deliberately dropped response through original-order lookup. That verified diagnostic uses one fixed $180 sample and no AI. Meaningful runtime AI, the combined model-to-payment journey, independent judge access and the required public video remain open; the submission is not complete.

## Official requirements and dates

The [event requirements](https://paypalaihackathon.devpost.com/) require meaningful use of PayPal and AI. The [rules, sections 4 and 6](https://paypalaihackathon.devpost.com/rules) distinguish entry requirements, a baseline viability check and five equally weighted criteria. PayPal REST is permitted; the [resources](https://paypalaihackathon.devpost.com/resources) list REST alongside the Agent Toolkit and MCP. Neither Toolkit nor MCP is mandatory. Installing a toolkit would not resolve the missing runtime AI evidence.

| Event | Verified timing |
|---|---|
| Submission | 1 October 2026, 09:15 Pacific, through **12 November 2026, 12:00 PST**. Deadline: **12 November, 20:00 UTC / 13 November, 01:30 IST**. |
| Judging | 1 December, 14:00 PST, through 15 December, 08:00 PST. |
| Announcement | 21 December 2026. The rules say approximately 14:00 Pacific; the schedule says 09:00 PST. Recheck the inconsistent announcement time. |

Sources: [schedule](https://paypalaihackathon.devpost.com/details/dates) and [rules, section 1](https://paypalaihackathon.devpost.com/rules), accessed 8 November 2026. The submission deadline agrees across both pages.

## Entry requirements: evidence and gaps

The first column summarizes the official [submission page](https://paypalaihackathon.devpost.com/) and [rules](https://paypalaihackathon.devpost.com/rules). Status describes this project, not certified eligibility.

| Requirement | Implemented evidence | Status and remaining gate |
|---|---|---|
| PayPal sandbox plus meaningful AI | [PayPal adapter](../lib/proofpay/provider.ts): OAuth, Orders v2 create/capture/lookup and native buyer approval. [Verified diagnostic](../evidence/diagnostic-release-review.json): actual sandbox capture and response-loss recovery. [Model adapter](../lib/proofpay/ai.ts): validated catalogue selection and limited provenance. | **PayPal diagnostic verified; AI incomplete.** The external run used a fixed sample, not a model proposal. No genuine model invocation or complete AI-to-PayPal run is established. |
| Working, reproducible demo | [Setup](../README.md), committed migration, server routes, [hosted rehearsal](../evidence/hosted-renewal-review.json), [workspace review](../evidence/hosted-workspace-review.json). | **Partly verified.** Owner access works. A fresh judge must successfully follow portable setup or receive an independently tested hosted route. A private owner URL alone is insufficient. |
| Public source, open-source license and run instructions | [Project branch](https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay), [Apache-2.0 license](../LICENSE), source, lockfile and [README](../README.md). The parent repository also has a license. | **Present locally; final publication check needed.** Verify anonymous access to the final revision and GitHub's license display. Include required assets/setup in that revision. |
| Functionality description and AI-tool identification | [Story](DEVPOST_STORY.md), [walkthrough](JUDGES.md), [architecture](ARCHITECTURE.md). | **Checkpoint draft ready.** Name the runtime provider/model after execution. Separate coding assistance from AI used by the product. |
| Public YouTube demo under three minutes | [Demo script](DEMO_SCRIPT.md) and demonstrated rehearsal sequence. | **Missing.** No verified public video URL. Record the actual build and mode; match narration to evidence. |
| Free judge testing through judging | Portable local flow and private hosted application exist. | **Unverified.** Test without the owner's session. Arrange any needed test access through an appropriate restricted channel; do not publish API secrets or owner credentials. |
| Event-period creation or substantial update | Git history adds ProofPay during November 2026. | **Application work documented.** Identify the existing parent repository and starter/dependencies; do not claim everything was created for the event. |
| English materials | Application, repository and story use English. | **Present.** Keep the final video/testing instructions consistent. |
| Eligible entrant and authorized team representative | Personal/team attestations, not software properties. | **Owner confirmation before submission.** Registration, teammate acceptance, eligibility and representation are not established by a build. |
| Rights and permitted third-party use | Dependency manifest, project license and retained starter notices. | **Final review needed.** Check asset/music permissions and applicable integration terms; do not attest on behalf of teammates. |
| Optional sponsor awards | No sponsor-specific integration is represented as implemented. | **Not targeted at this checkpoint.** Additional requirements apply only if entered. |

## Evidence inventory

| Evidence | Establishes | Does not establish |
|---|---|---|
| Latest local release result | Release owner reports **151/151 local tests passed** after diagnostic changes. This updates the earlier 131-test checkpoint. | Hosted execution, actual provider/model calls or a broad safety guarantee. Read the diagnostic browser evidence separately. |
| [Earlier local QA summary](../evidence/qa-2026-11-08-summary.json) and [test log](../evidence/qa-2026-11-08-test-output.log) | The historical **131/131** result covers provider, service, authentication, model, security, database and offline receipts, including separate-process races/restart and transactional writes. | The latest count, real PayPal/model execution, hosted D1 certification or ingress identity stripping. Provider/model records are synthetic. |
| [Historical local summary](../evidence/independent-review-summary.json) and [TAP](../evidence/independent-review.tap) | The earlier 92/92 result documents its service checkpoint. | Verification of later changes. |
| [Actual PayPal sandbox diagnostic](../evidence/diagnostic-release-review.json) | Fixed $180 sample, explicit owner and native buyer approval, one observed capture action with deliberate response loss, $180 reservation retained through reload, original-order GET confirming capture `4JC48621EJ575850B`, and stable repeated lookup/accounting. Final state: $120 available/$0 reserved/$180 paid/no unresolved purchase. | AI inference, a combined AI-to-payment journey, production funds, backend process restart, independent judge access or independently measured provider request counts. |
| [Hosted renewal rehearsal](../evidence/hosted-renewal-review.json) | Actual 15-minute expiry; capture disabled; renewal kept the order and $180 reservation; simulated response loss survived browser reload; lookup produced $180 paid/$120 available. | PayPal execution, hosted backend restart or independently measured provider request counts. |
| [Hosted workspace review](../evidence/hosted-workspace-review.json) | Six desktop views; search/filters; $90 approval/cancellation restored allowance; retained cancellation event after reload. | Model inference, sandbox capture or physical-device behavior. |
| [Hosted recovery review](../evidence/hosted-recovery-review.json) | On the deployed `47dcf677` application: a $160 request was blocked with $120 available; a new $90 alternative required owner approval; a dropped simulated capture response kept $90 reserved through reload; lookup reached $270 total paid/$30 available; another check retained the same capture and totals. | A real model or PayPal capture, backend restart, direct database inspection or measured provider-call counts. The UI reported four exported records, but the download-event wait timed out and file bytes were not verified. |
| [Earlier responsive review](../evidence/responsive-review.json) and [image](../evidence/mobile-approval-qa.png) | Actual component/CSS at phone widths using read-only synthetic fixtures; tablet spot check. TypeScript, lint and Worker build passed at that earlier UI checkpoint. | Later typography/inspector changes, hosted mobile authentication, touch-device behavior or payment execution. |
| Later local typography and [receipt inspector](../components/proofpay/receipt-inspector.tsx) review | Release review observed the new typography at 360/390/768/1280px without page-level horizontal overflow, and working keyboard scrolling. The implemented inspector was reviewed at 360/390px with a synthetic receipt. Full application TypeScript and ESLint checks also passed separately. | A real provider receipt or hosted verification of these later changes. The inspector reads stored observations; it does not perform a provider lookup or independently authenticate a receipt. |
| Earlier genuine PayPal adapter probe | OAuth, create and GET succeeded; that earlier order awaited buyer action. | A completed purchase in that probe. The later diagnostic above supplies separate capture evidence. |

Keep the layers separate: the release owner reports **151 local tests**, the earlier QA artifact records 131, and the diagnostic artifact records an actual hosted sandbox transaction. The 92-test and earlier responsive artifacts remain historical. A test-count update does not retroactively change an older artifact or prove external execution. The hosted evidence retains summarized observations, not raw account/network logs.

The implemented inspector compares current purchase fields with stored provider observations, including seller, amounts, currency, order/operation/capture references and completion status. Missing or different values remain explicit. The stored verification schema lacks the historical approval version and catalogue item; equal values therefore do not prove which approval version was checked or independently establish the item. The [offline verifier](../scripts/verify-receipt.mjs) checks versioned receipt structure, approval binding/digest and internal consistency. It does not establish authenticity: an author can replace both data and digest.

## Five judging criteria

Names and equal weighting follow [rules, section 6](https://paypalaihackathon.devpost.com/rules); the [event page](https://paypalaihackathon.devpost.com/) explains the criteria. The assessment is ours.

| Criterion | Why a judge could choose ProofPay | Why a judge could decline it now | Next evidence |
|---|---|---|---|
| Technological Implementation | Exact approval, atomic reservation, durable dispatch identity and independently checked outcomes form a nontrivial service. Actual sandbox capture and response-loss recovery now support the payment path. | The required external capabilities have not worked together: diagnostic selection is fixed, and runtime AI remains unverified. | Genuine model proposal → owner approval → native PayPal approval → capture → original-order verification and receipt, retaining the same evidence discipline as the diagnostic. |
| Design | Six workspace sections organize the next decision around a purchase. State-dependent actions explain expiry, held funds and cancellation. The receipt inspector makes stored field comparisons readable, including the actual diagnostic outcome. | Independent users have not completed the flow. Owner-private access remains a barrier. | Fresh-user setup/access check and a short usability task using the receipt's historical-data limits. |
| Potential Impact | Competing $180/$160 requests against $300 and an ambiguous response form a specific operational problem. Unknown amounts demonstrably stay reserved. | The catalogue is synthetic. No verified customers, saved hours or revenue. The studio story is a hypothesis. | A qualified buyer's current workaround; measured approval/recovery time. Keep pilot goals separate from results. |
| Innovation/Idea | The useful hypothesis connects business authority, shared allowance and recovery evidence through interruption. | Approval controls, idempotency and agent payments already exist. Claims of replacing PayPal or Stripe would reduce credibility. | Show the application decisions left around a payment API and the connected record. Use the comparison in [product strategy](PRODUCT_STRATEGY.md). |
| Presentation | One purchase, competing request and lost response can communicate value within three minutes. | No public video or complete external flow supports the central claim yet. | Actual-source recording, readable amounts/statuses, honest mode labels and clear limits. |

## Verdict and priorities

**I would keep ProofPay in serious technical consideration for its approval and recovery work, now supported by an actual sandbox capture. I would not choose this checkpoint as a winner or call it submission-ready.** Meaningful runtime AI, the combined journey, judge access and presentation still lack decisive evidence. This does not assign a score, assert a Stage One pass or speak for PayPal's judges.

1. Finish one genuine model-to-PayPal sandbox purchase in the application. Record a sanitized receipt and provider/model identifiers. Resolve failures rather than editing around them.
2. Preserve the completed diagnostic's response-loss evidence. Apply the same recovery checks to the genuine model-led workflow once available. Do not count the fixed sample as AI or call browser reload a backend restart.
3. Verify fresh judge access/setup, then record and review the public video. Preserve the reviewed revision and instructions through judging.
4. Use the **implemented read-only receipt inspector** to explain the recorded sandbox purchase-versus-provider comparison, including missing fields and historical approval/item limits. No additional feature outranks closing the AI and access gates; a new adapter, wallet or toolkit migration has lower value now.

The boundary remains one controlled merchant, USD and a per-workspace allowance. Renewal does not extend PayPal order validity. Cancellation releases an unused reservation only before provider dispatch. Unknown create results without an order ID require investigation. There is no production flow, refund execution, webhook receiver, general duplicate-prevention guarantee or externally signed proof.

The longer-term opportunity is a reusable operations layer for a validated purchasing workflow. [Commercial hypotheses](COMMERCIAL_PLAN.md) and [product roadmap](PRODUCT_STRATEGY.md) describe how to test it. Processor parity, customers, valuation and future market share are not established by this prototype.
