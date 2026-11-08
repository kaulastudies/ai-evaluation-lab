# ProofPay QA report

Updated 8 November 2026 for the manual PayPal sandbox diagnostic and Zod 4.6.7 migration. The release owner reports **151 of 151 local checks passed**, with no failures or skipped checks, plus successful typecheck, full lint, Worker build and responsive fixture build. The [current release record](../evidence/diagnostic-release-review.json) identifies that checkpoint. The audit reports 17 affected package entries: 0 critical, 0 high, 15 moderate and 2 low.

The [earlier 131-check record](../evidence/qa-2026-11-08-summary.json), starting from `47dcf677`, and its audit results remain historical evidence. They predate the diagnostic and Zod migration; they are not reruns of the current source.

This report distinguishes source review, local SQLite execution, synthetic upstream responses and offline receipt checks from the separately observed deployed PayPal-only diagnostic. That diagnostic passed native sandbox buyer approval, capture and recovery with virtual funds. Genuine model inference, the standard AI-to-PayPal journey, production readiness and independent verification of the hosting authentication boundary remain unestablished.

## Results and reproduction

Commands run from `hackathon/proofpay`, using Node `v24.22.1`:

```bash
npx tsc --noEmit
npm run lint
npm test
npm run build
node tests/responsive/build.mjs
```

| Check | Latest recorded result and scope |
| --- | --- |
| Combined independent suite | 151 passed; 0 failed or skipped, reported by the release owner |
| Full application typecheck and lint | `npx tsc --noEmit` and `npm run lint` passed |
| Production Worker build | `npm run build` passed |
| Responsive fixture build | `node tests/responsive/build.mjs` passed; this is not a browser check |
| Zod migration suite | 10 passed; three oversized-input regressions failed as expected on the prior installed version |
| Dependency installation for Zod migration | Passed; 694 packages installed, with Zod 4.6.7 deduped across consumers |
| Latest npm audit | Completed; exit 1 because 17 affected package entries remain |
| Deployed PayPal-only diagnostic | Passed on Site source `17cbededf`: native buyer approval, capture, response-loss recovery and stable accounting after repeated lookup/reload; manual/no-AI |
| Other hosted and mobile checks | Historical evidence below; not part of the 151 local checks |

The current `npm test` command explicitly names nine suites, excluding worker/helper files from test discovery:

```bash
node --test tests/review-provider.mjs tests/review-service.mjs tests/review-auth.mjs tests/review-ai.mjs tests/review-security.mjs tests/review-database.mjs tests/review-receipt.mjs tests/review-connectors.mjs tests/review-diagnostic.mjs
```

| Suite | Checks | Evidence provided |
| --- | ---: | --- |
| Provider | 23 | Strict identity, amount, seller, currency, order/capture status and final-capture matching; sandbox transport and no hidden retry |
| Service | 55 | Shared allowance, approval binding/expiry, renewal, cancellation, dispatch uncertainty, restart, reconciliation and evidence privacy |
| Authentication | 7 | Trusted-identity requirement and same-origin JSON mutation rules |
| Model | 7 | Catalogue restrictions, rejected malformed/failed output, no fallback and bounded provenance |
| Security | 9 | Streamed input bounds, action validation, API headers, credentialed redirect rejection and bounded upstream responses |
| Database | 7 | Transaction rollback, tenant isolation, evidence completeness and simultaneous cancellation in separate OS processes |
| Receipt | 27 | Actual local exports, adversarial binding/provider mutations and explicit manual/no-AI diagnostic classification |
| Connectors | 10 | Zod 4 record compatibility, authority/envelope checks, array caps and rejection before oversized collections are traversed |
| Diagnostic | 6 | Fixed selection without model/provider calls at creation, configuration/authentication boundaries, rollback, shared payment controls and an empty-body HTTP contract |

The historical [131-check test output](../evidence/qa-2026-11-08-test-output.log) is Node's human-readable test reporter, not TAP. Its [summary](../evidence/qa-2026-11-08-summary.json) records that earlier source and evidence SHA-256 hashes. Use the [current release record](../evidence/diagnostic-release-review.json) for the later combined run and the [Zod migration record](../evidence/zod-migration-2026-11-08-summary.json) for its targeted before/after tests. Hashes identify a checkpoint; they are not signatures or independent attestations. The earlier QA review retained no captured credentials, headers, cookies or raw provider/model responses. Its sensitive-pattern scan found no matching key, private-key, Authorization-value or email patterns in those retained test/audit artifacts; that historical check is not a comprehensive secret-scanning guarantee or a scan of subsequent artifacts.

## Manual sandbox diagnostic coverage

`POST /api/sandbox/diagnostic/start` accepts only `{}` and creates one unapproved, fixed $180 USD `workflow-review` request. It uses sandbox mode with a `sandbox-diagnostic` profile. Its creation makes no model or provider call, and its persisted provenance says `manual: true`, `aiCalled: false`. Standard AI proposals still require a model; diagnostic workspaces reject additional proposals even when model credentials exist.

The six diagnostic checks exercise missing authentication/configuration, cross-origin or nonempty HTTP input, provenance-insert rollback and use of the existing financial controls. With a synthetic provider, owner approval precedes order creation; buyer approval is checked before capture; response loss retains $180; an active hold prevents workspace switching; recovery looks up the original order without another create or capture. These are local SQLite/transport fixtures, not a live PayPal result.

The receipt suite now has 27 checks. It accepts actual local diagnostic exports and rejects changed manual/no-AI metadata, missing provenance, a different fixed item, or inconsistent approval/provider records. The verifier reports the declared proposal source and explicitly labels the diagnostic as manual/no-AI. It remains an unsigned consistency check. The separately observed live sandbox diagnostic below tests the PayPal path without establishing genuine model execution or the required AI-to-payment journey.

## Current hosted PayPal-only diagnostic

The release owner observed a completed manual sandbox diagnostic on deployed Site source `17cbededf`. The [release record](../evidence/diagnostic-release-review.json) covers the fixed $180 USD workflow review with native PayPal sandbox buyer approval and capture. No model was invoked.

| Recorded identity | Value |
| --- | --- |
| Operation | `bf7f982f-fe3a-4d3f-938c-511134e0f32f` |
| PayPal sandbox order | `0UG032264W476633K` |
| PayPal sandbox capture | `4JC48621EJ575850B` |

The deliberate response-drop action left the purchase `UNKNOWN` with $180 reserved. That state persisted through browser reload. A GET of the original order confirmed matching operation/order, seller, amount, currency and completed final capture. A repeated lookup and reload retained the same capture with $120 available, $0 reserved, $180 paid and $0 unknown. The browser warning and error collections were empty for the observed run.

These are real sandbox-provider observations using virtual funds. External network-call counts were not independently measured; stable accounting and capture identity do not by themselves prove that no extra provider request occurred. This successful PayPal-only test does not establish model execution, the standard AI-to-PayPal journey, public judge access or the required video. The application remains owner-private.

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
| Original baseline | 1 | 15 | 17 | 1 | 34 |
| Earlier compatible updates | 0 | 1 | 15 | 2 | 18 |
| After Zod 4.6.7 migration | 0 | 0 | 15 | 2 | 17 |

Raw, dated inputs are retained in the [original baseline](../evidence/npm-audit-2026-11-08-before.json), [earlier compatible-update audit](../evidence/npm-audit-2026-11-08-after.json), and [current Zod 4 audit](../evidence/npm-audit-2026-11-08-zod4.json).

Applied dependency updates:

| Dependency | Final version |
| --- | --- |
| `zod` | 4.6.7; deliberate major-version migration with connector regressions |
| `next`, `eslint-config-next` | 16.4.5 |
| `react`, `react-dom`, `react-server-dom-webpack` | 19.2.8 |
| `vite` | 8.3.6 |
| Direct `esbuild` used by local tests | 0.28.1 |
| Miniflare-scoped `sharp`, `undici`, `ws` overrides | 0.35.5, 7.30.1, 8.22.0 |
| Cloudflare Vite plugin-scoped `ws` override | 8.22.0 |
| Vinext-scoped `image-size` override | 2.0.3 |

Compatible lockfile updates also refreshed `brace-expansion`, `browserslist`, `js-yaml`, `@babel/core`, `baseline-browser-mapping`, `fast-uri` and `fflate`. Vinext `1.0.0-beta.5`, Cloudflare Vite plugin `1.37.1` and Wrangler `4.92.0` were retained. Vinext's React peer ranges accept the patched 19.2.8 trio. A larger framework/runtime migration was not treated as an automatic audit fix. Zod received a separate, tested major-version migration described below.

The lockfile was resolved with `npm install --package-lock-only --ignore-scripts --no-audit`, followed by the named transitive update using `npm update --package-lock-only --ignore-scripts --no-audit`. Actual installation used the approved managed installer, which invokes `npm run install:ci` and `npm ci`. No `npm audit fix --force` or blind major upgrade was run. A fresh checkout can reproduce installation with `npm run install:ci` as documented in [DEVELOPMENT.md](DEVELOPMENT.md).

Patched advisory families include [Next.js Node image response RCE](https://github.com/advisories/GHSA-vcvr-r3jv-pc5j), [Next.js image optimizer](https://github.com/advisories/GHSA-2464-fhr4-w9xw), [Next.js use-cache typed arrays](https://github.com/advisories/GHSA-673q-mjm6-r5xr) and [React Server Components denial of service](https://github.com/advisories/GHSA-wx67-qw84-cm4g). The update removes the affected versions from the audit paths addressed here. It does not establish that each pre-update exploit was reachable in this application.

### Zod finding resolved at this checkpoint

The prior high-severity [Zod collection-validation finding](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5) is absent from the current audit after upgrading 3.25.76 to 4.6.7. Connector callers now give `z.record` explicit key schemas, limit preview grants to 256 and content-block arrays to 1,024. The 10 connector checks cover actual preview binding, response validation, authority restrictions and malformed payloads. Three instrumented oversized-input regressions read all 257/1,025/1,025 elements with the prior installed version; after migration they reject with zero element reads.

The [migration evidence](../evidence/zod-migration-2026-11-08-summary.json) preserves those targeted results, installation and audit. Its combined-suite/build fields were still pending when recorded; the later [release review](../evidence/diagnostic-release-review.json) supplies the passing 151-test run and build results. The array caps do not bound every nested JSON depth, payload size or total process memory. This source review does not claim connector infrastructure is globally unreachable or production-safe.

## Remaining dependency findings

Exact audited package locations follow. These are unresolved findings, even where source inspection suggests a limited exposure.

| Package entry | Severity | Installed location |
| --- | --- | --- |
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

- **Satori 0.16.0 via `@vercel/og` 0.8.6 and Vinext:** [SVG escaping advisory](https://github.com/advisories/GHSA-wx4j-mvgx-mqwp), fixed in 0.33.5. No product `next/og`, `ImageResponse` or attacker-controlled SVG rendering route was found. The pinned parent dependency still carries the finding; a compatible framework/rendering update needs separate verification.
- **Minimatch 10.2.5 in TypeScript ESLint tooling:** [glob amplification denial of service](https://github.com/advisories/GHSA-g3hv-75wg-m249), fixed in 11.0.1. Its observed role is repository lint/type analysis, not purchase-input processing. Forcing the major dependency version underneath the current parser was not attempted.
- **Nested esbuild:** `@esbuild-kit/core-utils` carries 0.18.20, affected by the [development-server CORS advisory](https://github.com/advisories/GHSA-67mh-4wv8-2f99). Wrangler carries 0.27.3, affected by the [Windows development-server file-read advisory](https://github.com/advisories/GHSA-g7r4-m6w7-qqqr). No affected esbuild development server was started during this review; the environment is Linux. These nested copies remain despite the fixed direct esbuild. Follow the respective tooling upgrades rather than declaring the aggregate finding removed.

These reachability assessments are source-based inferences, not exploit tests or proofs of non-reachability. The 17 remaining moderate/low entries prevent a clean dependency-audit claim. Full public/production security clearance is not provided.

## Hosted, visual and external-service boundaries

The release owner separately recorded an authenticated hosted **rehearsal** run in [hosted-recovery-review.json](../evidence/hosted-recovery-review.json). It observed budget rejection, a lower-cost proposal requiring approval, reserved funds, simulated capture-response loss persisting across reload, reconciliation to the same capture and unchanged totals on a repeated check. That checkpoint predates this security patch and does not count as testing the newly deployed build. The export UI showed success, but downloaded bytes were not verified.

The responsive harness in [tests/responsive](../tests/responsive/README.md) renders the production component/CSS with synthetic data and mock fetch. The release owner visually checked receipt views at 360 and 390 pixels, Approvals/Controls at 360, Overview/Purchases at 768 and Evidence at 1280. No document overflow was observed; keyboard Tab plus held Right Arrow scrolled the table, and Escape closed the receipt. A positioned table wrapper corrected page overflow caused by an absolutely positioned screen-reader label; intentional table scrolling remains. The harness blocks external PayPal navigation and mock mutations. It provides layout evidence, not hosted authentication or provider integration evidence.

The current 151 checks do not make any model/PayPal network calls. A mocked sandbox adapter test proves request construction and failure behavior under its fixtures. Earlier real OAuth/order-create/GET observations do not substitute for a genuine model proposal followed by owner approval, sandbox buyer approval, capture and independent GET verification. That complete external chain remains a release-evidence gap.

Before describing the standard AI-to-PayPal journey as verified, retain redacted evidence for that complete chain, including matching operation/order/capture IDs, amount, currency, merchant, final-capture status and the independently fetched provider record. Verify response-loss recovery separately without issuing a second capture. Before public deployment, also establish that the ingress strips caller-supplied identity headers and restricts access as intended; local header tests cannot prove that hosting property.

For other security boundaries and implemented controls, see [SECURITY_REVIEW.md](SECURITY_REVIEW.md). No new release-blocking application defect was observed by the passing local suites. The remaining dependency findings, unverified model execution and standard AI-to-PayPal journey, owner-private access and missing public video remain open. The manual diagnostic has separate deployed sandbox evidence; it does not complete those gates.

## Earlier hosted release and CI checkpoint

Before the manual diagnostic and Zod migration, private deployment of Site source `603541fa` succeeded on 8 November 2026. The [hosted release record](../evidence/hosted-release-review.json) covers the stored receipt panel, a fresh $180 approval/cancellation and reload, and a new unapproved $90 proposal. Available allowance returned to $300 with no reserved or paid amount in the fresh workspace. These are rehearsal results. The [release screenshot](../evidence/hosted-release-qa.png) shows the deployed interface.

The earlier ProofPay GitHub workflow passed all steps at public source `35eb3a19`, including a clean dependency install, types, lint, 131 tests, Worker build and visual-fixture build. The repository-wide workflow stopped on an extra blank line at the end of the inherited ProofPay license; that follow-up removed the blank line without changing license text. Final workflow status must be read from the exact head commit.

These historical hosted/CI results are not evidence for the current diagnostic source. Its deployment and PayPal-only outcome are recorded separately above. Current CI status must still be checked against the exact public revision.
