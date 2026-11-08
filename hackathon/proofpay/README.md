# ProofPay Purchase Desk

**Owner-approved purchases with a shared allowance and a checkable payment outcome.**

ProofPay connects a purchasing request to the owner's approval, a durable operation and the payment provider's reported result. It is an AI Evaluation Lab prototype for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/).

A studio has a $300 allowance. Two assistants request reviews costing $180 and $160. Both requests may be useful, but approving both would exceed the allowance. ProofPay reserves funds when the owner approves a specific purchase. If a capture response disappears, it keeps the money reserved and checks the original order before recording payment.

[Judge guide](docs/JUDGES.md) · [Requirements and readiness](docs/JUDGE_READINESS.md) · [Development guide](docs/DEVELOPMENT.md) · [Architecture](docs/ARCHITECTURE.md) · [Security review](docs/SECURITY_REVIEW.md) · [QA report](docs/QA_REPORT.md)

## Why this is useful

An engineering team adding agent-driven purchases needs more than a successful checkout. It needs to know who authorized the action, whether other requests have already used the allowance, and what to do when the outcome is uncertain.

| Situation | ProofPay's behavior | What can be inspected |
|---|---|---|
| Two requests compete for one allowance | The server atomically reserves the approved amount. | Purchase state, held allowance and approval event. |
| A model chooses an item | The server supplies the permitted seller, price and currency. The owner grants approval separately. | Selected SKU, proposal source and available model-response identifiers. |
| Approval expires | New dispatch is blocked; funds remain held. Explicit renewal preserves the purchase and reservation. | Approval version, digest, expiry and renewal event. |
| A capture response is missing | The purchase stays unresolved. Recovery reads the original order without a new capture. | Stable operation/order/request IDs and provider verification records. |
| The owner withdraws an untouched request | Cancellation keeps its history and releases an approved reservation once. | Cancelled state and cancellation event; no refund is implied. |

The first intended user is a software team embedding approved purchases into a business workflow. The commercial hypothesis is that a reusable approval, reservation and recovery layer reduces integration and investigation work. Customer demand and willingness to pay still need validation. See the [product strategy](docs/PRODUCT_STRATEGY.md) and [pilot plan](docs/COMMERCIAL_PLAN.md).

## What exists today

The application has six connected views: Overview, Purchases, Approvals, Evidence, Controls and Connections. Purchases can be searched by item or reference; each record exposes its available next action and activity history. An on-demand receipt panel compares approved and observed fields, labels missing information and reads stored evidence without another provider call. Server-side services own the financial state. The browser and model cannot declare a payment successful.

Two modes are kept explicit:

| Mode | What runs | What it proves |
|---|---|---|
| Rehearsal | Deterministic catalogue selection and a durable simulated provider. No external credentials are needed. | Application workflow, persistence, allowance enforcement and the documented recovery scenarios. |
| PayPal sandbox | Configured model adapter, PayPal test merchant, native buyer approval and checked provider evidence. | Only the externally executed and recorded steps; configuration alone proves none of them. |

**This is a prototype, not a production payment service.** Genuine PayPal sandbox OAuth and create/GET calls have passed through the provider adapter. A genuine model invocation and buyer-approved PayPal capture remain unverified. The hosted application is owner-private and is not yet independently accessible to judges.

| Evidence | Scope |
|---|---|
| [Current local control tests](evidence/qa-2026-11-08-summary.json) | 131/131 passed, including SQLite concurrency, process restart, request hardening and offline receipt consistency. Provider/model responses are synthetic. |
| [Hosted renewal review](evidence/hosted-renewal-review.json) | Deployed rehearsal expiry, explicit renewal, lost-response recovery and persistence after browser reload. |
| [Hosted workspace review](evidence/hosted-workspace-review.json) | Desktop navigation, search, retained evidence and cancellation accounting. |
| [Responsive review](evidence/responsive-review.json) · [screenshot](evidence/mobile-approval-qa.png) | Actual component/CSS with synthetic records at phone widths; a tablet spot check. It is not a real-device or payment-integration test. |
| [Hosted recovery review](evidence/hosted-recovery-review.json) | Fresh over-allowance rejection, separately approved alternative and lost-response recovery; repeat lookup did not change accounting. |
| [Readability review](evidence/readability-review.json) · [screenshot](evidence/readability-qa.png) | Updated typography and receipt comparison at 360/390/768/1280 CSS-pixel widths, including keyboard table scrolling. Synthetic visual QA only. |
| [Hosted release check](evidence/hosted-release-review.json) · [screenshot](evidence/hosted-release-qa.png) | Deployed receipt comparison, fresh approval/cancellation, reload persistence and proposal provenance. Rehearsal only. |
| [Current QA report](docs/QA_REPORT.md) | Commands, results, identified gaps and the boundaries of the latest review. |

## Try the rehearsal locally

Use Node.js **22.13.0 or later**; the CI environment is pinned to Node.js 24.22.1. The tests use Node's built-in SQLite module. No PayPal account, model key or paid service is needed for the rehearsal and local tests.

```sh
git clone --branch proofpay/purchase-desk-v0.1 https://github.com/kaulastudies/ai-evaluation-lab.git
cd ai-evaluation-lab/hackathon/proofpay
npm run install:ci
npm run build
```

Initialize a **fresh local database** with the committed migration:

```sh
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_greedy_living_lightning.sql
npm run dev
```

Open the loopback URL printed by the server, normally `http://localhost:5173`. In an ordinary local checkout, `/signin-with-chatgpt?return_to=/` supplies a loopback-only simulated development identity. It is not a real ChatGPT login. Start the **$300 rehearsal**, approve a request, create its simulated order, enable **Drop the capture response**, capture and then check the original outcome.

The managed execution profile intentionally disables simulated sign-in. The [development guide](docs/DEVELOPMENT.md) explains that distinction, migration handling, server environment variables and deployment boundaries. Do not replay the initial migration against an existing database.

## Verify a change

Run these commands from `hackathon/proofpay`:

```sh
node node_modules/typescript/bin/tsc --noEmit
npm run lint
npm test
npm run build
node tests/responsive/build.mjs
```

[ProofPay CI](../../.github/workflows/proofpay.yml) runs these checks on relevant pushes and pull requests after installing from the lockfile. It uses no production credentials and performs no deployment or external payment. A workflow definition is not a passing run; inspect the checks on the exact commit under review.

The [visual fixture](tests/responsive/README.md) is a separate read-only QA harness. It renders the real interface with synthetic records, rejects mutations and blocks external navigation/downloads. Its successful build does not replace browser inspection. Hosted authentication, real model execution and PayPal buyer approval require separate checks.

An exported version 1 receipt can also be checked offline:

```sh
node scripts/verify-receipt.mjs /path/to/receipt.json
```

The [receipt verifier](scripts/verify-receipt.mjs) recomputes the approval digest and compares the exported operation, events and provider record. It makes no network calls. A passing result means the unsigned record is internally consistent; it does not authenticate PayPal, a model, the author or TIP compatibility. Older exports must be re-exported from the updated application. See [receipt verification](docs/DEVELOPMENT.md#offline-receipt-verification).

## Architecture and authority

| Component | Owns |
|---|---|
| React/Vinext purchase desk | Requests, owner interaction, mode labels, record inspection and evidence export. |
| Authenticated API boundary | Trusted ingress identity, same-origin mutation requirements and ownership checks. |
| Application service | Approval binding, atomic reservation, state transitions, durable dispatch and reconciliation. |
| Cloudflare D1 | Workspaces, operations, approval/event history and simulated provider state. |
| Model adapter | A permitted catalogue SKU and rationale; no payment credentials or approval authority. |
| PayPal sandbox adapter | Test order creation, buyer-approval checks, capture and original-order lookup. |

The expected operation, seller, amount, currency and completed capture must match before payment is recorded. Confirmation and its limited verification snapshot are persisted together. Approval digests and stored provider fields aid inspection; they are not signed PayPal attestations, externally anchored TIP receipts or proof against database compromise.

Read the [state machine and trust boundaries](docs/ARCHITECTURE.md). The [development guide](docs/DEVELOPMENT.md#api-surface) maps the API and source files.

## Current limits and next gates

- One controlled sample seller, USD and a small synthetic digital-service catalogue. The $300 figure is a workspace allowance, not a bank balance.
- No production payments, webhooks, refunds, fulfillment, subscriptions or cancellation after provider dispatch.
- A lost create response without a saved provider order ID needs manual investigation. There is no blind create/capture retry or automatic provider fallback.
- Hosted identity depends on a trusted ingress supplying the owner header. Exposing the Worker directly without an equivalent authenticated boundary is unsupported.
- Dependency audit retains 18 findings (0 critical, 1 high, 15 moderate, 2 low); the high finding is Zod in connector infrastructure. See the QA report for paths and reachability limits.
- Real model-to-PayPal execution, independent reviewer access, the required public demo video and final submission readiness remain open gates.
- Security review and passing tests do not establish regulatory compliance, fraud elimination, processor parity or a general exactly-once guarantee.

Development should close those gates before adding providers or broader financial products. The [departmental operating roadmap](docs/OPERATING_ROADMAP.md) and [provenance/TIP roadmap](docs/PROVENANCE_ROADMAP.md) record hypotheses and evidence requirements; it does not promise a company valuation or a hackathon result.

## License and attribution

ProofPay is part of [AI Evaluation Lab](https://github.com/kaulastudies/ai-evaluation-lab), maintained by Rama Chandra Malayanur. This directory includes an [Apache-2.0 license](LICENSE). Dependency versions are in `package.json` and `package-lock.json`; preserved starter/vendor notices cover their respective components. PayPal product names describe the integration and do not imply endorsement.
