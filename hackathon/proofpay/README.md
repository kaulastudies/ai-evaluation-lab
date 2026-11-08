# ProofPay Purchase Desk

**Owner-approved purchases with a shared allowance and a checkable payment outcome.**

A studio has $300 for outside reviews. Two requests cost $180 and $160. ProofPay reserves allowance when the owner approves a specific purchase, keeps uncertain payments reserved, and checks the original provider order before recording payment.

The project is an [AI Evaluation Lab](https://github.com/kaulastudies/ai-evaluation-lab) prototype for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/). GitHub is the source and review home. The current source targets **native Next.js 16, React 19, Node.js 24, Vercel and Neon/PostgreSQL**.

[Judge guide](docs/JUDGES.md) · [Readiness](docs/JUDGE_READINESS.md) · [Development](docs/DEVELOPMENT.md) · [Architecture](docs/ARCHITECTURE.md) · [Security](docs/SECURITY_REVIEW.md) · [QA](docs/QA_REPORT.md) · [Postman collection](postman/README.md)

Current records: [business increment local checks](evidence/business-portal-checks-2026-11-08.json) · [production release, database, CI and browser scope](evidence/business-portal-release-2026-11-08.json). The deployed app remains private, and owner sign-in requires the pending credential setup.

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

## A working desk for a business pilot

**Business settings** saves the business name, one department or cost-centre label, and a default USD allowance. New workspaces retain those values as a snapshot; changing the defaults does not change earlier workspace budgets or approvals. The starting default is $300 when no profile is configured. The allowance is per workspace, not a bank balance or an account-wide spending limit.

**Workspace history** lists the owner's saved workspaces. **Open workspace** is blocked while the active workspace has held or uncertain purchases. The department label does not create users, roles or separate department budgets. **Reset simulated workspace** remains an explicit rehearsal action; earlier records stay in history.

**Purchases → Export CSV** exports all loaded purchases in the active workspace, regardless of the screen filter, with the saved business context, mode, proposal source and status. Formula-leading spreadsheet cells are escaped. This is an application report, not an invoice, signed provider receipt or accounting certification.

Start with [the six-step pilot walkthrough](docs/COMMERCIAL_PLAN.md#first-onboarding-session). GitHub, Vercel and Neon already exist; the immediate access task is authorized owner-key configuration, followed by PayPal sandbox setup when testing payment. No extra sponsor signup or personal OpenAI credits are needed. See [resources and sign-ins](docs/COMMERCIAL_PLAN.md#resources-and-sign-ins-actually-needed).

The business increment has **199 passing local tests**, passing TypeScript, full lint, native and responsive fixture builds, and a zero-finding full dependency audit. The [production release](evidence/business-portal-release-2026-11-08.json) is READY after eight real Neon PostgreSQL checks, repeat migration and build passed. Responsive navigation was checked on the setup-pending shell only; owner sign-in, authenticated forms, CSV file bytes, AI and payment remain unverified.

## Current delivery and evidence

The Vercel migration changes the hosting, database and authentication boundary. Earlier Site results remain useful historical evidence, but do not certify the new deployment.

| Area | Verified or implemented | Remaining gate |
|---|---|---|
| Business increment | Business profiles, immutable workspace context, owned history/selection and CSV report implemented; **199/199 local tests**, types, full lint, both builds and full audit with zero findings. | Production and database checks passed. Authenticated settings/history, exported CSV bytes and purchasing still need the [remaining QA](docs/QA_REPORT.md). |
| Earlier native baseline | The recorded release passed **178/178 local tests**, types, lint, native/visual builds, six real PostgreSQL checks and CI. | This evidence predates the business increment and does not prove its hosted behavior. |
| Dependencies | [Final full audit](evidence/dependency-remediation-2026-11-08-summary.json): **0 known findings**, including development dependencies; parser checks 2/2. | This is a dated lockfile result, not a security certificate. |
| Current Vercel / Neon release | [Production deployment](https://proofpay-purchase-desk.vercel.app) READY at runtime source `1f4d8d6d`; **8/8 real PostgreSQL checks**, migrations and both CI runs passed. | Owner secret transfer needs explicit approval; owner/PayPal configuration and the authenticated hosted workflow remain pending. |
| PayPal | [Historical diagnostic](evidence/diagnostic-release-review.json) on source `17cbededf`: native buyer approval, $180 sandbox capture, response-loss recovery and stable repeated lookup. | No AI participated. Repeat the relevant checks on the current Vercel runtime. |
| Runtime AI | Fixed Vercel free-credit/OIDC route implemented; $4.93 free credit was observed by the release owner. | The selected model is confirmed eligible for free Gateway credit; actual inference and the complete model-to-payment journey remain unverified. |
| Presentation / access | Source, instructions, review materials and [Postman collection](postman/README.md) prepared. Nithya’s Devpost team acceptance was confirmed on 8 November 2026. | Independent application access, public video and final review remain open. Devpost membership does not create a ProofPay user role. **Final Devpost Submit is held.** |

The earlier diagnostic kept $180 reserved after response loss and browser reload; original-order lookup confirmed payment, with $120 available, $0 reserved and $180 paid. Its [record](evidence/diagnostic-release-review.json) identifies the operation/order/capture. External request counts were not independently measured. It used virtual funds, not production money.

Historical interface evidence includes the [readability review and screenshot](evidence/readability-review.json), [mobile screenshot](evidence/mobile-approval-qa.png), [hosted rehearsal](evidence/hosted-renewal-review.json) and [earlier release](evidence/hosted-release-review.json). The [current production record](evidence/business-portal-release-2026-11-08.json) and [screenshot](evidence/business-portal-setup-2026-11-08.jpg) cover all eight navigation headings at 360, 768 and 1280 pixels without horizontal overflow. This was the setup-pending shell: 15px body text, 14px mobile navigation, 48px mobile navigation targets and a visible keyboard outline. Authenticated records/actions and exported file bytes remain unverified; older screenshots are historical.

## Three explicit paths

| Path | Selection and provider | Required configuration |
|---|---|---|
| Rehearsal | Deterministic sample proposals and a durable simulated provider. | Owner session and remote database; no PayPal/model credentials. |
| Standard AI + PayPal sandbox | One validated model proposal, separate owner and native buyer approval, checked provider outcome. | Owner/database, PayPal sandbox and the reviewed Vercel free-credit policy. |
| Manual PayPal diagnostic | One fixed, unapproved $180 workflow review; no model call. | Owner/database and PayPal sandbox. Starting it does not dispatch a payment. |

All paths retain the financial controls. Diagnostic receipts say manual/no-AI; a diagnostic cannot establish the standard AI journey. The current free-credit policy permits one dispatched model attempt per workspace and one total for the reviewed grant, including failures. Personal OpenAI/API keys are rejected; there is no automatic retry or alternate provider. [Funding details](docs/DEVELOPMENT.md#bounded-runtime-ai) distinguish the operator's declaration from billing evidence.

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

Interactive use needs server configuration. There is no simulated sign-in or local-ledger fallback. With a dedicated database and owner variables in an uncommitted `.env.local`, apply the PostgreSQL migrations and use HTTPS:

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

The verifier compares the approval digest, operation, events and provider fields without network access. A pass means an unsigned record is internally consistent. It does not authenticate PayPal, a model, the author, current spending authority or TIP compatibility. See the [provenance roadmap](docs/PROVENANCE_ROADMAP.md).

## Scope and limits

ProofPay currently covers one controlled sample merchant and USD. Each new workspace snapshots the saved default allowance; $300 is the unconfigured starting default, not a universal or account-wide limit. The catalogue is synthetic; no paid review service is delivered. There are no production payments, refunds, webhooks, fulfillment, subscriptions or cancellation after provider dispatch. A lost create response without a saved order ID needs investigation and retains its reservation.

Owner sessions are a private-desk prototype, not a multi-user identity product. Database/admin compromise, broad denial-of-service resistance, compliance, processor parity and a general exactly-once guarantee are not established. The roadmap records evidence needed for broader use; it does not promise a valuation or hackathon result.

## License

ProofPay is maintained within AI Evaluation Lab by Rama Chandra Malayanur and includes an [Apache-2.0 license](LICENSE). Preserve dependency and starter notices. PayPal product names identify the integration and do not imply endorsement.
