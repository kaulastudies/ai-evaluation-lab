# ProofPay security review

Reviewed 8 November 2026 against base commit `47dcf677`, with the changes described below. This is a scoped source review and local regression exercise, not a penetration-test certificate, compliance assessment or claim of production readiness. No live payments, secret inspection, key rotation or cloud configuration changes were performed by this review.

## Trust boundary and assets

ProofPay is an owner-only private Site with a merchant-owned PayPal sandbox integration. Its protected assets are the owner's local spending authority, workspace allowance, provider credentials, payment identities and evidence history. A model may suggest a catalogue SKU and rationale; it never grants approval or controls price, seller, currency or budget.

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

## Controls reviewed and retained

- Every API route requires the trusted ingress identity. Operation/evidence reads join the owning workspace; active-workspace constraints protect approval, renewal and cancellation. SQL parameters are bound rather than interpolated from user content.
- Mutations require an exact same-origin `Origin`, JSON media type and compatible Fetch Metadata when supplied. Missing or opaque `Origin` values do not bypass the check. No permissive CORS response is added.
- HTTP action validation runs before constructing a service or accessing the database. Read-only actions cannot invoke mutations through the common handler.
- Catalogue prices and merchant identity come from server data. Model output cannot supply financial authority, and a failed model call cannot become a rehearsal proposal.
- Money is stored as integer cents. Shared allowance reservation is checked inside the serialized SQL write transaction. Cancelled or blocked requests do not hold funds; uncertain provider operations do.
- Provider create/capture intent is stored before dispatch. Capture has one dispatch attempt; later reconciliation reads the original provider order. Missing or ambiguous outcomes never release money automatically.
- Cancellation is allowed only before provider dispatch and retains purchase/request identity. Its audit and status transition share one compare-and-swap transaction. Renewal changes the approval version, invalidating stale execution authority.
- Confirmation requires the approved order identity, operation reference/custom ID, merchant, amount, currency, completed order and completed final capture. The sanitized verification snapshot and confirmation are committed together. A provider response, redirect or order ID alone is insufficient.
- PayPal transport is pinned to the sandbox API host. Buyer approval links are restricted to PayPal sandbox HTTPS hosts. Configured model URLs are trusted deployment configuration, not user-provided destinations.
- Evidence is owner-scoped and contains allowlisted verification/provenance fields. It does not export OAuth tokens, API secrets, raw provider responses or payer records. Raw errors are replaced with bounded application messages; the application does not log credentials.
- The receipt's approval-binding profile permits offline recomputation and comparison with the exported current operation. This is a consistency check on an unsigned application record, not provider authenticity, external attestation or retroactive approval-version evidence for older provider snapshots.

## Validation

The new `tests/review-security.mjs` contains nine focused checks. They exercise chunked and misleading-length input, multibyte limits, early stream cancellation, invalid encoding, action envelopes, actual handler security headers, upstream redirect handling, oversized responses and malformed token handling. Network behavior is mocked; all credentials in these tests are synthetic.

The following targeted run passed 46 checks at implementation time:

```bash
node --test tests/review-security.mjs tests/review-auth.mjs tests/review-ai.mjs tests/review-provider.mjs
node node_modules/typescript/bin/tsc --noEmit
node node_modules/eslint/bin/eslint.js lib/proofpay app/api
```

The independent QA review owns transaction-abort regressions, cross-process reservation tests, cancellation/renewal races and dependency assessment. See `QA_REPORT.md` for the final combined results and their evidence boundaries. Existing provider/model successes from other sessions are not new security-test evidence.

## Remaining limits

- This does not establish ingress header stripping, deployment access rules, hosted header behavior, denial-of-service resistance or the absence of undocumented vulnerabilities. Those require separate deployment checks and an appropriate independent security assessment.
- No global HTML CSP, frame policy or HSTS change was made: framework hydration, private Site embedding and host TLS policy need their own compatibility and deployment review. The strict CSP added here applies to JSON API responses only.
- The API has per-request byte caps but no application-level rate limit, model-spend quota, global retention policy or account-wide purchasing limit. The $300 allowance belongs to one isolated workspace. Owner-only access is material to this prototype's risk model.
- The model service origin is trusted configuration. The application does not implement a general URL allowlist or DNS-based SSRF defense for administrator-supplied model endpoints. Redirects are not followed.
- Audit rows are durable application records, not externally signed or immutable against a privileged database administrator. Failed create/capture diagnostic-event writes may still leave a conservative dispatch state requiring review; they cannot justify a second capture or release.
- Provider calls have timeouts and bounded response reads, but the application does not enforce its own total inbound upload deadline beyond hosting limits.
- There is no live-money mode, webhook handler, automatic uncertain-create retry, production refund/dispute workflow or automatic release of an unresolved provider reservation. Sandbox outcomes use virtual accounts and funds.
- Dependency status changes over time. Use the independent audit's exact lockfile and date; a clean audit cannot certify the application.

## Primary references

- [Cloudflare Workers Request API](https://developers.cloudflare.com/workers/runtime-apis/request/) — documents redirect behavior, including sensitive-header forwarding. Workers supports `manual`; the Fetch-standard `error` mode is not implemented there.
- [Cloudflare D1 database API](https://developers.cloudflare.com/d1/worker-api/d1-database/) — documents transactional batch execution and rollback.
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) — source-origin checks, rejection of simple content types and Fetch Metadata defense.

References were checked on 8 November 2026. They support the control design, not a guarantee about this deployment.
