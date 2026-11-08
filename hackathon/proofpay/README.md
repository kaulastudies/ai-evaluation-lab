# ProofPay Purchase Desk

**Owner-approved purchases with a shared allowance and a checkable payment outcome.**

A studio has $300 for outside reviews. Two requests cost $180 and $160. ProofPay reserves allowance when the owner approves a specific purchase, keeps uncertain payments reserved, and checks the original provider order before recording payment.

The project is an [AI Evaluation Lab](https://github.com/kaulastudies/ai-evaluation-lab) prototype for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/). GitHub is the source and review home. The current source targets **native Next.js 16, React 19, Node.js 24, Vercel and Neon/PostgreSQL**.

[Judge guide](docs/JUDGES.md) · [Readiness](docs/JUDGE_READINESS.md) · [Development](docs/DEVELOPMENT.md) · [Architecture](docs/ARCHITECTURE.md) · [Security](docs/SECURITY_REVIEW.md) · [QA](docs/QA_REPORT.md) · [Postman collection](postman/README.md)

Current records: [actual AI-to-PayPal run](evidence/configured-live-qa-2026-11-08.md) · [seven-view browser QA](evidence/judge-portal-browser-qa-2026-11-08.json) · [local source checks](evidence/judge-portal-source-qa-2026-11-08.json) · [earlier independent HTTPS QA](evidence/judge-hosted-qa-2026-11-08.json). The current public workflow reached 6/6 observations, all seven views passed 21 responsive checks, and the deployment passed nine real PostgreSQL checks. The replacement Kokoro V2 video is frozen at **141.354362 seconds**, with full decode/audio/caption checks and sampled visual review passed. Manual YouTube upload remains pending; **final Devpost Submit stays held**.

## Open the public judge workspace

Use **[proofpay-evaluation-lab.vercel.app](https://proofpay-evaluation-lab.vercel.app)** for judging. No Vercel account, owner login, PayPal account or API key is needed. Choose **Open judge workspace** to enter the seven-view portal. Its complete simulated browser workflow passed on runtime `cfd1d007`; all seven views have responsive evidence. Follow the [judge guide](docs/JUDGES.md) to try the app; technical setup is optional.

Each visitor receives a signed, two-hour guest session and a separate simulated $300 workspace. Approve $180, try the competing $160 request, create the simulated order, deliberately drop its capture response, reload, and verify the original outcome. Use **Continue workflow** to reach the next action. If a prior demo is complete, choose **Start fresh demo → Confirm fresh demo** from any loaded section. **New sample request** creates a deterministic proposal; **Evidence** provides the in-app receipt inspector and **Export all receipts**. “Judge administrator” means control of that guest rehearsal only; it grants no owner, production or account administration.

The judge project uses its own PostgreSQL database and judge-session secret. Its API constructs only a durable simulated provider and deterministic sample proposals; it does not read owner/PayPal/AI credentials or obtain Gateway OIDC. Owner APIs and sign-in are disabled on that deployment. The private owner deployment and the recorded real sandbox purchase remain separate.

| Public rehearsal limit | Enforced scope |
|---|---|
| Session lifetime | Two hours, kept in a Secure/HttpOnly/SameSite=Strict guest cookie. |
| Actions and resets | Up to 100 mutations and 10 simulated resets per guest session. |
| New guest sessions | At most 60 per hour and 300 total for the deployment. |
| External calls | No live model or PayPal calls; no paid credit or new inference grant. |

The [seven-view source checkpoint](evidence/judge-portal-source-qa-2026-11-08.json), `26893ed6`, passed **210/210 local tests**, TypeScript, full lint and the native build. Current runtime `cfd1d007` passed both CI workflows and **9/9 real PostgreSQL checks with no skips**, committed migrations, TypeScript and the Next.js 16.4.5 build. The [browser review](evidence/judge-portal-browser-qa-2026-11-08.json) completed the six-observation recovery flow with an empty captured application console. All seven views were measured at 360/768/1280px: **21 layouts without horizontal overflow**, with 16px main text. Layout measurements were taken at `26893ed6`; the later commit changes preferred workflow selection only.

The seven-view portal upgrade provides:

| View | What it shows |
|---|---|
| Overview | Allowance, unresolved purchases and the next action. |
| Purchases | Saved requests, order/capture actions and recovery. |
| Approvals | Review and approve exact purchases within the allowance. |
| Evidence | Inspect recorded decisions and provider observations; export simulated JSON receipts. |
| Controls | Read the enforced rules and start a fresh simulation when a prior demo is complete. |
| AI & backend | Read-only rehearsal limits and the dated owner run’s model/payment route. It cannot change providers, display secrets or perform a live connection check. |
| Evaluation lab | Six workflow observations: approval, competing allowance block, response drop, reload preservation, original-outcome verification and stable repeated check. Saved server records support the first checks; reload/repeat observations are browser comparisons, not a backend restart or independent audit. |

“Not yet observed” is not a failed test. The lab links dated source-test and genuine sandbox evidence separately from the current simulated session.

The preceding three-view judge release passed **210/210 local tests**, TypeScript, full ESLint and the native Next.js build. The [measured testing record](docs/REPEATABLE_TESTING.md#measured-checkpoint) keeps these results separate from the earlier 199-test owner checkpoint. The deployed release then passed **9/9 real PostgreSQL checks**, migrations and build. The [independent HTTPS review](evidence/judge-hosted-qa-2026-11-08.json) passed all **21 expected outcomes**, including two-guest isolation, denied owner/sandbox/cross-origin actions, response-loss recovery and retained prior receipts after a guest reset. The [browser review](evidence/judge-browser-qa-2026-11-08.json) completed all **6/6 lab observations** and checked all three views at 360/768/1280px: nine layouts, no horizontal overflow, 16px main text and no collected application warnings/errors. These remain the earlier three-view release results. The new seven-view browser and layout checks are recorded separately above; the two sets of 21 checks are not the same measurements. The prior zero-finding dependency audit retains its original scope.

These are bounded free-demo limits, not unlimited testing availability. The existing [real AI-to-PayPal run](evidence/configured-live-qa-2026-11-08.md) is linked evidence, not replayed by the judge demo. Its reviewed one-attempt model grant remains consumed. A simulation reset never resets that grant or a real payment.

## Why it is useful

An engineering team adding purchases to an agent workflow needs to connect business authority, shared allowance and payment recovery. A successful checkout alone does not answer who approved the exact purchase or what happens after a missing response.

| Situation | Application behavior | Inspectable record |
|---|---|---|
| Requests compete for an allowance | Approval reserves funds through a conditional database transaction. | Amount, held allowance and approval event. |
| A model proposes an item | The server owns seller, catalogue price and currency; the owner approves separately. | Selected SKU, rationale and limited response provenance. |
| Approval expires | New dispatch is blocked; explicit renewal preserves the reservation and operation. | Version, digest, expiry and renewal event. |
| A capture response disappears | Funds stay reserved; recovery reads the original order. | Stable operation/order/request IDs and checked provider fields. |
| An untouched request is withdrawn | Cancellation retains history and releases an unused reservation once. | Cancelled state and event; no refund is implied. |

The first business pilot targets an owner-led agency, consultancy or studio that needs to approve outside services and inspect payment outcomes. Reduced approval and investigation work is a hypothesis, not measured customer traction. The [business pilot plan](docs/COMMERCIAL_PLAN.md) defines onboarding, required sign-ins, acceptance and explicitly unvalidated pricing.

## Private owner features for a business pilot

**Business settings** saves the business name, one department or cost-centre label, and a default USD allowance. New workspaces retain those values as a snapshot; changing the defaults does not change earlier workspace budgets or approvals. The starting default is $300 when no profile is configured. The allowance is per workspace, not a bank balance or an account-wide spending limit.

**Workspace history** lists the owner's saved workspaces. **Open workspace** is blocked while the active workspace has held or uncertain purchases. The department label does not create users, roles or separate department budgets. **Reset simulated workspace** remains an explicit rehearsal action; earlier records stay in history.

**Purchases → Export CSV** exports all loaded purchases in the active workspace, regardless of the screen filter, with the saved business context, mode, proposal source and status. Formula-leading spreadsheet cells are escaped. This is an application report, not an invoice, signed provider receipt or accounting certification.

Start with [the six-step pilot walkthrough](docs/COMMERCIAL_PLAN.md#first-onboarding-session). GitHub, Vercel and Neon are configured, and owner/PayPal server configuration is now saved. Hosted owner sign-in and the business profile were verified. No extra sponsor signup or personal OpenAI credits were used; the reviewed model grant is consumed, so preserve the recorded run rather than issuing another proposal. See [resources and sign-ins](docs/COMMERCIAL_PLAN.md#resources-and-sign-ins-actually-needed).

The earlier owner runtime recorded **199 passing local tests**, passing TypeScript, full lint, native and responsive fixture builds, and dated zero-finding full dependency audit. The [configured release](evidence/configured-live-qa-2026-11-08.md) is READY after eight real Neon PostgreSQL checks and migrations passed in both builds. Hosted owner sign-in, saved business settings, rehearsal recovery and one actual AI-to-PayPal sandbox purchase passed. Browser CSV file bytes remain unverified. Public judge access and independent two-guest isolation have their separate rehearsal results above.

## Current delivery and evidence

The latest [configured hosted record](evidence/configured-live-qa-2026-11-08.md) supersedes earlier pending configuration/AI/payment status. Older reports retain their dated scope; their setup-pending browser observations and former Site results are historical evidence.

| Area | Verified or implemented | Remaining gate |
|---|---|---|
| Business increment | Business profiles, immutable workspace context, owned history/selection and CSV report implemented; **199/199 local tests**, types, full lint, both builds and full audit with zero findings. | Hosted sign-in, saved profile and purchasing passed. Browser CSV bytes, complete history/user-access checks and customer validation remain open. |
| Earlier native baseline | The recorded release passed **178/178 local tests**, types, lint, native/visual builds, six real PostgreSQL checks and CI. | This evidence predates the business increment and does not prove its hosted behavior. |
| Dependencies | [Final full audit](evidence/dependency-remediation-2026-11-08-summary.json): **0 known findings**, including development dependencies; parser checks 2/2. | This is a dated lockfile result, not a security certificate. |
| Verified private owner release | [Private owner workspace — not judge access](https://proofpay-purchase-desk.vercel.app) READY at public source `d17ec6c9`, runtime unchanged; **8/8 real PostgreSQL checks** and migrations passed in production and preview builds. Owner/PayPal configuration is saved and owner sign-in passed. | This protected URL is for the owner. Judges use the public evaluation-lab URL above. Earlier CI/source results retain their own scope. |
| PayPal | [Current combined run](evidence/configured-live-qa-2026-11-08.md): model proposal, owner/native buyer approvals, USD180 sandbox capture, response-loss hold through reload and original-order confirmation. Repeated lookup retained the same capture/totals. | Virtual funds only; no production settlement or general exactly-once guarantee. External request counts were not independently measured. |
| Runtime AI | Vercel Gateway recorded HTTP200 for `openai/gpt-4.1-mini` through OpenAI: 242 input / 48 output tokens, USD0.0002 displayed cost. Its proposal continued into the verified sandbox purchase. | The one-attempt reviewed grant is consumed. Do not reset or retry it to stage another demonstration; no personal OpenAI credits were used. |
| Public judge access | [Canonical public demo](https://proofpay-evaluation-lab.vercel.app), runtime `cfd1d007`: complete 6/6 browser workflow, 21 seven-view responsive checks at layout-equivalent `26893ed6`, empty captured app console and current 9/9 PostgreSQL gate. | Earlier 21 two-guest HTTPS outcomes retain their dated isolation scope. Usage limits apply; no live inference or PayPal call is available. Browser export/download remains separate. |
| Presentation / access | Frozen V2 video: 141.354362 seconds, 312 exact narration words, 43 captions and 29 timed shots. Full decode/audio/caption checks and sampled visual review passed. Source, instructions and the current Devpost draft are saved; Nithya’s acceptance is confirmed. | Manual MP4 selection, public YouTube upload and fresh-viewer playback remain pending. No independent listening or forced-alignment result is claimed. The old Flite cut was rejected. **Final Devpost Submit is held.** |

The current combined run kept USD180 reserved after response loss and reload. Original-order lookup confirmed payment, leaving USD120 available, USD0 reserved and USD180 paid; repeat lookup preserved the same capture. The [configured QA record](evidence/configured-live-qa-2026-11-08.md) contains model/order/capture identifiers and receipt limits. The [older no-AI diagnostic](evidence/diagnostic-release-review.json) remains a separate historical run.

Historical interface evidence includes the [readability review and screenshot](evidence/readability-review.json), [mobile screenshot](evidence/mobile-approval-qa.png), [hosted rehearsal](evidence/hosted-renewal-review.json) and [earlier release](evidence/hosted-release-review.json). The [earlier production record](evidence/business-portal-release-2026-11-08.json) and [screenshot](evidence/business-portal-setup-2026-11-08.jpg) cover all eight navigation headings at 360, 768 and 1280 pixels without horizontal overflow. This was the setup-pending shell: 15px body text, 14px mobile navigation, 48px mobile navigation targets and a visible keyboard outline. The later configured run opened all eight authenticated sections at 360/768/1280 with no horizontal document overflow, and verified history selection between the preserved rehearsal and sandbox workspaces. Exported browser file bytes remain unverified; these screenshots keep their historical scope.

## Demonstration video

The previous 163.521-second Flite/vector-presenter render was **rejected for voice and presentation and will not be published**. Its mechanical checks did not establish acceptable narration or viewing quality.

The replacement **[V2 source and reproduction guide](tools/demo-video-v2/README.md)** uses locally generated Kokoro `af_heart` neural speech and actual captured UI states, with no avatar, paid speech service or personal API credits. The frozen `proofpay-v2-review-cut.mp4` is **141.354362 seconds (2:21.354)** and 7,744,891 bytes: H.264 1920×1080 at 30fps with AAC 48kHz mono audio. Full decode passed; decoded peak was −1.969 dBFS with zero clipped samples. Its **43 captions preserve 312 exact words**, across 29 timed shots; scene six clearly identifies saved evidence from the completed external run. Sampled visual review passed. No independent listening or forced-alignment result is claimed.

[Final metadata and narration](docs/DEMO_SCRIPT.md) record the frozen file hash and verification boundaries. This is an edited walkthrough, not continuous footage of the original external transaction. **Public YouTube URL: pending manual MP4 selection/upload and fresh-viewer verification.** The previous `tools/demo-video` pipeline is historical and rejected; use `tools/demo-video-v2` for the current version. No new live model or PayPal call was made to produce V2.

## Runtime paths

| Path | Selection and provider | Required configuration |
|---|---|---|
| Public judge rehearsal | Deterministic sample proposals and a durable simulated provider. | Temporary guest session created in the app; no account, owner key or provider credentials. |
| Private owner rehearsal | The same simulated purchase controls in the owner desk. | Owner session and remote database; no PayPal/model credentials. |
| Standard AI + PayPal sandbox | One validated model proposal, separate owner and native buyer approval, checked provider outcome. | Owner/database, PayPal sandbox and the reviewed Vercel free-credit policy. |
| Manual PayPal diagnostic | One fixed, unapproved $180 workflow review; no model call. | Owner/database and PayPal sandbox. Starting it does not dispatch a payment. |

All paths retain the financial controls. Diagnostic receipts say manual/no-AI; a diagnostic cannot establish the standard AI journey. The free-credit policy permits one dispatched model attempt per workspace and one total for the reviewed grant, including failures. That reviewed grant was consumed by the recorded successful run; do not reset it or make another model call for repetition. Personal OpenAI/API keys are rejected; there is no automatic retry or alternate provider. [Funding details](docs/DEVELOPMENT.md#bounded-runtime-ai) distinguish the operator's declaration from billing evidence.

## Install and check the source

Use Node.js **24.x**. From a clean checkout:

```sh
git clone --branch proofpay/purchase-desk-v0.1 https://github.com/kaulastudies/ai-evaluation-lab.git
cd ai-evaluation-lab/hackathon/proofpay
npm run install:ci
npx tsc --noEmit
npm run lint
npm test
npm run build
node tests/responsive/build.mjs
```

These local checks do not make a model or PayPal call. The separate live PostgreSQL gate requires an explicitly configured test connection. The [development guide](docs/DEVELOPMENT.md) explains its isolated schema, migrations, owner-key setup, HTTPS development and Vercel release checks.

Developers running a private owner instance need server configuration; judges can use the public workspace above without this setup. There is no simulated owner sign-in or local-ledger fallback. With a dedicated database and owner variables in an uncommitted `.env.local`, apply the PostgreSQL migrations and use HTTPS:

```sh
node --env-file=.env.local scripts/migrate-postgres.mjs
npm run dev -- --experimental-https
```

Set `APP_ORIGIN=https://localhost:3000` for that local server. Use the printed HTTPS address and sign in with the dedicated owner key. Do not use the old Wrangler/D1 migration or Sites sign-in instructions for this runtime.

## Inspect the API and receipts

The [Postman collection](postman/proofpay.postman_collection.json) covers login/logout, workspace, proposal, approval, cancellation, renewal and evidence requests. It uses a local Vault placeholder and HTTPS cookie jar, contains no credentials, and defaults to rehearsal. Its schema and scripts were checked offline; actual Postman execution is not yet claimed.

A version 1 receipt can also be checked offline:

```sh
node scripts/verify-receipt.mjs /path/to/receipt.json
```

The [independent HTTPS review](evidence/judge-hosted-qa-2026-11-08.json) downloaded a 4,254-byte guest receipt from the evidence API and passed this verifier. That checks actual API response bytes; it does not verify the browser’s Blob export or CSV download.

The verifier compares the approval digest, operation, events and provider fields without network access. A pass means an unsigned record is internally consistent. It does not authenticate PayPal, a model, the author, current spending authority or TIP compatibility. See the [provenance roadmap](docs/PROVENANCE_ROADMAP.md).

## Scope and limits

ProofPay currently covers one controlled sample merchant and USD. Each new workspace snapshots the saved default allowance; $300 is the unconfigured starting default, not a universal or account-wide limit. The catalogue is synthetic; no paid review service is delivered. There are no production payments, refunds, webhooks, fulfillment, subscriptions or cancellation after provider dispatch. A lost create response without a saved order ID needs investigation and retains its reservation.

Owner sessions are a private-desk prototype, not a multi-user identity product. Database/admin compromise, broad denial-of-service resistance, compliance, processor parity and a general exactly-once guarantee are not established. The roadmap records evidence needed for broader use; it does not promise a valuation or hackathon result.

## License

ProofPay is maintained within AI Evaluation Lab by Rama Chandra Malayanur and includes an [Apache-2.0 license](LICENSE). Preserve dependency and starter notices. PayPal product names identify the integration and do not imply endorsement.
