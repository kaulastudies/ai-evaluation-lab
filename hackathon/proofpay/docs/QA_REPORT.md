# ProofPay QA report

Reviewed 8 November 2026, starting from commit `47dcf677` and including the source changes fingerprinted in the [machine-readable result](../evidence/qa-2026-11-08-summary.json). The combined local suite passed **131 of 131 checks**, with no failures, cancellations or skipped checks. Dependency updates reduced the audit from 34 affected package entries to 18; one high-severity dependency finding remains.

This report covers source review, local SQLite execution, synthetic upstream responses and offline receipt consistency. It does not establish genuine model inference, a buyer-approved PayPal sandbox capture, production readiness or the behavior of the hosting authentication boundary.

## Results and reproduction

Commands run from `hackathon/proofpay`, using Node `v24.22.1`:

```bash
npm test
node node_modules/eslint/bin/eslint.js tests/review-worker.mjs tests/review-service.mjs tests/review-database.mjs
npm audit --json
```

| Check | Result at this checkpoint |
| --- | --- |
| Combined independent suite | 131 passed; 0 failed, cancelled or skipped |
| Lint of changed independent database/service/worker tests | Passed |
| Dependency installation using the managed installer | Passed; 694 packages installed by the final clean install |
| Final npm audit | Completed; exit 1 because 18 affected package entries remain |
| Full application typecheck and lint after frontend changes | Release owner reports `npx tsc --noEmit` and `npm run lint` passed, exit 0 |
| Responsive fixture build | Release owner reports passed, using the three current component/style source files |
| Production Worker build | Passed on the upgraded dependency set; private deployment and hosted checks are recorded separately |
| Hosted browser and mobile checks | Separate evidence, described below; not part of the 131 local checks |

The combined command explicitly names the seven suites, excluding worker/helper files from test discovery:

```bash
node --test tests/review-provider.mjs tests/review-service.mjs tests/review-auth.mjs tests/review-ai.mjs tests/review-security.mjs tests/review-database.mjs tests/review-receipt.mjs
```

| Suite | Checks | Evidence provided |
| --- | ---: | --- |
| Provider | 23 | Strict identity, amount, seller, currency, order/capture status and final-capture matching; sandbox transport and no hidden retry |
| Service | 55 | Shared allowance, approval binding/expiry, renewal, cancellation, dispatch uncertainty, restart, reconciliation and evidence privacy |
| Authentication | 7 | Trusted-identity requirement and same-origin JSON mutation rules |
| Model | 7 | Catalogue restrictions, rejected malformed/failed output, no fallback and bounded provenance |
| Security | 9 | Streamed input bounds, action validation, API headers, credentialed redirect rejection and bounded upstream responses |
| Database | 7 | Transaction rollback, tenant isolation, evidence completeness and simultaneous cancellation in separate OS processes |
| Receipt | 23 | Actual local service exports plus adversarial binding/provider mutations checked by an independent offline verifier |

The [test output](../evidence/qa-2026-11-08-test-output.log) is Node's human-readable test reporter, not TAP. The [summary](../evidence/qa-2026-11-08-summary.json) records exact source and evidence SHA-256 hashes. These hashes identify this test checkpoint; they are not signatures or independent attestations. The evidence files contain no captured credentials, headers, cookies or raw provider/model responses. A sensitive-pattern scan of the retained test/audit artifacts found no matching key, private-key, Authorization-value or email patterns; this is an additional check, not a comprehensive secret-scanning guarantee.

## Database findings and independent regressions

Review found that proposal creation and its provenance event, and approval and its audit event, previously used separate writes. A failed audit insert could leave an operation without provenance or an unaudited reservation. Retrying the request did not repair the missing record. Both pairs now use transactional D1 batches.

The new database suite uses SQLite triggers to deliberately abort the provenance insert, approval event insert and approval state write. Each test checks the raw database after failure, confirms that the entire transaction rolled back, and verifies a successful retry where applicable. These checks would fail against the previous separate-write behavior.

The other new checks establish that:

- Two owners can use the same request key without sharing operations, allowance or evidence. Seven operation methods reject a foreign owner's ID without provider effects.
- The workspace's 100-event display cap does not truncate the complete operation evidence export.
- A session pointer incorrectly referencing another owner's workspace cannot expose that workspace or its evidence.
- Two separate OS processes cancelling one approved purchase return safely with one cancellation event and one reservation release.

Existing tests retain actual separate-process reservation contention and a child-process restart, as well as staged cancellation/approval/renewal/dispatch races. The approval test barrier was moved to the batch boundary after the transactional fix, so it still pauses before the competing transaction rather than after a write. Database checks include `PRAGMA integrity_check` and `PRAGMA foreign_key_check`.

The adapter uses real SQLite with `BEGIN IMMEDIATE` transactions and foreign keys enabled. It models the D1 prepared-statement/batch surface; it is not an emulator proving hosted D1 scheduling, replication or recovery behavior. The schema does not enforce every state/money invariant with CHECK constraints, and the event operation ID lacks a foreign-key constraint. Correct application writes remain part of the trust model; arbitrary privileged database corruption is not covered.

## Dependency changes

The audit counts package entries, including parent packages affected through a dependency. It does not count independent exploitable vulnerabilities.

| Audit snapshot | Critical | High | Moderate | Low | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Before | 1 | 15 | 17 | 1 | 34 |
| After | 0 | 1 | 15 | 2 | 18 |

Raw, dated inputs are retained in [before.json](../evidence/npm-audit-2026-11-08-before.json) and [after.json](../evidence/npm-audit-2026-11-08-after.json).

Applied compatible version updates:

| Dependency | Final version |
| --- | --- |
| `next`, `eslint-config-next` | 16.4.5 |
| `react`, `react-dom`, `react-server-dom-webpack` | 19.2.8 |
| `vite` | 8.3.6 |
| Direct `esbuild` used by local tests | 0.28.1 |
| Miniflare-scoped `sharp`, `undici`, `ws` overrides | 0.35.5, 7.30.1, 8.22.0 |
| Cloudflare Vite plugin-scoped `ws` override | 8.22.0 |
| Vinext-scoped `image-size` override | 2.0.3 |

Compatible lockfile updates also refreshed `brace-expansion`, `browserslist`, `js-yaml`, `@babel/core`, `baseline-browser-mapping`, `fast-uri` and `fflate`. Vinext `1.0.0-beta.5`, Cloudflare Vite plugin `1.37.1` and Wrangler `4.92.0` were retained. Vinext's React peer ranges accept the patched 19.2.8 trio. A larger framework/runtime migration was not treated as an automatic audit fix.

The lockfile was resolved with `npm install --package-lock-only --ignore-scripts --no-audit`, followed by the named transitive update using `npm update --package-lock-only --ignore-scripts --no-audit`. Actual installation used the approved managed installer, which invokes `npm run install:ci` and `npm ci`. No `npm audit fix --force` or blind major upgrade was run. A fresh checkout can reproduce installation with `npm run install:ci` as documented in [DEVELOPMENT.md](DEVELOPMENT.md).

Patched advisory families include [Next.js Node image response RCE](https://github.com/advisories/GHSA-vcvr-r3jv-pc5j), [Next.js image optimizer](https://github.com/advisories/GHSA-2464-fhr4-w9xw), [Next.js use-cache typed arrays](https://github.com/advisories/GHSA-673q-mjm6-r5xr) and [React Server Components denial of service](https://github.com/advisories/GHSA-wx67-qw84-cm4g). The update removes the affected versions from the audit paths addressed here. It does not establish that each pre-update exploit was reachable in this application.

## Remaining dependency findings

Exact audited package locations follow. These are unresolved findings, even where source inspection suggests a limited exposure.

| Package entry | Severity | Installed location |
| --- | --- | --- |
| `zod` | High | `node_modules/zod` |
| `satori` | Moderate | `node_modules/satori` |
| `@vercel/og` | Moderate | `node_modules/@vercel/og` |
| `vinext` | Moderate | `node_modules/vinext` |
| `minimatch` | Moderate | `node_modules/@typescript-eslint/typescript-estree/node_modules/minimatch` |
| `@typescript-eslint/typescript-estree` | Moderate | `node_modules/@typescript-eslint/typescript-estree` |
| `@typescript-eslint/parser` | Moderate | `node_modules/@typescript-eslint/parser` |
| `@typescript-eslint/type-utils` | Moderate | `node_modules/@typescript-eslint/type-utils` |
| `@typescript-eslint/utils` | Moderate | `node_modules/@typescript-eslint/utils` |
| `@typescript-eslint/eslint-plugin` | Moderate | `node_modules/@typescript-eslint/eslint-plugin` |
| `typescript-eslint` | Moderate | `node_modules/typescript-eslint` |
| `eslint-config-next` | Moderate | `node_modules/eslint-config-next` |
| `esbuild` | Moderate aggregate | `node_modules/@esbuild-kit/core-utils/node_modules/esbuild`; `node_modules/wrangler/node_modules/esbuild` |
| `@esbuild-kit/core-utils` | Moderate | `node_modules/@esbuild-kit/core-utils` |
| `@esbuild-kit/esm-loader` | Moderate | `node_modules/@esbuild-kit/esm-loader` |
| `drizzle-kit` | Moderate | `node_modules/drizzle-kit` |
| `wrangler` | Low | `node_modules/wrangler` |
| `@cloudflare/vite-plugin` | Low | `node_modules/@cloudflare/vite-plugin` |

The underlying causes and assessed exposure are:

- **Zod 3.25.76:** [oversized collection validation can exhaust memory](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5); the advisory fixes it in 4.6.6. Zod is used by starter connector infrastructure: `scripts/connector-preview/protocol.mjs`, `scripts/connector-preview/host-binding.mjs` and `lib/connector-errors.mts`, including unconstrained arrays/JSON. The purchase API uses its own validators and no active product connector route was found, but Zod is not globally unused or proven unreachable. Remediation requires a deliberate major-version migration and validation of the v3 `z.record(...)` caller and embedded v4 imports. Do not enable untrusted connector payloads on the assumption this finding is closed.
- **Satori 0.16.0 via `@vercel/og` 0.8.6 and Vinext:** [SVG escaping advisory](https://github.com/advisories/GHSA-wx4j-mvgx-mqwp), fixed in 0.33.5. No product `next/og`, `ImageResponse` or attacker-controlled SVG rendering route was found. The pinned parent dependency still carries the finding; a compatible framework/rendering update needs separate verification.
- **Minimatch 10.2.5 in TypeScript ESLint tooling:** [glob amplification denial of service](https://github.com/advisories/GHSA-g3hv-75wg-m249), fixed in 11.0.1. Its observed role is repository lint/type analysis, not purchase-input processing. Forcing the major dependency version underneath the current parser was not attempted.
- **Nested esbuild:** `@esbuild-kit/core-utils` carries 0.18.20, affected by the [development-server CORS advisory](https://github.com/advisories/GHSA-67mh-4wv8-2f99). Wrangler carries 0.27.3, affected by the [Windows development-server file-read advisory](https://github.com/advisories/GHSA-g7r4-m6w7-qqqr). No affected esbuild development server was started during this review; the environment is Linux. These nested copies remain despite the fixed direct esbuild. Follow the respective tooling upgrades rather than declaring the aggregate finding removed.

These reachability assessments are source-based inferences, not exploit tests or proofs of non-reachability. The remaining high finding prevents a clean dependency-audit claim. Full public/production security clearance is not provided.

## Hosted, visual and external-service boundaries

The release owner separately recorded an authenticated hosted **rehearsal** run in [hosted-recovery-review.json](../evidence/hosted-recovery-review.json). It observed budget rejection, a lower-cost proposal requiring approval, reserved funds, simulated capture-response loss persisting across reload, reconciliation to the same capture and unchanged totals on a repeated check. That checkpoint predates this security patch and does not count as testing the newly deployed build. The export UI showed success, but downloaded bytes were not verified.

The responsive harness in [tests/responsive](../tests/responsive/README.md) renders the production component/CSS with synthetic data and mock fetch. The release owner visually checked receipt views at 360 and 390 pixels, Approvals/Controls at 360, Overview/Purchases at 768 and Evidence at 1280. No document overflow was observed; keyboard Tab plus held Right Arrow scrolled the table, and Escape closed the receipt. A positioned table wrapper corrected page overflow caused by an absolutely positioned screen-reader label; intentional table scrolling remains. The harness blocks external PayPal navigation and mock mutations. It provides layout evidence, not hosted authentication or provider integration evidence.

The 131 checks do not make any model/PayPal network calls. A mocked sandbox adapter test proves request construction and failure behavior under its fixtures. Earlier real OAuth/order-create/GET observations do not substitute for a genuine model proposal followed by owner approval, sandbox buyer approval, capture and independent GET verification. That complete external chain remains a release-evidence gap.

Before describing this as a verified end-to-end sandbox integration, retain redacted evidence for that chain, including matching operation/order/capture IDs, amount, currency, merchant, final-capture status and the independently fetched provider record. Verify response-loss recovery separately without issuing a second capture. Before public deployment, also establish that the ingress strips caller-supplied identity headers and restricts access as intended; local header tests cannot prove that hosting property.

For other security boundaries and implemented controls, see [SECURITY_REVIEW.md](SECURITY_REVIEW.md). No new release-blocking application defect was observed by the passing local suites. The remaining dependency finding, missing genuine external flow and pending production build/hosting checks must remain explicit in readiness claims.
