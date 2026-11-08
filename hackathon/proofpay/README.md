# ProofPay Purchase Desk


**Owner-approved purchases with a shared allowance and a checkable payment outcome.**

A studio has $300 for outside reviews. Two requests cost $180 and $160. ProofPay reserves allowance when the owner approves a specific purchase, keeps uncertain payments reserved, and checks the original provider order before recording payment.

The project is an [AI Evaluation Lab](https://github.com/kaulastudies/ai-evaluation-lab) prototype for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/). GitHub is the source and review home. The current source targets **native Next.js 16, React 19, Node.js 24, Vercel and Neon/PostgreSQL**.

[Judge guide](docs/JUDGES.md) · [Readiness](docs/JUDGE_READINESS.md) · [Development](docs/DEVELOPMENT.md) · [Architecture](docs/ARCHITECTURE.md) · [Security](docs/SECURITY_REVIEW.md) · [QA](docs/QA_REPORT.md) · [Postman collection](postman/README.md)

Current records: [local checks](evidence/native-vercel-checks-2026-11-08.json) · [Vercel deployment, real database and CI](evidence/native-vercel-release-2026-11-08.json). The deployed app remains private, and owner sign-in requires the pending credential setup.

## Why it is useful

An engineering team adding purchases to an agent workflow needs to connect business authority, shared allowance and payment recovery. A successful checkout alone does not answer who approved the exact purchase or what happens after a missing response.

| Situation | Application behavior | Inspectable record |
|---|---|---|
| Requests compete for an allowance | Approval reserves funds through a conditional database transaction. | Amount, held allowance and approval event. |
| A model proposes an item | The server owns seller, catalogue price and currency; the owner approves separately. | Selected SKU, rationale and limited response provenance. |
| Approval expires | New dispatch is blocked; explicit renewal preserves the reservation and operation. | Version, digest, expiry and renewal event. |
| A capture response disappears | Funds stay reserved; recovery reads the original order. | Stable operation/order/request IDs and checked provider fields. |
| An untouched request is withdrawn | Cancellation retains history and releases an unused reservation once. | Cancelled state and event; no refund is implied. |

The intended first customer is a software team embedding approved purchases in a business process. Reduced integration and investigation work is a commercial hypothesis, not measured customer traction. See [product strategy](docs/PRODUCT_STRATEGY.md) and the [operating roadmap](docs/OPERATING_ROADMAP.md).

## Current delivery and evidence

The Vercel migration changes the hosting, database and authentication boundary. Earlier Site results remain useful historical evidence, but do not certify the new deployment.

| Area | Verified or implemented | Remaining gate |
|---|---|---|
| Native source | Next.js/Node, PostgreSQL adapter, signed owner sessions, migrations and bounded inference policy implemented. The release owner reports **178/178 local tests**, TypeScript, full lint, native build and visual fixture build passed. | Six real PostgreSQL checks passed; authenticated hosted actions remain gated in [QA](docs/QA_REPORT.md). |
| Dependencies | [Final full audit](evidence/dependency-remediation-2026-11-08-summary.json): **0 known findings**, including development dependencies; parser checks 2/2. | This is a dated lockfile result, not a security certificate. |
| Vercel / Neon | [Native Vercel deployment](https://proofpay-purchase-desk.vercel.app) READY; **6/6 real PostgreSQL checks** and both schema migrations passed. | Owner secret transfer needs explicit approval; owner/PayPal configuration and the authenticated hosted workflow remain pending. |
| PayPal | [Historical diagnostic](evidence/diagnostic-release-review.json) on source `17cbededf`: native buyer approval, $180 sandbox capture, response-loss recovery and stable repeated lookup. | No AI participated. Repeat the relevant checks on the current Vercel runtime. |
| Runtime AI | Fixed Vercel free-credit/OIDC route implemented; $4.93 free credit was observed by the release owner. | The selected model is confirmed eligible for free Gateway credit; actual inference and the complete model-to-payment journey remain unverified. |
| Presentation / access | Source, instructions, review materials and [Postman collection](postman/README.md) prepared. | Independent judge access, public video and final review remain open. **Final Devpost Submit is held.** |

The earlier diagnostic kept $180 reserved after response loss and browser reload; original-order lookup confirmed payment, with $120 available, $0 reserved and $180 paid. Its [record](evidence/diagnostic-release-review.json) identifies the operation/order/capture. External request counts were not independently measured. It used virtual funds, not production money.

Historical interface evidence includes the [readability review and screenshot](evidence/readability-review.json), [mobile screenshot](evidence/mobile-approval-qa.png), [hosted rehearsal](evidence/hosted-renewal-review.json) and [earlier release](evidence/hosted-release-review.json). Current navigation, focus and the configuration-unavailable shell were checked at 360, 768 and 1280 pixels without horizontal overflow. Authenticated records/actions remain unverified; old screenshots are not a current deployment check.

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

ProofPay currently covers one controlled sample merchant, USD and a $300 allowance per isolated workspace. The catalogue is synthetic; no paid review service is delivered. There are no production payments, refunds, webhooks, fulfillment, subscriptions or cancellation after provider dispatch. A lost create response without a saved order ID needs investigation and retains its reservation.

Owner sessions are a private-desk prototype, not a multi-user identity product. Database/admin compromise, broad denial-of-service resistance, compliance, processor parity and a general exactly-once guarantee are not established. The roadmap records evidence needed for broader use; it does not promise a valuation or hackathon result.

## License

ProofPay is maintained within AI Evaluation Lab by Rama Chandra Malayanur and includes an [Apache-2.0 license](LICENSE). Preserve dependency and starter notices. PayPal product names identify the integration and do not imply endorsement.
