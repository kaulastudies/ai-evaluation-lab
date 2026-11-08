# ProofPay Purchase Desk

An AI Evaluation Lab project for purchasing requests, shared spending limits and payment-outcome verification.

A small studio has a $300 allowance for outside review work. Two assistants propose purchases of $180 and $160. ProofPay keeps the spending decision with the owner, reserves the permitted amount, and records what the payment provider actually confirms. When a payment response is lost, the operation stays unresolved until its original outcome can be checked.

The project is a hackathon prototype. The intended integration is PayPal sandbox, not production payments.

## Current verification status

The application code includes the owner interface, persistent ledger, rehearsal provider, PayPal sandbox adapter and model adapter. Genuine PayPal sandbox OAuth and create/GET calls have been verified through the provider adapter. The order remained awaiting buyer action; a genuine model invocation and buyer-approved capture are not yet verified. A rehearsal can demonstrate application behaviour with a simulated provider; it does not establish a PayPal payment or an AI integration.

The hosted Site is private to its owner and is not ready for independent judge access. The managed local preview does not provide mock sign-in. Hosted UI behaviour must be checked separately; code and local test results are not hosted UI evidence.

Read [the judge guide](docs/JUDGES.md), [architecture and limits](docs/ARCHITECTURE.md), and [recording script](docs/DEMO_SCRIPT.md). Verification results should identify the tested source version and distinguish local tests from external integrations.

## Product scope

- One controlled demonstration merchant and a small sample catalogue.
- One USD allowance shared by the purchasing requests in a workspace.
- Structured proposals validated against server-owned catalogue items and prices.
- Owner approval before payment execution.
- Durable operation records, reservations and outcome evidence.
- Read-only verification of an uncertain capture against its original provider order.

The model does not receive payment secrets, increase the budget, approve its own purchase or establish payment success. A timeout does not establish that payment failed. Reserved funds remain reserved while the outcome is unknown.

The sample seller offers Workflow review ($180), Design review ($160) and Starter review ($90). These digital packages and prices are synthetic; no paid service is delivered by the demonstration.

## Run locally

Use Node.js 22.13.0 or later. The checkout includes its lockfile and the Vinext/React application, Cloudflare Worker runtime and D1 database configuration.

```sh
npm ci
npm run build
```

The build generates `dist/server/wrangler.json`. Apply the committed SQL migrations to a fresh local database before starting. Migration commands are described below. For interactive use in a portable local checkout, run:

```sh
npm run dev
```

Open the loopback URL printed by the server, normally `http://localhost:5173`. The portable development server provides a loopback-only simulated sign-in through `/signin-with-chatgpt?return_to=/`. It is a local development identity, not a real ChatGPT login. Use **Start $300 rehearsal** to populate the two sample requests; no external credentials are needed for rehearsal.

The managed execution profile disables that simulated sign-in; its local sign-in route may return 404. Use the portable local workflow above or the authenticated hosted Site. Do not weaken the backend's identity check to make a managed preview work.

`npm start` runs the built Worker directly and retains D1 state under `.wrangler/state`. It does not provide the development sign-in route or deploy the application. Use it for Worker verification behind a trusted identity proxy, not as the interactive local setup. Hosted requests rely on Sites ingress supplying `oai-authenticated-user-id`; never expose a deployment that accepts an arbitrary client identity header.

### Local database

The D1 binding is named `DB`. The hosting declaration is `.openai/hosting.json`; the schema is under `db/`, and SQL migrations are under `drizzle/`.

For a fresh database, apply the initial committed migration:

```sh
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_greedy_living_lightning.sql
```

Apply any later committed migrations in filename order. Do not replay migrations already applied. Use `.wrangler/state`, not `.wrangler/state/v3`; Wrangler manages its versioned subdirectories. Local migrations affect only the local preview database. Hosted migration application is a separate deployment step.

`npm run db:generate` is for developers changing the schema. Review and commit its SQL output; judges and ordinary users should apply the existing migrations rather than generate new ones.

## External integration configuration

The adapters read these names from the Cloudflare Worker environment. Never put their secret values into browser code, committed files, screenshots, video, public judge instructions or exported receipts.

| Variable | Purpose |
|---|---|
| `PAYPAL_CLIENT_ID` | Sandbox application identifier. |
| `PAYPAL_CLIENT_SECRET` | Sandbox application secret, server-side only. |
| `PAYPAL_MERCHANT_ID` | Expected sandbox merchant/payee identity used for validation. |
| `AI_API_KEY` | API credential for the selected inference service, server-side only. |
| `AI_BASE_URL` | HTTPS base URL for an OpenAI-compatible chat-completions API. The adapter appends `/chat/completions`; include any required version path in the base. |
| `AI_MODEL` | Exact model identifier used to generate proposals. |

Credential configuration is not proof of a successful integration. Record a real model response and an actual PayPal sandbox order/capture before claiming those paths work. The PayPal buyer's native approval remains part of the purchase flow. API credentials do not replace buyer approval.

The AI adapter requests JSON-object output containing a catalogue `sku` and `rationale`. Proposal events retain allowlisted provider response ID and returned model when supplied, requested model, provider origin and receipt time; credentials and raw provider payloads are omitted. These fields identify a run but are not a signed provider attestation. The selected endpoint/model must support that format. Rehearsal uses deterministic selection rules and explicitly records that no model was called; it is not a fallback that may be relabelled as real AI.

For hosted operation, configure the values through the deployment's server-side environment settings. For local Vite development, use an uncommitted `.dev.vars` file in the project root, following [Cloudflare's local secrets documentation](https://developers.cloudflare.com/workers/vite-plugin/reference/secrets/). Restart the development server after changes and inspect **Connections** for configuration status. Configuration status checks presence; it does not test credentials or prove a model/payment call succeeds. The PayPal adapter is fixed to `api-m.sandbox.paypal.com`.

The UI enables **Start PayPal sandbox workspace** when both integrations are configured. Use a separate sandbox buyer to complete **Open PayPal approval**, then capture and check that same order. No production-payment mode is included.

## Implemented API

All routes require the trusted owner identity. Mutations also require same-origin JSON requests. Operation routes check ownership; an operation ID is not authorization.

| Method and path | Action |
|---|---|
| `GET /api/state` | Read the owner's active workspace, operations and events. |
| `POST /api/rehearsal/start` | Create an isolated rehearsal with the two sample proposals. |
| `POST /api/workspaces` | Create a workspace in an explicit mode. |
| `POST /api/proposals` | Validate a model-selected or rehearsal-selected catalogue proposal. |
| `POST /api/operations/:id/approve` | Bind owner approval and reserve available allowance atomically. |
| `POST /api/operations/:id/renew-approval` | Explicitly reapprove an expired pre-capture purchase without adding a reservation or replacing its order. |
| `POST /api/operations/:id/create-order` | Claim one durable create attempt and store its checked order. |
| `POST /api/operations/:id/capture` | Claim one capture attempt after buyer approval; supports the labelled response-drop fault. |
| `POST /api/operations/:id/reconcile` | Read and compare the saved order's outcome. |
| `GET /api/operations/:id/evidence` | Export that operation's server-side evidence receipt. |

## Verification and evidence

The useful checks examine both the allowed result and forbidden effects:

- Distinct concurrent proposals cannot oversubscribe the shared allowance.
- A changed amount, merchant or currency cannot reuse old approval.
- Uncertain capture retains its reservation and original operation identity.
- Recovery compares the expected order, payee, amount, currency and completion state.
- Repeated actions and reconciliation cannot add a second accounting effect in the tested cases.
- Restart tests exercise durable state; a browser refresh alone is not backend-restart evidence.
- Catalogue text and model output cannot change financial policy.

Keep results labelled by layer: unit test, mocked integration, application rehearsal, real model call or actual PayPal sandbox run. Passing a rehearsal is not a sandbox-payment result. Do not claim a general safety percentage, production readiness, fraud elimination or guaranteed exactly-once execution.

## Development and deployment

```sh
npm run lint
npm test
npm run build
```

The test command runs `tests/review-auth.mjs`, `tests/review-ai.mjs`, `tests/review-provider.mjs` and `tests/review-service.mjs`. These use controlled inputs and provider responses. They do not make a real model call or PayPal sandbox payment. Inspect the output for the result of your checkout; do not infer a pass from the presence of test files.

The app uses Vinext/React, a Cloudflare Worker and D1. `.openai/hosting.json` binds this checkout to its existing Site. Preserve that identity when deploying and apply the committed migrations through the deployment workflow. Keep secrets and `.wrangler/`, `.vinext/` and `.sites-runtime/` out of source control.

The project uses third-party dependencies listed in `package.json` and the lockfile. Starter runtime integrations and their notices remain in the checkout. Refer to the repository's license and third-party notices for use and redistribution terms.

## Known limits

The $300 limit applies to one isolated demonstration workspace, not a bank account or an account-wide allowance. Starting a new rehearsal preserves prior records but creates a separate allowance. A sandbox workspace with reserved or uncertain operations cannot be hidden by switching workspaces.

Approval expires after 15 minutes and prevents a new dispatch; expiry does not release reserved money. The owner can explicitly renew an expired `APPROVED` or `ORDER_READY` purchase. Renewal preserves the reservation, purchase and provider IDs, increments approval version and rejects stale dispatch authority. It does not extend PayPal order validity. There is no revocation or reservation-release API. Create and capture each have one durable dispatch attempt. After uncertainty, the app checks the original order without automatically retrying payment. If a create response is lost before its order ID is saved, this prototype requires manual investigation and retains the reservation.

There is no webhook receiver, refund execution, fulfillment, subscription or production-payment flow. The evidence receipt contains request IDs, approval digest and `verificationRecords` with the provider fields used for confirmation, labelled by source and mode. That snapshot is stored transactionally with confirmation; it is not signed or externally anchored. See [architecture and limits](docs/ARCHITECTURE.md) for the trust boundary and state transitions.

## Project links

- [AI Evaluation Lab](https://github.com/kaulastudies/ai-evaluation-lab)
- [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/)
- [Official rules](https://paypalaihackathon.devpost.com/rules)
- [PayPal idempotency documentation](https://developer.paypal.com/api/rest/reference/idempotency/)

The submitted story and demonstration must match the actual delivered build. Final registration, submission and judging are separate from implementation or deployment.
