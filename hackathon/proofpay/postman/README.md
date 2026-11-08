# ProofPay Postman collection

Import [proofpay.postman_collection.json](proofpay.postman_collection.json) to inspect the owner workflow and exported evidence through the same authenticated API used by the application. The file contains no credentials, cookies, private response examples or provider order/capture requests. It is a development artifact, not a completed external integration test or a runtime AI provider.

## Configure once

1. Import the JSON collection in Postman. Version 2.1 is used for a portable single-file handoff.
2. Set the collection's `baseUrl` to the deployment's exact HTTPS `APP_ORIGIN`, with no path or trailing slash. The `.invalid` placeholder is deliberately unusable. Use the canonical application URL; redirects are disabled.
3. Put the generated owner key in your **local Postman Vault** as `proofpay-owner-key`. Restrict the secret to your application host. The login request references `{{vault:proofpay-owner-key}}`; keep the value out of collection/environment exports, saved examples and screenshots.
4. Leave the cookie jar enabled. Send **Login with owner key**. The server issues an eight-hour `__Host-proofpay-session` cookie with Secure, HttpOnly and SameSite=Strict. The client sends the cookie on subsequent HTTPS requests. Do not copy it into a manual `Cookie` header.

The server must already have its durable database, owner configuration and `APP_ORIGIN` configured. A successful import does not supply these resources. Postman requires HTTPS for this Secure cookie; a plain HTTP development URL is not an equivalent test. See [development setup](../docs/DEVELOPMENT.md) for the current runtime requirements.

The collection uses `noauth` because authentication is the owner session cookie, not a bearer token. It does not accept a Sites or Vercel identity header as authorization. Mutations send `Origin: {{baseUrl}}` and `Content-Type: application/json`.

## Rehearsal walkthrough

Send individual requests in this order:

1. **Login with owner key**.
2. **Start seeded rehearsal**. This creates a $300 simulated workspace and selects its proposed $180 workflow review. It sets `operationId`, `approvalVersion` and `mode` in the collection.
3. **Get current state**. Inspect the selected operation, seller, amount, status and current approval version.
4. **Approve selected operation**. Verify that $180 is reserved and $120 remains available.
5. **Get selected operation evidence**. The receipt identifies rehearsal mode and its recorded approval.
6. **Cancel before dispatch**, then **Get current state**. For this untouched approved request, the allowance should return to $300 with no reservation.
7. **Logout** when finished.

These steps call the application and change its demonstration workspace. They make no model or PayPal calls. Do not run the whole collection indiscriminately: workspace creation, cancellation, renewal and diagnostic requests are alternatives with different state preconditions.

To test a new request, choose **Start empty workspace** with `mode=rehearsal`, then **Propose workflow review**. Inspect the returned state and copy the intended ID into `operationId`. Keep `proposalKey` unchanged for a retry of the same request; use a different key for a distinct request. **Renew expired approval** requires an eligible expired approval, so rejection of a fresh or cancelled request is expected.

Use the collection variables directly for this walkthrough. An environment or runner data file can override them and prevent the collection's response scripts from updating the values you actually send. The scripts never store the owner key or session cookie in a collection variable.

## Sandbox paths

**Start manual PayPal diagnostic** needs the server's PayPal sandbox configuration. It creates one fixed, unapproved $180 workflow review with explicit manual/no-AI provenance. Starting it makes no provider or model request. Additional proposals are blocked in that workspace. Complete native buyer approval and provider actions in the application when deliberately testing the full sandbox payment path.

For a standard AI workspace, set `mode=sandbox` and choose **Start empty workspace**. **Propose workflow review** consumes one durable attempt under the reviewed Vercel free-credit grant. The code permits one dispatch per workspace and a configured grant total (currently one); failed, timed-out and invalid responses consume the attempt. There is no automatic retry or alternate provider. Retrying the same successful request key reads its stored proposal. Creating another workspace does not reset the grant total. The gateway configuration and actual execution remain subject to [RESOURCE_PLAN.md](../docs/RESOURCE_PLAN.md). Personal OpenAI/API-key paths are rejected. A Postman plan or its Agent Mode credits do not supply ProofPay's runtime inference.

Both sandbox paths retain owner approval, allowance and evidence controls. An active reserved or uncertain sandbox operation blocks switching workspaces. Do not clear the ledger or start another payment to hide an uncertain outcome.

## Reading results

Each eligible request expects HTTP 200, JSON and `Cache-Control: no-store`. Session requests also check issuance/clearing of the expected cookie. State responses refresh the selected operation's approval version; evidence checks confirm the receipt schema and operation identity. These response assertions do not independently authenticate provider records or prove financial correctness.

| Response | Meaning / next step |
|---|---|
| `401 AUTH_REQUIRED` | Sign in; check HTTPS, cookie jar and expiry. |
| `401 AUTH_INVALID` | The owner key did not match. Do not retry blindly. |
| `403 ORIGIN_REJECTED` | URL and Origin must match the configured canonical application origin. |
| `429 LOGIN_RATE_LIMITED` | The private desk admits at most ten login attempts per minute across instances; honor `Retry-After`. |
| `503 AUTH_NOT_CONFIGURED` or `DATABASE_UNAVAILABLE` | Complete the server-side configuration before testing. |
| `400 UNSUPPORTED_FIELD` / `INVALID_VERSION` | Use the documented body and current positive integer approval version. |
| `409 SANDBOX_WORKSPACE_HELD` | Resolve the existing reserved or uncertain sandbox operation. |
| `409 DIAGNOSTIC_FIXED_CATALOGUE` | The manual diagnostic deliberately rejects another proposal. |
| `409 AI_ALLOWANCE_USED` | The workspace attempt or total free grant is consumed. No further model request was dispatched; do not delete ledger rows or change grant IDs to retry. |
| `503 AI_FUNDING_EXPIRED` / `AI_FUNDING_RESTRICTED` | Stop and review the configured free-credit declaration. Do not add personal keys or paid fallback. |

An expected rejection appears as a failed generic HTTP-200 assertion. Inspect the response's `code` and the operation state; do not weaken the server to make the assertion pass.

The collection has been checked against the official 2.1 schema and its embedded JavaScript parsed locally. It has not yet been imported or executed in Postman against the migrated Vercel deployment. No Postman account, subscription, paid feature or sponsor award eligibility has been established by creating it. Record actual execution separately with source revision and sanitized results.

Official references: [collection schema](https://schema.postman.com/json/collection/v2.1.0/collection.json), [request body variables and Vault references](https://learning.postman.com/docs/use/send-requests/create-requests/parameters), [cookie behavior](https://learning.postman.com/docs/use/send-requests/response-data/cookies/).
