# ProofPay security review


Updated 8 November 2026 for native Next.js/Node 24, Vercel, Neon/PostgreSQL and signed owner sessions. This is a scoped source/regression review, not a penetration-test certificate, compliance assessment or production clearance. The earlier Sites ingress model and its hosted results are historical.

The current local release reports 178/178 tests, TypeScript, full lint, Next.js build and responsive fixture build passed. The [full dependency audit](../evidence/dependency-remediation-2026-11-08-summary.json) reports zero known findings, including development dependencies. Six real PostgreSQL checks and schema application passed separately. The newly deployed owner/payment workflow remains gated by credential provisioning and live verification.

Current local check record: [native verification summary](../evidence/native-vercel-checks-2026-11-08.json). Hosted and real-database gates remain separate.

## Assets and trust boundaries

The application protects the owner's purchase authority, workspace allowance, server credentials, durable operation identities and evidence. A model can propose a permitted SKU/rationale; it cannot approve, set prices or execute payment. The browser requests actions but cannot write a confirmed payment directly.

The server trusts its configured owner hash/session secret, PostgreSQL connection, PayPal merchant configuration and reviewed inference grant. Compromise of these server settings or privileged database access is outside the protection established by the application checks. There is one private owner, not a multi-user organization or identity-management product.

## Current controls

| Boundary | Implemented behavior | Limit of the claim |
|---|---|---|
| Owner authentication | Dedicated key checked with salted scrypt; HMAC-signed eight-hour owner session. Sites/Vercel identity headers are ignored for authorization. | Owner configuration and hosted login still need execution evidence. No MFA, account recovery or multi-user roles. |
| Session transport | `__Host-proofpay-session`, Secure, HttpOnly, SameSite=Strict, host-only, `Path=/`; exact canonical application origin. | Logout clears this client's cookie, not copied tokens. Expiry or secret rotation handles revocation boundaries. |
| Login work limit | Durable global cap of ten attempts/minute across instances; 429 and `Retry-After: 60`. | A global cap can temporarily deny the owner access during abusive traffic; it is not broad DoS prevention. |
| API authority | Owner-scoped reads/actions, exact same-origin JSON mutations, compatible Fetch Metadata and action/method/field/version validation. | An operation ID is not authority. Hosted behavior requires its own verification. |
| Input bounds | Streamed application bodies stop at 10,000 bytes; login is limited to 4,096 bytes; unsupported encoding and invalid UTF-8 rejected. | Hosting upload/time/resource limits remain relevant. |
| Upstream transport | Sandbox PayPal host; restricted buyer-approval links; manual redirect handling; bounded token/order/model reads and timeouts. | No automatic retry establishes that an uncertain effect failed. |
| PostgreSQL | Bound values, certificate-verified TLS, conditional financial writes and serializable batches. Explicit serialization/deadlock aborts may retry only after successful rollback, at most three retries. | Ambiguous transport/commit failures are not retried. Real database concurrency/rollback checks are a separate gate. |
| Approval and allowance | Exact purchase/version/expiry binding, reservation and audit in one transaction; pre-dispatch cancellation/renewal preserve history. | $300 is a per-workspace demonstration allowance, not an account-wide/bank limit. |
| Provider outcome | Expected operation/order, seller, amount, currency and completed final capture must match; confirmation and its limited snapshot persist together. | A return URL, successful HTTP status or model statement is not confirmation. |
| Inference funding | Fixed Vercel gateway/model/provider, request-context OIDC, reviewed expiring grant, durable one-attempt/workspace and total cap; failures count. Personal/API-key paths and fallback are rejected. | Flags are operator declarations, not live billing verification. No actual inference is established by configuration. |
| Page/browser policy | `nosniff`, `no-referrer`, `X-Frame-Options: DENY`, disabled camera/microphone/geolocation, frame/base/object/form CSP constraints; no framework powered-by header. | This is not a comprehensive script-source CSP or XSS proof. Actual deployed headers remain to be checked. |
| API evidence | No-store JSON, same-origin resource policy and restrictive JSON-document CSP; allowlisted provenance/provider fields. | Records are unsigned and not immutable against an administrator. |

## Manual diagnostic and receipts

`POST /api/sandbox/diagnostic/start` accepts only `{}` and requires owner authentication, same-origin JSON and PayPal configuration. It stores one fixed $180 workflow review with manual/no-AI provenance. It makes no provider/model call when started, rejects additional proposals and shares approval, reservation, buyer-preflight, dispatch and recovery code. A held active sandbox cannot be hidden by switching workspaces.

The version 1 receipt includes the ordered approval binding, digest and limited verification fields. The offline verifier checks internal consistency and labels manual diagnostic records explicitly. It does not authenticate PayPal, a model, the author, current authority or TIP compatibility. Someone able to replace the record can recompute its digest; historical approval-version/item evidence is limited.

## Validation and dependency changes

The 178 local checks cover the shared financial service, controlled provider/model behavior, authentication, request hardening, database rollback/races, receipts, connectors, funding, native-runtime adapters and parser compatibility. Their external responses are synthetic. The funding review separately passed 73 targeted checks, overlapping the main suite; counts must not be added together. Six real PostgreSQL checks passed using an isolated random schema and no external model/PayPal calls.

The final [native audit](../evidence/npm-audit-2026-11-08-native-after.json) completed with exit 0 and no findings or advisory exceptions. Removing Vinext/Cloudflare/Wrangler and Drizzle tooling removed their vulnerable transitive paths. A scoped `minimatch` override was checked through the actual TypeScript parser. Earlier 34-, 18- and 17-entry snapshots remain historical; the temporary libSQL branch was removed. The exact graph, install and parser checks are in the [remediation summary](../evidence/dependency-remediation-2026-11-08-summary.json). Zero known audit findings does not prove the absence of application vulnerabilities.

The [historical PayPal diagnostic](../evidence/diagnostic-release-review.json), source `17cbededf`, completed buyer approval, a $180 capture, response-loss recovery and stable accounting using virtual funds. It used no model and did not independently measure provider request counts. It cannot certify the new authentication/database/deployment boundary.

## Open security and delivery gates

- PostgreSQL migrations and the six live database checks passed. Inspect actual Vercel login/logout, authorization, headers and authenticated persistence after credential configuration.
- Configure owner/PayPal values through an authorized private server-side channel. Until then, missing configuration must remain closed; do not introduce a bypass for a demo.
- The release owner confirmed the selected model's free-credit eligibility. Verify actual bounded inference and recorded credit usage before claiming the AI path works. Keep personal OpenAI credits excluded.
- Establish independent judge access without publishing the owner key or database/payment credentials.
- Broader rate limiting, MFA/recovery, retention, monitoring, incident response, backup restoration and independent security assessment remain future work.

There is no production-money mode, webhook/refund/dispute/fulfillment workflow or automatic release of uncertain reservations. No fraud-elimination, regulatory-compliance, processor-parity or general exactly-once guarantee is claimed. Final Devpost submission remains held.

## Verified deployment checkpoint

[Release evidence](../evidence/native-vercel-release-2026-11-08.json) identifies production deployment `dpl_4ju9LAJwguL8YVk8Nj7DXWaXUupc`, source `5f4592116a605137943973b0aadf38e8cfc061ae`, and the passing [ProofPay CI](https://github.com/kaulastudies/ai-evaluation-lab/actions/runs/42470607942) and [repository CI](https://github.com/kaulastudies/ai-evaluation-lab/actions/runs/42470607796). Production build logs have zero npm warnings. The real-database gate passed before migration/build; no personal model credit or new PayPal transaction was used.
