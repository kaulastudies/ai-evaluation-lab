# ProofPay Devpost draft

Updated **8 November 2026** during the GitHub/Vercel/Neon migration. The 151-test result and fixed-sample PayPal sandbox capture/recovery on earlier source `17cbededf` are historical; no model participated. Current owner/PayPal configuration, migrated hosted behavior and runtime AI remain unverified. **Use the existing Devpost entry and do not click final Submit.**

## Project name

ProofPay Purchase Desk

## Short pitch

An AI-assisted purchase desk connecting owner approval, a shared allowance and payment evidence, with a PayPal sandbox adapter and recovery when a response is lost.

## Story — current checkpoint

### Inspiration

A payment timeout leaves a practical question: did the purchase fail, or did only the response disappear?

We built ProofPay around a small studio with a $300 allowance for outside review work. Two assistants request packages costing $180 and $160. Both requests may be reasonable, but they cannot both fit. The owner needs to approve the right purchase, see what remains available and find out what happened when a payment response goes missing.

### What it does

ProofPay keeps the proposal, owner approval, allowance reservation and payment outcome in one operation record. Its workspace shows purchases needing attention, approvals, evidence, enforced controls and integration configuration. Business settings save an identity, department label and default per-workspace allowance; new workspaces snapshot those values. Owned history and an active-workspace CSV report make earlier work inspectable. These features do not create multi-user roles, accounting certification or an account-wide budget.

The demonstration catalogue contains Workflow review ($180), Design review ($160) and Starter review ($90). These are synthetic packages; no paid review service is delivered. After the owner reserves $180, the competing $160 request is blocked. A cheaper alternative is a new proposal requiring its own approval.

An expired approval can be explicitly renewed before capture dispatch without changing the purchase, provider order or reservation. A request can also be cancelled before any provider dispatch, releasing an unused local reservation while retaining its history.

The PayPal sandbox path creates an order and requires the buyer's native PayPal approval. If a capture response is lost, ProofPay keeps the amount reserved and checks the original order. It records payment only when the expected operation, merchant, amount, currency and completed final capture match. Another outcome check does not dispatch another capture.

### How we built it

The current source uses TypeScript, native Next.js 16/React 19 on Node.js 24 and remote Neon/PostgreSQL, with GitHub for source and Vercel for the selected deployment. Signed owner-session cookies replace the earlier ingress-header authentication. The model adapter requests a catalogue SKU and explanation through a fixed Vercel free-credit/OIDC route. Server code validates the selection and supplies the price and merchant; the model cannot approve a purchase, change the allowance or declare a payment complete.

Owner approval binds the exact purchase and expiry. An atomic database decision reserves the shared allowance. Separate create and capture request IDs are stored before dispatch. PayPal OAuth and Orders v2 provide order creation, capture and subsequent lookup. Application approval and PayPal buyer approval are separate decisions.

Confirmation stores the limited provider fields used for verification alongside the accounting change. The receipt inspector compares current purchase fields with those stored observations, making matching, different and missing values visible. The verification record does not retain the historical approval version or catalogue item, and the interface states those limits.

Versioned exports include the operation, approval binding and digest, request IDs, events and verification records. An offline verifier checks their internal consistency. These are inspectable application records, not signed PayPal attestations; replacing both data and digest could produce another internally consistent file.

Inference requires a reviewed grant and expiry, one durable attempt per workspace and a configured total (currently one). Failed attempts count; there is no automatic retry, direct personal API-key route or provider fallback. These controls bound requests; actual billing and model execution still require evidence.

Rehearsal is a visibly separate mode with deterministic proposals and a persisted simulated provider. Missing configuration never silently substitutes rehearsal for a sandbox action.

### The hard part

The difficult boundary is between a durable application decision and an external payment effect. A missing response cannot justify releasing the allowance or sending a second purchase. Competing approvals also need one atomic reservation decision, rather than separate reads of an outdated balance.

We tested the application service with separate processes contending for allowance and a fresh process reopening saved state after response loss. Renewal and cancellation use conditional state/version checks so stale authority cannot override a competing action.

### What we have verified

The earlier runtime recorded **151/151 local tests passed** after its diagnostic changes. The suite uses SQLite with a D1-contract adapter, synthetic provider/model fixtures and mocked HTTP. It covers concurrency, process restart, approval, renewal, cancellation before dispatch, transactional audit writes, owner isolation, bounded requests/responses and offline receipt consistency. Earlier 131- and 92-test records remain historical evidence. These local results are separate from external execution.

At that historical checkpoint, full application TypeScript and ESLint checks also passed. Local visual review checked the revised typography at 360, 390, 768 and 1280px without page-level horizontal overflow and verified keyboard scrolling. The implemented receipt inspector was reviewed at 360/390px with a synthetic record. These are local interface checks, not a hosted or physical-device payment demonstration.

The earlier private hosted rehearsal separately verified real approval expiry, disabled capture, explicit renewal with the same order and reservation, and recovery after a simulated capture response was dropped and the browser reloaded. It finished with $180 paid and $120 available. Another hosted check verified that cancelling an approved $90 request before dispatch restored its reservation and retained its history.

A later hosted run blocked a $160 request against that remaining $120, then created a separate $90 alternative requiring its own approval. Dropping the simulated capture response left $90 reserved through reload. Checking the original order confirmed the purchase, leaving $270 total paid and $30 available; a repeated check preserved the same capture and totals. The UI reported four exported purchase records, but the downloaded file contents were not verified. This run observed application behavior with a simulated provider, not actual PayPal activity or provider-call counts.

We then completed a **genuine PayPal sandbox diagnostic** on the earlier Site deployment, source `17cbededf`. It used one fixed $180 Workflow review, with explicit owner approval and native sandbox buyer approval. We enabled the application's deliberate capture-response drop. The outcome stayed unresolved through browser reload, retaining $180 reserved, $120 available and no recorded spend. A GET of the original order then confirmed the matching completed final capture. Repeating the lookup retained the same capture and eight operation events; a further reload showed $180 paid, $0 reserved and $120 available. The UI observation does not independently measure provider request counts.

**That diagnostic called no AI model and does not certify the new deployment.** The [business increment local checks](../evidence/business-portal-checks-2026-11-08.json) pass 199 tests, types, full lint and both builds. The [production release](../evidence/business-portal-release-2026-11-08.json) is READY after eight real PostgreSQL checks, repeat migration, build and both CI runs passed. Responsive browser checks cover only the setup-pending shell; authenticated forms and purchasing remain unverified. The dependency audit reports zero known findings, including development dependencies; its parser compatibility checks passed. See [current QA](QA_REPORT.md) for the migration checks. Meaningful runtime AI, the complete model-to-PayPal journey, new owner/PayPal configuration and independent judge access remain unverified. The public demonstration video remains unfinished. Sandbox uses virtual accounts and funds; this was not a production payment.

### What we learned and what comes next

Payment status needs evidence. A successful HTTP response, an assistant's explanation and a completed provider capture mean different things; the product must keep those distinctions visible.

Our next step is to validate the migrated Vercel/Neon workflow, then complete a genuine model proposal and PayPal purchase within the reviewed free-credit allowance. We will retain the same recovery checks, verify judge access and record the public demonstration. Beyond the hackathon, we want to test whether owner-led service businesses will pay for a bounded approval and payment-evidence workflow, using the [sandbox pilot plan](COMMERCIAL_PLAN.md). That is a customer hypothesis, not existing traction.

The current scope is one merchant, USD and an isolated workspace allowance. Renewal does not extend PayPal order validity. Cancellation is unavailable after provider dispatch and is not a refund. Unknown create results without a saved order ID require investigation. Production payments, refunds, webhooks, fulfillment and provider portability remain outside this build.

## Submission references and remaining gates

- [Public project branch](https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay) · [draft pull request](https://github.com/kaulastudies/ai-evaluation-lab/pull/53)
- [Setup](../README.md) · [judge readiness](JUDGE_READINESS.md) · [architecture](ARCHITECTURE.md)
- [Verified sandbox diagnostic](../evidence/diagnostic-release-review.json) · [QA report](QA_REPORT.md)
- [Earlier 131-test QA summary](../evidence/qa-2026-11-08-summary.json) · [historical test log](../evidence/qa-2026-11-08-test-output.log)
- [Hosted renewal](../evidence/hosted-renewal-review.json) · [hosted workspace](../evidence/hosted-workspace-review.json) · [hosted recovery](../evidence/hosted-recovery-review.json) · [earlier responsive review](../evidence/responsive-review.json)
- [Current business production release](../evidence/business-portal-release-2026-11-08.json): READY, eight real PostgreSQL checks and repeat migration passed, with responsive checks limited to the setup-pending shell. Authenticated access remains pending. [QA](QA_REPORT.md) separates this from historical evidence.
- [Native dependency evidence](../evidence/dependency-remediation-2026-11-08-summary.json) · [Postman development collection](../postman/README.md)

Suggested source technology tags: TypeScript, React, Next.js, Node.js, PostgreSQL, Neon, Vercel, PayPal REST APIs and PayPal Orders v2. The Postman collection is authored and checked offline; actual Postman execution is not yet claimed. Add the runtime model/provider only after its actual invocation. Do not claim Toolkit, MCP, agent-commerce protocol compatibility or optional sponsor integrations that are absent from the code.

The ProofPay application was added during the event within an existing repository. Identify the new application work and preserve starter/dependency notices. Do not claim the parent repository or every dependency was newly created.

| Gate | Evidence needed before changing the story |
|---|---|
| Runtime AI | Named provider/model, run date, validated proposal and matching operation; no secrets or raw unrelated response data. |
| Sandbox capture and response loss | **Historically verified for the fixed no-AI diagnostic on the former runtime:** native buyer approval, completed capture, held allowance through reload, original-order GET and stable repeat lookup. This does not establish the standard model-led journey. |
| Combined AI-to-PayPal purchase | A genuine model proposal followed by owner/native buyer approvals, capture and checked receipt in the same application workflow. |
| Source and reproduction | Final reviewed revision, matching evidence, applicable checks and fresh judge setup/access verification. Preserve labels distinguishing simulated, local and external runs. |
| Presentation | Public YouTube URL under three minutes showing the actual build, with English narration or captions and permitted assets. |
| Team and final review | Nithya’s team acceptance was confirmed on 8 November 2026; verify representative authority and final entry fields. Keep final Submit on hold until the owner explicitly releases it. |

The [official requirements](https://paypalaihackathon.devpost.com/), [rules](https://paypalaihackathon.devpost.com/rules) and [resources](https://paypalaihackathon.devpost.com/resources) were rechecked on 8 November 2026. PayPal REST plus meaningful AI is a permitted approach; Toolkit/MCP is optional. The deadline is 12 November 2026 at noon PST. Full criteria, date details and the current choose/not-choose assessment are in [JUDGE_READINESS.md](JUDGE_READINESS.md).
