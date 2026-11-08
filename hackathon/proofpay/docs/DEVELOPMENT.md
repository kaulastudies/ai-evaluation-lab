# Developing ProofPay

This guide covers the application in `hackathon/proofpay`. Run commands from that directory unless a step says otherwise. The public working branch is `proofpay/purchase-desk-v0.1`; the review is [PR #53](https://github.com/kaulastudies/ai-evaluation-lab/pull/53). Deployment and hackathon submission are separate actions.

## Prerequisites and installation

Use Node.js 22.13.0 or later and npm. The automated workflow pins Node.js 24.22.1. `node:sqlite` supplies the independent database test harness; the application itself uses Cloudflare D1. You do not need provider secrets for the local control tests, Worker build or rehearsal.

```sh
git clone --branch proofpay/purchase-desk-v0.1 https://github.com/kaulastudies/ai-evaluation-lab.git
cd ai-evaluation-lab/hackathon/proofpay
npm run install:ci
```

`install:ci` installs the committed lockfile with development and optional dependencies and checks that the framework executable is present. A clean clone chooses the portable execution profile. Checkout-local managed settings live under the ignored `.sites-runtime/` directory; do not copy them into a portable checkout or CI.

Do not run a dependency installer in a checkout while another process is building or testing it. Keep dependency changes deliberate, commit the lockfile and rerun the relevant checks. Do not commit `node_modules`, generated output, database files, credentials or private execution records.

## Local database and interactive rehearsal

Build once to generate the Worker configuration:

```sh
npm run build
```

For a new local database, apply the initial migration:

```sh
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_greedy_living_lightning.sql
```

The binding is `DB`. The persistence directory is `.wrangler/state`; Wrangler manages its versioned children. Apply additional committed migrations in order when they exist. Do not rerun SQL already applied. The command above changes local state only; it does not initialize or migrate the hosted database.

```sh
npm run dev
```

Use the server's printed loopback URL, normally `http://localhost:5173`. The portable development server has a loopback-only `/signin-with-chatgpt?return_to=/` route that sets a simulated development identity. Its middleware removes client-supplied identity headers before applying that local identity. This is a development convenience, not real authentication for a public deployment.

The managed profile sets `mockAuth: false`; a 404 on its local sign-in route is an expected profile limitation. Use an ordinary portable checkout or the authenticated hosted application. Do not bypass the production identity checks to make a preview accessible.

In **Connections**, start the **$300 rehearsal**. Approve a sample request, create its simulated order, capture it and inspect its activity. To exercise uncertainty, select **Drop the capture response** before capture. The reservation should stay held until **Check simulated outcome** verifies the existing order. These operations simulate money and provider behavior.

`npm start` runs the built Worker locally and uses the same persistence path. It has no portable development sign-in middleware. It is useful behind a trusted identity proxy for Worker verification, but it is not the recommended interactive entry point and does not deploy anything.

## Server configuration

`.env.example` documents variable names with empty values. Rehearsal needs none of them. For real sandbox integration, use server-side environment settings in the hosted deployment. In portable Vite development, an uncommitted `.dev.vars` file supplies Worker variables. Restart after changing it. See [Cloudflare's Vite secrets reference](https://developers.cloudflare.com/workers/vite-plugin/reference/secrets/).

| Variable | Required for | Meaning |
|---|---|---|
| `PAYPAL_CLIENT_ID` | PayPal sandbox | Sandbox application's client identifier. |
| `PAYPAL_CLIENT_SECRET` | PayPal sandbox | Server-side application secret. |
| `PAYPAL_MERCHANT_ID` | PayPal sandbox | Expected test payee, checked against provider evidence. |
| `AI_API_KEY` | Model proposals | Server-side inference credential. |
| `AI_BASE_URL` | Model proposals | Approved HTTPS OpenAI-compatible API base, including a version path when needed. The adapter appends `/chat/completions`. |
| `AI_MODEL` | Model proposals | Explicit supported model identifier. |

Keep values out of source, frontend bundles, screenshots, issue descriptions, logs and exported evidence. A local `.env.local` file is not proof that a hosted Worker received a secret. Inspect **Connections** for presence, then execute and verify the actual service call. Presence is not a credential test.

The AI adapter requests JSON containing `sku` and `rationale`; the chosen endpoint/model must support that response format. The server owns catalogue prices, merchant, currency and approval policy. Rehearsal selection remains explicitly deterministic and is never relabelled as a successful model call.

The PayPal adapter is fixed to the sandbox API. Use a separate sandbox buyer for native PayPal approval. An API secret does not replace buyer consent. A return URL does not prove payment. Verify the original order/capture and inspect the recorded receipt before describing an end-to-end sandbox result.

## Checks and evidence

```sh
node node_modules/typescript/bin/tsc --noEmit
npm run lint
npm test
npm run build
node tests/responsive/build.mjs
```

| Check | Exercises | Does not establish |
|---|---|---|
| TypeScript and lint | Source types and configured static rules. | Runtime correctness or complete security. |
| `npm test` | Auth/model/provider contracts and application/database regressions using controlled inputs. | A real model response or PayPal payment. |
| SQLite race/restart cases | Actual process contention, transactions and persisted simulated state. | Parity with every hosted D1 behavior or a full service outage exercise. |
| Worker build | Client, RSC/SSR and Worker compilation/packaging. | Successful deployment, authentication or live API configuration. |
| Responsive fixture build | The actual component/CSS bundled with labelled synthetic data. | Browser inspection, touch-device behavior or backend integration. |
| Hosted rehearsal | Observed UI/API/database behavior in the deployed app with a simulated provider. | A genuine PayPal payment or an actual model call. |

Review the command's output for the exact checkout. Use [QA_REPORT.md](QA_REPORT.md) and the committed `evidence/` files for recorded results; do not replace current results with an older passing count. The database harness models the D1 prepared-statement and batch surface with real SQLite. Its stated scope is intentionally narrower than full D1 emulation.

For layout changes, use [tests/responsive](../tests/responsive/README.md) and inspect affected views at narrow widths. It intercepts fetch calls, rejects mutations, and blocks external navigation/downloads. Its output directory is ignored by Git and lint; its source remains linted. Preserve the clear synthetic-data label in screenshots.

### Offline receipt verification

Export a purchase's evidence from the updated application, then run:

```sh
node scripts/verify-receipt.mjs /path/to/receipt.json
```

The command accepts one regular JSON file, up to 1 MiB, with `receiptSchemaVersion: 1`. It recomputes the `proofpay-approval-v1` SHA-256 digest, compares its exact ordered inputs with the exported operation, and checks the consistency of status, provider fields and confirmation events. It prints a JSON result on success and exits with code 1 on invalid input. No credentials or network access are needed. Re-export older receipts; they lack the versioned binding fields this verifier needs.

This is an unsigned application-record check. Someone who can replace the data can also recompute its digest. The digest does not cover request text, rationale, labels, request IDs or event prose. A passing result does not establish provider authenticity, model execution, current permission to spend, external signatures or TIP compatibility. Treat the declared mode and recorded status as claims within the inspected record.

## CI behavior

[`.github/workflows/proofpay.yml`](../../../.github/workflows/proofpay.yml) runs on ProofPay-related pull requests, matching branch pushes and manual dispatch. It installs the lockfile, checks types/lint/tests, builds the Worker and builds the visual fixture.

The workflow grants `contents: read`, does not persist checkout credentials, pins its actions to full commit SHAs, and has a timeout and concurrency cancellation. It receives no PayPal, inference or deployment secrets. It does not publish a Site, merge a PR, accept terms or submit Devpost. Check the actual workflow result after pushing; adding the YAML does not prove that GitHub accepted or ran it.

The action pins were verified against the official `actions/checkout` v6.1.0 and `actions/setup-node` v6.5.0 tag refs on 8 November 2026. Review an upstream change before updating a pin. GitHub documents [workflow syntax and permission scopes](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

## Source map

| Path | Responsibility |
|---|---|
| `components/proofpay/purchase-desk.tsx`, `app/globals.css` | Owner interface, accessible dialogs, navigation and responsive styling. |
| `app/api/` | Route handlers; keep authorization and request validation at the boundary. |
| `lib/proofpay/auth.ts` | Trusted identity and mutation-origin requirements. |
| `lib/proofpay/service.ts` | Approval, reservations, dispatch claims, cancellation and reconciliation. |
| `lib/proofpay/ai.ts` | Structured catalogue selection and limited model provenance. |
| `lib/proofpay/provider.ts` | PayPal sandbox calls and the durable rehearsal provider. |
| `db/schema.ts`, `drizzle/` | Persistent schema and reviewed migrations. |
| `worker/index.ts`, `vite.config.ts`, `scripts/` | Worker/framework/runtime integration. |
| `scripts/verify-receipt.mjs` | Offline version 1 receipt consistency checks; no external authentication. |
| `tests/`, `evidence/` | Reproducible checks and explicitly scoped recorded observations. |

### API surface

Routes require the authenticated owner's identity. Mutation routes also enforce the request boundary; possessing an operation ID grants no access to it.

| Method | Path | Action |
|---|---|---|
| GET | `/api/state` | Active workspace, operations and recent events. |
| POST | `/api/rehearsal/start` | Start an isolated simulated workspace. |
| POST | `/api/workspaces` | Start a workspace in an explicit supported mode. |
| POST | `/api/proposals` | Select and validate a catalogue proposal. |
| POST | `/api/operations/:id/approve` | Approve the exact purchase and reserve allowance. |
| POST | `/api/operations/:id/cancel` | Cancel before provider dispatch, with state/version checks. |
| POST | `/api/operations/:id/renew-approval` | Reapprove an eligible expired purchase while retaining its reservation and IDs. |
| POST | `/api/operations/:id/create-order` | Claim a durable create attempt and store its checked order. |
| POST | `/api/operations/:id/capture` | Claim capture after the approval and buyer checks. |
| POST | `/api/operations/:id/reconcile` | Read and compare the original order's outcome. |
| GET | `/api/operations/:id/evidence` | Export the operation's application evidence receipt. |

## Change and release discipline

Keep a change small enough that its state transitions and failure behavior can be reviewed. Add regression tests for a real failure or risk; preserve expected forbidden effects such as zero extra capture calls or no cross-owner disclosure. A UI improvement must retain exact operation/version targeting and accurate rehearsal/sandbox labels.

For schema work, edit `db/schema.ts`, run `npm run db:generate`, and review the SQL. Test against a fresh local database and a representative prior schema before applying a hosted migration. Never generate or modify a migration merely to make an existing database appear clean.

The official deployment has an existing Site identifier in `.openai/hosting.json`. Maintainers must preserve that identity and its access policy when publishing updates. A fork must provision its own deployment identity, storage and trusted authentication boundary; the checked-in identifier grants no deployment rights. Secrets belong in the selected deployment's server environment, not the hosting manifest.

Before a release, record the source commit, checks, dependency findings, migration outcome and deployment result. Then inspect the actual hosted workflow. Preserve unresolved outcomes and their reservations; never clear them or issue a new provider request merely to produce a clean demo. The [judge readiness review](JUDGE_READINESS.md) covers the separate event-specific gates.

## Troubleshooting

| Symptom | First check |
|---|---|
| `node:sqlite` is unavailable | Check `node --version`; use at least 22.13.0, preferably the CI version. |
| Framework executable missing after install | Run `npm run install:ci` to completion in the intended app directory. Do not edit the lockfile to suppress an install failure. |
| `no such table` | Confirm the committed migration was applied to `.wrangler/state` using the generated Worker config. |
| Local sign-in returns 404 | Check whether the checkout uses the managed profile. Simulated sign-in is intentionally unavailable there. |
| Sandbox start is disabled | Inspect Connections and the server variable names. Presence still requires a real credential and execution check. |
| Purchase remains uncertain | Inspect its original order and retained evidence. Do not create a replacement purchase or blindly retry capture. |
| A screenshot looks correct but CI fails | Follow the exact failing type/test/build output; a screenshot validates only the observed interface. |
