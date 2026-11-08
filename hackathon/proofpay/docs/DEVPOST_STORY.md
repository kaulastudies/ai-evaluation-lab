# ProofPay Devpost draft

Updated **8 November 2026**. One actual AI-to-PayPal sandbox purchase and response-loss recovery succeeded. The public, isolated judge rehearsal is verified. A **163.521-second narrated walkthrough is rendered; its public YouTube URL is pending**. Use the existing Devpost entry; **do not click final Submit**.

## Project name

ProofPay Purchase Desk

## Short pitch

Approve a purchase, reserve its allowance and check what happened when the payment response disappears.

## Story

### Inspiration

A payment timeout leaves a practical question: did the purchase fail, or did only the response disappear?

We built ProofPay around a small studio with a $300 allowance for outside review work. Two requests cost $180 and $160. Both may be useful, but they cannot both fit. The owner needs to approve the exact purchase, see what remains available and inspect the payment outcome when a response goes missing.

### What it does

ProofPay connects a purchase request, owner approval, allowance reservation and checked provider outcome in one operation.

A model proposes an item from a controlled catalogue and explains its choice. Server code determines the seller, price and currency; the model cannot approve a purchase or declare payment complete. Owner approval reserves allowance before dispatch. PayPal's native buyer approval is a separate step.

If a capture response disappears, the purchase remains unresolved and its allowance stays reserved. Recovery reads the original order and checks the operation, seller, amount, currency and completed final capture before recording payment. A receipt inspector makes those stored comparisons readable and shows where information is missing.

Owners can renew expired approval for an unchanged purchase before capture dispatch, or cancel an untouched request before any provider dispatch. The allowance belongs to a workspace, not the owner's entire PayPal account.

The catalogue contains three synthetic digital-service packages: Workflow review ($180), Design review ($160) and Starter review ($90). No paid review service is delivered. The sandbox uses virtual funds.

### Try it as a judge

Open **https://proofpay-evaluation-lab.vercel.app** and choose **Try the demo**. No login or payment credentials are required. Each visitor receives an isolated, temporary rehearsal session.

**Purchase desk** lets you approve a $180 request, see the competing $160 request blocked, simulate a missing capture response, reload and recover the original outcome. **AI & backend** exposes read-only configuration and history. **Evaluation lab** makes the rehearsal checks and their limits visible.

This judge workspace uses deterministic proposals and a simulated provider. It never calls the model or PayPal and cannot spend provider credits. The saved external-run evidence is separate from your own rehearsal. [Repeatable testing instructions](REPEATABLE_TESTING.md) explain the session and usage limits.

### How we built it

The application uses TypeScript, Next.js 16 and React 19 on Node.js 24, deployed through GitHub and Vercel with Neon/PostgreSQL. Owner sessions use signed cookies. Approval binds the exact purchase and expiry; a conditional database transaction reserves the allowance. Create and capture request IDs are stored before provider dispatch.

PayPal OAuth and Orders v2 handle order creation, native buyer approval, capture and lookup. Confirmation and its limited verification snapshot are persisted together. The public judge deployment uses separate rehearsal storage and disables owner routes.

The runtime model route uses Vercel AI Gateway with a reviewed free-credit grant and a durable attempt limit. Failed attempts count; the application does not silently retry or switch to personal provider credentials. The grant's one model attempt has been consumed. We preserve that completed proposal instead of making another model call for a demonstration.

### What we verified

On 8 November, the deployed owner application completed a genuine model-to-PayPal sandbox purchase. Gateway evidence records `openai/gpt-4.1-mini`, HTTP200, 242 input tokens and 48 output tokens, with a displayed USD0.0002 request cost. It used the reviewed Vercel free-credit route, with no personal OpenAI key or personal credits.

That proposal became a $180 purchase. The owner approved it, the sandbox buyer completed PayPal's native approval, and the application dispatched capture while deliberately dropping the response. A browser reload retained $180 reserved, $120 available and $0 paid.

A GET of the original order confirmed the matching completed final capture. The result became $180 paid, $0 reserved and $120 available. Repeated lookup retained the same capture and totals. This is one observed sandbox run; aggregate external request counts were not independently measured.

The current release has **210 passing local checks** and **nine deployed PostgreSQL checks**. The public judge workspace passed **six observed hosted UI checks** and **21 independent HTTPS checks across two guest sessions**, including cross-session isolation, budget blocking, response-loss recovery and repeat lookup. An actual guest receipt downloaded over HTTPS passed the offline consistency verifier. These are separate checks, not 210 live payments or model calls.

The three judge modules were also checked at 360, 768 and 1280-pixel widths: nine views with no horizontal overflow, 16px main text and no captured application warnings or errors. The earlier owner browser CSV/Blob download remains unverified; the successful guest HTTPS receipt check does not replace that missing evidence.

### What we learned

An application decision and an external payment effect need different evidence. A missing response cannot justify releasing allowance or issuing another purchase. A model's explanation, a return link and a completed provider capture are not interchangeable.

The receipt is useful for inspection, but it is unsigned application evidence. Its provider verification snapshot lacks the historical approval version and catalogue SKU. Matching current fields and passing the offline verifier establish limited internal consistency, not provider authenticity, historical authority or service fulfillment.

### What's next

The next commercial test is whether owner-led agencies, consultancies or studios will pay for a reusable approval, allowance and recovery workflow. Customer demand, time savings and pricing remain hypotheses.

The current build covers one controlled seller, US dollars and a workspace allowance. Production payments, refunds, webhooks, fulfillment, multi-user roles and provider portability remain outside this build. Our immediate focus is learning from repeatable evaluations before expanding that scope.

## Video and submission references

- [Public judge workspace — no login](https://proofpay-evaluation-lab.vercel.app)
- [Public source and setup](https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay)
- Public YouTube URL: **pending publication and fresh-viewer verification**.
- [Actual AI-to-PayPal run](../evidence/configured-live-qa-2026-11-08.md) · [independent judge HTTPS evidence](../evidence/judge-hosted-qa-2026-11-08.json) · [repeatable testing](REPEATABLE_TESTING.md)
- [Architecture](ARCHITECTURE.md) · [judge readiness](JUDGE_READINESS.md) · [exact narration and scenes](DEMO_SCRIPT.md)

The rendered video is an edited walkthrough of saved evidence from the completed external run plus actual captured states from a separate fresh rehearsal. No continuous recording of the original transaction exists. Its original illustrated presenter uses offline Flite speech and actual phoneme timing for mouth animation. No HeyGen generation or avatar-service credits were used. The presenter does not portray a team member or PayPal representative.

Implemented technology tags: TypeScript, Next.js, React, Node.js, Vercel, Neon, PostgreSQL, Vercel AI Gateway, OpenAI GPT-4.1 mini, PayPal REST APIs, PayPal Orders v2. The Postman collection is authored and checked offline; actual Postman execution is not claimed. Do not list Toolkit, MCP or agent-commerce protocols as implemented integrations without corresponding evidence.

The application was added during the event within the existing AI Evaluation Lab repository. Preserve the starter and dependency notices. Nithya's Devpost team acceptance was confirmed; team membership does not create an application role or establish a particular contribution.

## Final draft gates

| Item | Current state |
|---|---|
| Meaningful runtime AI and PayPal sandbox | Verified once in the same hosted workflow. Model/order/capture evidence retained; the reviewed model grant is consumed. |
| Independent judge access | Verified at the public URL above, with temporary isolated rehearsal sessions and no live provider calls. |
| Public YouTube video | A 163.521-second file is rendered and mechanically validated. Public upload, exact URL and fresh-viewer playback remain pending. |
| Video/source consistency | Narration states 210 local checks and clearly separates saved external-run evidence from a fresh simulation. Review the final public asset before pasting its URL. |
| Receipt export | Actual guest HTTPS receipt download and offline consistency check passed. Owner browser CSV/Blob file bytes remain unverified. |
| Final Devpost submission | **Held.** Video publication and draft updates do not authorize final Submit. |

The [official requirements](https://paypalaihackathon.devpost.com/) and [rules](https://paypalaihackathon.devpost.com/rules), reviewed 8 November 2026, require meaningful PayPal/AI use, runnable access, public licensed source and a public YouTube demonstration under three minutes. No prize, production-readiness or general exactly-once claim is made.
