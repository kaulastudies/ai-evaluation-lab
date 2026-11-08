# ProofPay QA report

Updated 8 November 2026 for the GitHub/Vercel/Neon migration. The release owner reports **178/178 local tests, TypeScript, full lint, native Next.js build and responsive fixture build passed**. The final dependency audit reports **zero known findings**, including development dependencies. These checks do not establish a working hosted owner session, a live PostgreSQL result, model inference or a new PayPal run.

Neon is connected to the new Vercel project. Schema execution, owner/PayPal configuration and the migrated hosted workflow are pending at this checkpoint. The earlier Site's sandbox diagnostic is recorded below as historical evidence. Final Devpost Submit remains held.

Current local evidence: [check summary](../evidence/native-vercel-checks-2026-11-08.json), [tests](../evidence/native-vercel-tests-2026-11-08.log), [types](../evidence/native-vercel-types-2026-11-08.log), [lint](../evidence/native-vercel-lint-2026-11-08.log), [build](../evidence/native-vercel-build-2026-11-08.log) and [visual build](../evidence/native-vercel-visual-build-2026-11-08.log).

The 178-test record includes three subprocess regressions proving that malformed database URLs and connection/cleanup/transaction failures do not expose credential material. Public static assets were also scanned for the three dedicated local authentication secrets: 12 files, zero matches.

## Current native release checks

| Check | Recorded result | Scope |
|---|---|---|
| `npm test` | 178 passed, reported by the release owner | Local controlled/synthetic suites; no PayPal/model calls. |
| `npx tsc --noEmit` | Passed | Source types. |
| `npm run lint` | Passed | Full configured lint. |
| `npm run build` | Passed | Native Next.js compilation; not deployment or migration. |
| Responsive fixture build | Passed after the final login fix | Bundles actual components with synthetic records; browser inspection remains separate. |
| Full `npm audit --json` | Exit 0; 0 critical/high/moderate/low | Exact lockfile/date, including development dependencies, without advisory exceptions. |
| Actual parser compatibility | 2/2 passed | Scoped minimatch override through TypeScript parser allow/deny paths. Included in local suite; do not add counts. |
| Targeted funding/service/model review | 73/73 passed | Overlaps main suite; request caps, policy and synthetic responses, not live billing. |
| Real PostgreSQL gate | Pending | `tests/review-postgres-live.mjs`; requires explicit database connection and uses a fresh random schema. |
| PostgreSQL migration | Pending | `scripts/migrate-postgres.mjs` with tracked checksums and transaction/advisory lock. |
| Vercel owner/UI/payment flow | Pending | Owner/PayPal configuration has not yet been saved and verified. Missing configuration must fail closed. |
| Postman collection | Official v2.1 schema valid; 17 scripts parse; five HTTPS guard cases pass | Offline artifact checks; no actual Postman import or API execution. |
| New responsive interface | Source refinements and scoped frontend checks completed | Current screenshot/browser verification is separate; older screenshots remain historical. |

Run the source checks from `hackathon/proofpay` with Node 24:

```sh
npx tsc --noEmit
npm run lint
npm test
npm run build
node tests/responsive/build.mjs
```

The separate real-database gate is `node --test tests/review-postgres-live.mjs` with its dedicated connection configured. The current CI/release definition places database checks and migration before release build. A defined gate is not a passing gate; record the actual result and source revision after execution. Do not make database-dependent checks silently skip when configuration is absent.

## What the new code and tests cover

The shared service retains owner approval, reservation, expiry/renewal, cancellation before dispatch, durable create/capture claims, uncertainty holds and original-order reconciliation. Historical SQLite tests exercise real process races and persisted simulated state. They remain useful service regressions but cannot establish PostgreSQL transaction semantics.

Native tests cover signed sessions, rejected forged identity headers/cookies, exact-origin mutations, login policy, configuration failures and adapter contracts. The PostgreSQL adapter binds values, uses serializable batches and retries only explicitly aborted serialization/deadlock transactions after rollback. It does not retry ambiguous commit/transport failures or external provider work.

The real PostgreSQL suite creates and removes only its fresh random schema. It covers overlapping reservations, audit rollback, competing capture claims, recovery through a fresh adapter, cancellation, funding claims and the durable login limiter. The provider remains synthetic. The disposable CI database may disable TLS only for explicitly permitted loopback tests; remote runtime/migrations retain verified TLS.

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

Complete the real PostgreSQL gate and schema migration, then inspect the exact Vercel deployment's sign-in/out, denied access, headers, persistence and rehearsal. Configure and rerun the relevant PayPal diagnostic on that runtime. Verify a bounded free-credit model proposal and the complete AI-to-PayPal workflow separately, retaining only sanitized identifiers and outcomes. Independent judge access and a public video remain open.

Do not infer a passing hosted flow from a build, a zero audit, a connected database or the historical diagnostic. [SECURITY_REVIEW.md](SECURITY_REVIEW.md) and [JUDGE_READINESS.md](JUDGE_READINESS.md) describe the remaining boundaries.
