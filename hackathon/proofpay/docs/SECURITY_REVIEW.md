# ProofPay security review

Reviewed 8 November 2026, beginning with base commit `47dcf677` and updated for the manual sandbox diagnostic and Zod 4.6.7 migration. The [current release record](../evidence/diagnostic-release-review.json) and [migration evidence](../evidence/zod-migration-2026-11-08-summary.json) distinguish the later checks from the original review. This is a scoped source review and local regression exercise, not a penetration-test certificate, compliance assessment or claim of production readiness. No real-money payments, secret inspection, key rotation or cloud configuration changes were performed by this source review. The release owner's separate sandbox diagnostic is recorded below.

## Trust boundary and assets

ProofPay is an owner-only private Site with a merchant-owned PayPal sandbox integration. Its protected assets are the owner's local spending authority, workspace allowance, provider credentials, payment identities and evidence history. A model may suggest a catalogue SKU and rationale; it never grants approval or controls price, seller, currency or budget.

The explicit manual sandbox diagnostic creates one fixed $180 workflow review request without a model call. It shares the financial controls and trusted owner boundary. It does not supply an AI proposal, grant approval or dispatch a payment when started; its interface and receipts retain the manual/no-AI classification.

The application trusts the private Sites ingress to authenticate the visitor, remove any caller-supplied `oai-authenticated-user-id` and supply its own identity. The application does not independently verify that header cryptographically. A raw Worker exposed on another ingress that accepts forged identity headers would violate this threat model. The local header tests cannot prove hosting ingress behavior. Owner-only access and absence of a bypass endpoint must be checked separately when deploying.

The review considered cross-site browser requests, malformed or oversized API input, another authenticated tenant guessing operation IDs, malicious model content, unexpected upstream responses and redirects, duplicate workers, concurrent approval/cancellation, process interruption and failed database statements. A compromised hosting administrator, database writer or secret store is outside the protection provided by these application controls.

## Findings and changes

| Finding | Consequence before change | Implemented control |
| --- | --- | --- |
| Request size was checked after `request.text()` buffered the whole payload | The 10,000-character check did not bound memory while reading and did not count UTF-8 bytes | Stream and stop at 10,000 bytes; reject an oversized declared length before reading; reject unsupported compression and invalid UTF-8 |
| Credentialed upstream fetches used automatic redirects | Cloudflare Workers documents forwarding Authorization headers to redirect destinations, including other hosts | PayPal token/order and model requests use `redirect: manual`; every non-success response fails closed without following or retrying |
| Upstream JSON responses were parsed without a size cap | An unexpected large response could exhaust Worker resources before parsing/validation | Token response capped at 16 KiB; order and model responses capped at 256 KiB; token type, size and whitespace validated |
| Proposal/source and approval/audit were separate writes | A failed event write could leave a proposal without model provenance or a reservation without its approval event; a retry would not repair it | Proposal plus source record and approval plus reservation now use D1 transactional batches with conditional inserts; failure rolls back the state change |
| JSON media-type matching accepted lookalike prefixes; action envelopes relied mostly on downstream assumptions | Invalid clients could receive inconsistent validation and unsupported fields were silently ignored | Exact JSON media type, action-specific method/field allowlists, positive integer approval version, UUID operation IDs, and nonblank well-formed ingress identity |
| API responses had only basic cache/type headers | Evidence JSON lacked explicit referrer, cross-origin embedding and document policies | All handled API success/error responses use `no-store`, `nosniff`, `no-referrer`, `Cross-Origin-Resource-Policy: same-origin`, and a restrictive JSON-document CSP |
| Receipt omitted the workspace ID used by its approval hash | An offline reader could not reconstruct the actual approval hash input | Owner-only receipt schema v1 includes the workspace ID and exact ordered `proofpay-approval-v1` binding profile; existing hashes are unchanged |
| Zod 3.25.76 retained a high-severity collection-validation finding in connector infrastructure | Oversized arrays could still traverse their elements before rejection | Tested migration to Zod 4.6.7, explicit record key schemas, 256-grant and 1,024-content-block limits; the current audit no longer lists Zod |

## Controls reviewed and retained

- Every API route requires the trusted ingress identity. Operation/evidence reads join the owning workspace; active-workspace constraints protect approval, renewal and cancellation. SQL parameters are bound rather than interpolated from user content.
- Mutations require an exact same-origin `Origin`, JSON media type and compatible Fetch Metadata when supplied. Missing or opaque `Origin` values do not bypass the check. No permissive CORS response is added.
- HTTP action validation runs before constructing a service or accessing the database. Read-only actions cannot invoke mutations through the common handler.
- Catalogue prices and merchant identity come from server data. Model output cannot supply financial authority, and a failed model call cannot become a rehearsal proposal.
- The manual diagnostic endpoint accepts only an empty JSON object and requires trusted owner identity, same-origin JSON and PayPal configuration. It fixes the catalogue item server-side; additional proposals are rejected in that profile. Standard sandbox proposals still require a model response.
- Diagnostic creation stores the workspace, fixed proposal, manual/no-AI provenance and session update in a D1 batch. A failed provenance insert rolls the batch back. Starting the diagnostic makes no model or provider call; approval, reservation, buyer preflight, dispatch and recovery use the existing service methods. A held sandbox operation prevents hiding that workspace by starting another.
- Money is stored as integer cents. Shared allowance reservation is checked inside the serialized SQL write transaction. Cancelled or blocked requests do not hold funds; uncertain provider operations do.
- Provider create/capture intent is stored before dispatch. Capture has one dispatch attempt; later reconciliation reads the original provider order. Missing or ambiguous outcomes never release money automatically.
- Cancellation is allowed only before provider dispatch and retains purchase/request identity. Its audit and status transition share one compare-and-swap transaction. Renewal changes the approval version, invalidating stale execution authority.
- Confirmation requires the approved order identity, operation reference/custom ID, merchant, amount, currency, completed order and completed final capture. The sanitized verification snapshot and confirmation are committed together. A provider response, redirect or order ID alone is insufficient.
- PayPal transport is pinned to the sandbox API host. Buyer approval links are restricted to PayPal sandbox HTTPS hosts. Configured model URLs are trusted deployment configuration, not user-provided destinations.
- Evidence is owner-scoped and contains allowlisted verification/provenance fields. It does not export OAuth tokens, API secrets, raw provider responses or payer records. Raw errors are replaced with bounded application messages; the application does not log credentials.
- The receipt's approval-binding profile permits offline recomputation and comparison with the exported current operation. This is a consistency check on an unsigned application record, not provider authenticity, external attestation or retroactive approval-version evidence for older provider snapshots.
- The offline verifier accepts diagnostic receipts only in sandbox mode, with the fixed $180 item and matching manual/no-AI provenance. It reports that classification explicitly while retaining all approval/provider consistency checks. Neither that label nor a passing digest authenticates a provider or establishes AI execution.

## Validation

`tests/review-security.mjs` contains nine focused checks. They exercise chunked and misleading-length input, multibyte limits, early stream cancellation, invalid encoding, action envelopes, actual handler security headers, upstream redirect handling, oversized responses and malformed token handling. Network behavior is mocked; all credentials in these tests are synthetic.

The following historical targeted run passed 46 checks when the initial request/transport controls were implemented:

```bash
node --test tests/review-security.mjs tests/review-auth.mjs tests/review-ai.mjs tests/review-provider.mjs
node node_modules/typescript/bin/tsc --noEmit
node node_modules/eslint/bin/eslint.js lib/proofpay app/api
```

The later combined local run passed 151 checks, with 0 failures or skips, as reported by the release owner. It includes six diagnostic tests, 27 receipt tests and 10 connector tests, alongside the existing auth, model, provider, service, security and database suites. Full typecheck, lint, Worker build and responsive fixture build also passed. See [QA_REPORT.md](QA_REPORT.md) and the [current release record](../evidence/diagnostic-release-review.json) for that checkpoint and its limits; the earlier 46-check result is not a current combined run.

The diagnostic regressions cover authentication/configuration, action-body restrictions, provenance rollback, owner and buyer approval, uncertainty holds and recovery without another capture. The connector migration's instrumented oversized collections failed against the prior installed Zod and pass with zero element reads under 4.6.7. Its limits bound collection counts, not arbitrary nested JSON size, depth or total memory. The [migration audit](../evidence/npm-audit-2026-11-08-zod4.json) retains 17 affected package entries: 15 moderate, 2 low, 0 high and 0 critical. This is not a clean-audit claim.

Provider/model responses in these suites are synthetic. Separately, the release owner completed the manual PayPal sandbox diagnostic on deployed Site source `17cbededf`: native buyer approval, $180 capture, response loss with the reservation retained through reload, and original-order verification of matching amount, seller, currency, operation/order and completed final capture. Repeated lookup/reload retained the same capture and $120 available / $0 reserved / $180 paid / $0 unknown. No browser warnings or errors were reported. See the [release record](../evidence/diagnostic-release-review.json) for identifiers and observations.

That hosted run uses virtual funds and explicitly makes no AI claim. External provider request counts were not independently measured; the observed stable capture/accounting does not establish a general exactly-once guarantee. Genuine model execution, the standard AI-to-PayPal journey, independent judge access and the public video remain open. Earlier rehearsal and local test results retain their separate scopes.

## Remaining limits

- This does not establish ingress header stripping, deployment access rules, hosted header behavior, denial-of-service resistance or the absence of undocumented vulnerabilities. Those require separate deployment checks and an appropriate independent security assessment.
- No global HTML CSP, frame policy or HSTS change was made: framework hydration, private Site embedding and host TLS policy need their own compatibility and deployment review. The strict CSP added here applies to JSON API responses only.
- The API has per-request byte caps but no application-level rate limit, model-spend quota, global retention policy or account-wide purchasing limit. The $300 allowance belongs to one isolated workspace. Owner-only access is material to this prototype's risk model.
- The model service origin is trusted configuration. The application does not implement a general URL allowlist or DNS-based SSRF defense for administrator-supplied model endpoints. Redirects are not followed.
- Audit rows are durable application records, not externally signed or immutable against a privileged database administrator. Failed create/capture failure-event writes may still leave a conservative dispatch state requiring review; they cannot justify a second capture or release.
- Provider calls have timeouts and bounded response reads, but the application does not enforce its own total inbound upload deadline beyond hosting limits.
- There is no live-money mode, webhook handler, automatic uncertain-create retry, production refund/dispute workflow or automatic release of an unresolved provider reservation. Sandbox outcomes use virtual accounts and funds.
- Dependency status changes over time. Use the independent audit's exact lockfile and date; a clean audit cannot certify the application.

## Primary references

- [Cloudflare Workers Request API](https://developers.cloudflare.com/workers/runtime-apis/request/) — documents redirect behavior, including sensitive-header forwarding. Workers supports `manual`; the Fetch-standard `error` mode is not implemented there.
- [Cloudflare D1 database API](https://developers.cloudflare.com/d1/worker-api/d1-database/) — documents transactional batch execution and rollback.
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) — source-origin checks, rejection of simple content types and Fetch Metadata defense.

References were checked on 8 November 2026. They support the control design, not a guarantee about this deployment.
