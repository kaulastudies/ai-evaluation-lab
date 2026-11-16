# ProofPay QA report

This report retains the earlier business-release checkpoint below. For current runtime evidence and the confirmed 8 November 2026 submission, see [judge readiness](JUDGE_READINESS.md) and the [public Devpost project](https://devpost.com/software/proofpay-purchase-desk). Earlier setup-pending and held-submission statements describe that historical checkpoint.

Updated 8 November 2026 for business settings, immutable workspace context, owned history and CSV reporting. The [current local record](../evidence/business-portal-checks-2026-11-08.json) reports **199/199 tests, zero skipped; TypeScript, full lint, native Next.js build and responsive fixture build passed**. The [full dependency audit](../evidence/business-portal-audit-2026-11-08.json) has **zero findings**, including development dependencies.

The [current release record](../evidence/business-portal-release-2026-11-08.json) identifies source `1f4d8d6d5a8decb916d9cfe411a54731d452008a` and production deployment `dpl_6k7XAFTRGZodLDoLjmwK3uLqTM5J` as **READY**. Both preview and production passed **8/8 real PostgreSQL checks**. The preview applied `0002_business_profiles.sql`; production repeated the checksum-locked migrations successfully and completed its build with zero warnings. Both [ProofPay CI](https://github.com/kaulastudies/ai-evaluation-lab/actions/runs/42472825608) and [repository CI](https://github.com/kaulastudies/ai-evaluation-lab/actions/runs/42472825621) passed. Owner-secret transfer remains blocked by automatic approval review; authenticated browser forms, CSV downloads, model and PayPal execution are not established. Final Devpost Submit remains held.

Local evidence: [summary](../evidence/business-portal-checks-2026-11-08.json), [tests](../evidence/business-portal-tests-2026-11-08.log), [types](../evidence/business-portal-types-2026-11-08.log), [lint](../evidence/business-portal-lint-2026-11-08.log), [build](../evidence/business-portal-build-2026-11-08.log) and [visual build](../evidence/business-portal-visual-build-2026-11-08.log). Public static assets were scanned for three dedicated local authentication secrets: 12 files, zero matches. This is a bounded scan, not proof that every possible secret is absent.

The [preceding native release](../evidence/native-vercel-release-2026-11-08.json) passed 178 local tests, six real PostgreSQL checks and the initial/funding migrations. It remains evidence for that source revision, not for the new business views. The former Site's sandbox diagnostic is historical evidence below.

## Current native release checks

| Check | Recorded result | Scope |
|---|---|---|
| `npm test` | 199 passed, zero skipped | Local controlled/synthetic suites; no PayPal/model calls. |
| `npx tsc --noEmit` | Passed | Source types. |
| `npm run lint` | Passed | Full configured lint. |
| `npm run build` | Passed | Native Next.js compilation; not deployment or migration. |
| Responsive fixture build | Passed after the business UI freeze | Bundles actual components with synthetic records; browser inspection remains separate. |
| Full `npm audit --json` | Exit 0; 0 critical/high/moderate/low | Exact lockfile/date, including development dependencies, without advisory exceptions. |
| Actual parser compatibility | 2/2 passed | Scoped minimatch override through TypeScript parser allow/deny paths. Included in local suite; do not add counts. |
| Targeted funding/service/model review | 73/73 passed | Overlaps main suite; request caps, policy and synthetic responses, not live billing. |
| Real PostgreSQL gate | 8/8 passed in preview and again in production on Neon | `tests/review-postgres-live.mjs`; requires explicit database connection and uses a fresh random schema. |
| PostgreSQL migration | New `0002_business_profiles.sql` committed in preview; repeat migration succeeded in production | `scripts/migrate-postgres.mjs` with tracked checksums and transaction/advisory lock. |
| Vercel owner/UI/payment flow | Pending | Owner/PayPal configuration has not yet been saved and verified. Missing configuration must fail closed. |
| Postman collection | Official v2.1 schema valid; 17 scripts parse; five HTTPS guard cases pass | Offline artifact checks; no actual Postman import or API execution. |
| Current production responsive shell | All eight navigation headings, keyboard focus and no horizontal overflow at 360, 768 and 1280 pixels; warning/error collection empty | Setup-pending shell only. Authenticated forms, records, CSV download and owner flow remain unverified. |

Run the source checks from `hackathon/proofpay` with Node 24:

```sh
npx tsc --noEmit
npm run lint
npm test
npm run build
node tests/responsive/build.mjs
```

The separate real-database gate is `node --test tests/review-postgres-live.mjs` with its dedicated connection configured. The current CI/release definition places database checks and migration before release build. A defined gate is not a passing gate; record the actual result and source revision after execution. Do not make database-dependent checks silently skip when configuration is absent.

## Production browser observations

The [release record](../evidence/business-portal-release-2026-11-08.json) and [screenshot](../evidence/business-portal-setup-2026-11-08.jpg) document the canonical production URL. Each of the eight navigation headings was checked at 360, 768 and 1280 pixels without page-level horizontal overflow. Body text was 15px; navigation was 14px on mobile/tablet and 15px on desktop. Minimum navigation height was 48px on mobile/desktop and 46px at tablet width. Keyboard navigation showed a 2.4px solid outline; the collected warnings/errors were empty.

Every observation displayed **Workspace setup pending**. These checks verify that shell's layout and navigation, not sign-in, saved settings, history selection, authenticated purchase actions or CSV file contents. No live AI/model call, new PayPal transaction or personal OpenAI credit use occurred in this release review.

## Business increment checks

The 199-test total includes 17 business-service tests and four CSV tests; these overlap the independently reviewed 21-test subset and must not be added again. Business tests cover owner isolation, field limits, optimistic-version conflicts, immutable workspace/approval snapshots, retained history and held-fund selection guards. The real PostgreSQL suite adds profile persistence and genuinely overlapping selection/approval checks in an isolated schema.

The CSV suite contains 20 assertions across four tests for the actual report builder: saved business context, all loaded active-workspace rows regardless of filter, simulation/source labels, quoting and formula-prefix escaping including whitespace/control/BOM cases. This does not establish downloaded browser file bytes or behavior in every spreadsheet product. Hosted QA still needs a real export reopened and compared with the displayed workspace.

Settings affect future workspaces only. History switching blocks held or uncertain active operations in both modes; the separate explicit simulated reset retains prior history. The department field creates neither multiple users nor separate departmental budgets. These controls do not create an account-wide allowance.

## What the code and tests cover

The shared service retains owner approval, reservation, expiry/renewal, cancellation before dispatch, durable create/capture claims, uncertainty holds and original-order reconciliation. Historical SQLite tests exercise real process races and persisted simulated state. They remain useful service regressions but cannot establish PostgreSQL transaction semantics.

Native tests cover signed sessions, rejected forged identity headers/cookies, exact-origin mutations, login policy, configuration failures and adapter contracts. The PostgreSQL adapter binds values, uses serializable batches and retries only explicitly aborted serialization/deadlock transactions after rollback. It does not retry ambiguous commit/transport failures or external provider work.

The real PostgreSQL suite creates and removes only its fresh random schema. It covers overlapping reservations, audit rollback, competing capture claims, recovery through a fresh adapter, cancellation, funding claims, the durable login limiter, business-profile snapshots and history-selection races. The provider remains synthetic. The disposable CI database may disable TLS only for explicitly permitted loopback tests; remote runtime/migrations retain verified TLS.

Funding tests enforce the fixed Vercel gateway/model/provider, reviewed grant/expiry, one dispatched attempt per workspace and configured grant total. Failures, timeouts and invalid output count; a new workspace does not reset the grant cap. There is no personal OpenAI/API-key path, automatic retry or alternate provider. A successful same-key repeat reads an existing proposal. The free-credit declaration is not independent billing proof.

The receipt verifier checks unsigned internal consistency, including explicit manual/no-AI diagnostic provenance. It does not establish provider authenticity, model execution, event completeness, the real-world time of approval or TIP compatibility.

## Dependency remediation

| Dated stage | Critical | High | Moderate | Low | Total package entries |
|---|---:|---:|---:|---:|---:|
| Original baseline | 1 | 15 | 17 | 1 | 34 |
| Earlier compatible updates | 0 | 1 | 15 | 2 | 18 |
| Zod 4.6.7 migration | 0 | 0 | 15 | 2 | 17 |
| Final native Next.js/Postgres graph | 0 | 0 | 0 | 0 | 0 |

Counts are affected package entries, not independent exploitable vulnerabilities. Current evidence: [remediation summary](../evidence/dependency-remediation-2026-11-08-summary.json), [before](../evidence/npm-audit-2026-11-08-native-before.json), [after](../evidence/npm-audit-2026-11-08-native-after.json), [parser tests](../evidence/dependency-tooling-2026-11-08-tests.log) and [installed tree](../evidence/dependency-tree-2026-11-08-native.txt).

The final install has Next.js 16.4.5, React/React DOM 19.2.8, pg/@types/pg 8.23.1, @vercel/oidc 4.0.7 and Zod 4.6.7. Vinext/Vite/Cloudflare/Wrangler, their scoped overrides, direct RSC and Drizzle migration tooling were removed. A scoped minimatch 11.0.1 override removes the parser dependency's advisory path and passes actual parser compatibility checks. The temporary libSQL dependency is absent. No audit findings were hidden through omission flags, severity filters or accepted exceptions.

The [earlier Zod evidence](../evidence/zod-migration-2026-11-08-summary.json) retains ten connector regressions, including rejection before traversing oversized arrays. Its old pending build/suite fields belong to that checkpoint. Array caps do not bound arbitrary nested JSON depth or total process memory. A zero audit is not a penetration test or production-security certificate.

## Historical PayPal sandbox result

On the former Site source `17cbededf`, the release owner completed the [manual diagnostic](../evidence/diagnostic-release-review.json) with a fixed $180 USD workflow review and no model call.

| Identity | Recorded value |
|---|---|
| Operation | `bf7f982f-fe3a-4d3f-938c-511134e0f32f` |
| PayPal sandbox order | `0UG032264W476633K` |
| PayPal sandbox capture | `4JC48621EJ575850B` |

Native buyer approval preceded capture. Deliberately dropping the response left `UNKNOWN` and $180 reserved through browser reload. A GET of the original order confirmed matching operation/order, seller, amount, currency and completed final capture. Repeated lookup/reload retained the same capture and $120 available / $0 reserved / $180 paid / $0 unknown. The observed browser warning/error collections were empty.

This was a genuine sandbox-provider result using virtual funds. External request counts were not independently measured. It proves neither model inference nor the new Vercel/PostgreSQL/session implementation, and it is not a hosted backend restart test. Do not reuse the old capture as a new deployment result.

## Other historical evidence

- [151-test diagnostic release](../evidence/diagnostic-release-review.json), [131-test summary](../evidence/qa-2026-11-08-summary.json) and [92-test summary](../evidence/independent-review-summary.json): earlier source/runtime checkpoints. Their counts and hashes remain unchanged.
- [Hosted renewal](../evidence/hosted-renewal-review.json), [workspace](../evidence/hosted-workspace-review.json), [recovery](../evidence/hosted-recovery-review.json) and [release](../evidence/hosted-release-review.json): simulated-provider UI/accounting observations on the former runtime.
- [Responsive](../evidence/responsive-review.json) and [readability](../evidence/readability-review.json) reviews: actual components with synthetic records at stated widths, with their own source fingerprints. They do not verify the new owner sign-in or mobile layout.
- The earlier ProofPay GitHub workflow passed at public source `35eb3a19`. That result is not the current workflow/commit result.

Historical evidence includes limited summarized observations, not unrestricted account/network logs. Export success toasts did not always establish downloaded file bytes; preserve each artifact's stated limits. Hashes identify a checkpoint and are not signatures or independent attestations.

## Remaining release evidence

The production release, eight-case real PostgreSQL gate, migrations and both CI runs passed. After authorized credential configuration, inspect the exact Vercel deployment's sign-in/out, denied access, headers, persistence and rehearsal. Configure and rerun the relevant PayPal diagnostic on that runtime. Verify a bounded free-credit model proposal and the complete AI-to-PayPal workflow separately, retaining only sanitized identifiers and outcomes. Independent judge access and a public video remain open.

Do not infer a passing hosted flow from a build, a zero audit, a connected database or the historical diagnostic. [SECURITY_REVIEW.md](SECURITY_REVIEW.md) and [JUDGE_READINESS.md](JUDGE_READINESS.md) describe the remaining boundaries.

## Earlier native deployment checkpoint

[Release evidence](../evidence/native-vercel-release-2026-11-08.json) identifies production deployment `dpl_4ju9LAJwguL8YVk8Nj7DXWaXUupc`, source `5f4592116a605137943973b0aadf38e8cfc061ae`, and the passing [ProofPay CI](https://github.com/kaulastudies/ai-evaluation-lab/actions/runs/42470607942) and [repository CI](https://github.com/kaulastudies/ai-evaluation-lab/actions/runs/42470607796). Production build logs have zero npm warnings. The real-database gate passed before migration/build; no personal model credit or new PayPal transaction was used.
