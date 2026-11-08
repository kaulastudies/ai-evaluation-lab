# ProofPay Devpost draft

Updated **8 November 2026**, reviewing source `c2c5848` and the [configured hosted QA record](../evidence/configured-live-qa-2026-11-08.md). **One actual AI-to-PayPal sandbox purchase and response-loss recovery succeeded.** Independent judge access and a public video remain pending. Use the existing Devpost entry; **do not click final Submit**.

## Project name

ProofPay Purchase Desk

## Short pitch

Owner-approved purchases with a shared allowance, real AI catalogue proposals, and PayPal sandbox recovery that checks the original order before recording payment.

## Story — current checkpoint

### Inspiration

A payment timeout leaves a practical question: did the purchase fail, or did only the response disappear?

We built ProofPay around a small studio with a $300 allowance for outside review work. Two requests cost $180 and $160. Both may be useful, but they cannot both fit. The owner needs to approve the exact purchase, know what remains available and inspect the payment outcome when a response goes missing.

### What it does

ProofPay connects a purchase request, owner approval, allowance reservation and checked provider outcome in one operation. The workspace includes purchases, approvals, evidence, controls, connections, business settings and saved workspace history.

The model proposes a permitted catalogue item and rationale. Server code determines the seller, price and currency; the model cannot approve a purchase or declare payment complete. Owner approval reserves allowance before dispatch. PayPal's native buyer approval is a separate step.

If a capture response disappears, the purchase remains unresolved and its allowance stays reserved. Recovery reads the original order and checks the operation, seller, amount, currency and completed final capture before recording payment. The receipt inspector makes those stored comparisons readable.

Owners can renew expired approval for an unchanged purchase before capture dispatch, or cancel an untouched request before any provider dispatch. Business settings supply a name, department label and default workspace allowance. Those labels do not create user roles or an account-wide budget.

The catalogue contains three synthetic digital-service packages: Workflow review ($180), Design review ($160) and Starter review ($90). No paid review service is delivered. Rehearsal is visibly separate, with deterministic proposals and a simulated provider.

### How we built it

The application uses TypeScript, native Next.js 16 and React 19 on Node.js 24, deployed through GitHub and Vercel with Neon/PostgreSQL. Owner sessions use signed cookies. Approval binds the exact purchase and expiry; a conditional database transaction reserves the allowance. Create and capture request IDs are stored before provider dispatch.

PayPal OAuth and Orders v2 handle order creation, buyer approval, capture and lookup. Confirmation and its limited verification snapshot are persisted together.

The runtime model route uses Vercel AI Gateway with a reviewed free-credit grant and a durable attempt limit. Failed attempts count, and the application does not silently retry or switch to personal provider credentials. The recorded grant has been consumed; we preserve the completed proposal rather than making another model call for filming.

### What we have verified

On 8 November, the deployed application completed a genuine model-to-PayPal sandbox purchase. Gateway evidence records `openai/gpt-4.1-mini` through OpenAI, HTTP200, 242 input tokens and 48 output tokens. Its displayed request cost was USD0.0002. It used the reviewed Vercel free-credit route, with no personal OpenAI key or personal credits.

That proposal became a $180 purchase. The owner approved it, the sandbox buyer completed PayPal's native approval, and the application dispatched capture while deliberately dropping the response. A browser reload retained $180 reserved, $120 available and $0 paid.

A GET of the original order confirmed the matching completed final capture. The result became $180 paid, $0 reserved and $120 available. Repeated lookup retained the same capture and totals. This is one observed sandbox run with virtual funds; aggregate external request counts were not independently measured.

The unchanged reviewed build also retains **199 passing local checks**, passing TypeScript, full lint and builds. Production and preview builds separately passed **eight real PostgreSQL checks and migrations**. Local tests use controlled fixtures and have their own scope; they are not 199 live payments or model calls.

Hosted rehearsal verified competing-request rejection, response-loss recovery and cancellation before dispatch. All eight authenticated sections were checked at 360, 768 and 1280-pixel widths without document overflow. Saved business settings and switching between the preserved rehearsal and sandbox workspaces also passed the observed checks. Browser-exported file bytes remain unverified after the download collection timed out.

### What we learned

The important boundary is between an application decision and an external payment effect. A missing response cannot justify releasing allowance or issuing another purchase. A model's explanation, a return link and a completed provider capture are different kinds of evidence.

The receipt helps inspect the result, but it is unsigned application evidence. Its stored verification schema lacks the historical approval version and catalogue SKU. Matching current fields does not independently prove those historical values, provider authenticity or service fulfillment.

### What comes next

We are preparing an isolated judge rehearsal that can be repeated without owner credentials, model spending or PayPal actions. Its access URL and independence checks are still pending. The video will show persisted evidence from the completed external run and a separately labelled fresh rehearsal. No continuous recording of the original transaction exists.

Beyond the hackathon, the next test is whether owner-led agencies, consultancies or studios will pay for a reusable approval, allowance and recovery workflow. Customer demand, savings and pricing are hypotheses. Production payments, refunds, webhooks, fulfillment, multi-user roles and provider portability remain outside this build.

## Submission references

- [Public source and setup](https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay)
- [Canonical application](https://proofpay-purchase-desk.vercel.app) — currently requires owner access; this is not an independently tested judge-rehearsal link.
- [Actual AI-to-PayPal run](../evidence/configured-live-qa-2026-11-08.md) · [199-test source checkpoint](../evidence/business-portal-checks-2026-11-08.json) · [QA report](QA_REPORT.md)
- [Architecture](ARCHITECTURE.md) · [judge readiness](JUDGE_READINESS.md) · [video narration and scenes](DEMO_SCRIPT.md)

Implemented technology tags: TypeScript, Next.js, React, Node.js, Vercel, Neon, PostgreSQL, Vercel AI Gateway, OpenAI GPT-4.1 mini, PayPal REST APIs, PayPal Orders v2. The Postman collection is authored and checked offline; actual Postman execution is not claimed. Do not list Toolkit, MCP or agent-commerce protocols as implemented integrations without corresponding evidence.

The application was added during the event within the existing AI Evaluation Lab repository. Preserve the starter and dependency notices. Nithya's Devpost team acceptance was confirmed; team membership does not create an application role or establish a particular contribution.

## Final draft gates

| Item | Current state |
|---|---|
| Meaningful runtime AI and PayPal sandbox | Verified once in the same hosted workflow; source/model/order/capture evidence retained. The reviewed model grant is consumed. |
| Independent judge rehearsal | Under design. Actual URL, isolation, fresh-session access and repeatability must be verified before this draft claims availability. |
| Public YouTube video | Pending. Record persisted completed evidence plus clearly labelled fresh rehearsal with a generic stock AI presenter; do not imply an original continuous recording. Add only the actual verified public URL. |
| Video/source consistency | Match the final delivered source and evidence. Update test counts only from a new recorded result. |
| Export claims | Browser file bytes remain unverified. An export toast or an implemented offline verifier is not a successful downloaded-file check. |
| Final Devpost submission | Held. Video publication and draft updates do not authorize final Submit. |

The [official requirements](https://paypalaihackathon.devpost.com/) and [rules](https://paypalaihackathon.devpost.com/rules), reviewed 8 November 2026, require meaningful PayPal/AI use, runnable access, public licensed source and a public YouTube demonstration under three minutes. No prize, production-readiness or general exactly-once claim is made.
