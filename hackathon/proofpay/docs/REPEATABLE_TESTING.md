# Repeatable ProofPay checks

Judges can repeat the financial-control and receipt checks without PayPal credentials, a model key, an owner key or a database account. These checks execute the application service with temporary local databases and a simulated provider. They do not repeat the recorded live AI-to-PayPal purchase.

The reviewed live model grant has already been consumed. Do not delete its attempt records, change its grant ID, raise its limit or request another proposal to reproduce a demonstration. Rehearsal does not use that grant.

## Reproduce the source checks

Use Node.js 24.x. From a clean checkout of the public source:

```sh
git clone --branch proofpay/purchase-desk-v0.1 https://github.com/kaulastudies/ai-evaluation-lab.git
cd ai-evaluation-lab/hackathon/proofpay
npm run install:ci
npm test
npx tsc --noEmit
npm run lint
```

The installer needs registry access. The tests above do not need external service credentials. Keep any existing environment files private; these commands do not require creating or loading one. Do not run an installer while another process is using the same checkout's dependencies.

For a short, repeatable recovery-and-receipt check after installation:

```sh
node --test --test-name-pattern='response loss survives fresh process|actual local service exports verify|CLI exits zero for local rehearsal' tests/review-service.mjs tests/review-receipt.mjs
```

This runs three checks. Their fixtures start fresh automatically and are removed afterward:

1. The real service approves a $180 rehearsal request, creates its simulated order and captures with deliberate response loss. The request remains `UNKNOWN` with $180 reserved. A new Node process opens the persisted SQLite database, checks the original order twice and confirms $180 paid with $0 reserved. Capture is forbidden in that restarted process. The original order and capture request IDs remain unchanged, with one confirmation event and one simulated capture.
2. A separately generated rehearsal goes through proposed, approved, order-ready, unknown and confirmed states. The independent receipt verifier checks each exported record.
3. The receipt CLI accepts the locally generated confirmed record and rejects a mutated record, with the expected process exit codes.

The first check is a genuine process restart using temporary SQLite storage. It is not a PostgreSQL, hosted-session, model or PayPal test. The wider `npm test` suite adds competing processes, authorization, isolation, business profile conflicts, cancellation/renewal races, provider-evidence mutations, funding limits and CSV encoding.

## Current seven-view checkpoint

The [seven-view source review](../evidence/judge-portal-source-qa-2026-11-08.json), checkpoint `26893ed6`, passed **210/210 local tests**, TypeScript, full lint and build. Current runtime `cfd1d007` passed both CI workflows and **9/9 real PostgreSQL checks with no skips**, committed migrations, TypeScript and the Next.js 16.4.5 build.

The [current browser record](../evidence/judge-portal-browser-qa-2026-11-08.json) completed all **six workflow observations** on `cfd1d007`: approval, competing-request block, dropped response, retained hold through reload, original-order recovery and unchanged repeat. Overview reopened the same unresolved purchase, Evidence inspected its selected receipt, and the captured application console was empty.

All seven views were checked at 360, 768 and 1280px: **21 responsive measurements**, no horizontal overflow and 16px main text. These layout measurements were taken at `26893ed6`; `cfd1d007` changes preferred workflow selection only. This is connected-browser review, not incognito automation or a full accessibility/security assessment. No new model or PayPal call was made.

The historical checkpoint below remains unchanged. Its **21 HTTPS outcomes across two guests** are a separate isolation/recovery review, not the new 21-layout count.

## Measured checkpoint

The following records describe the earlier owner and three-view judge releases, not the current seven-view browser review.

An independent run on 8 November 2026 used source commit `c2c5848`:

| Command | Observed result |
|---|---|
| `npm test` | 199 passed, 0 failed, 0 skipped; test runner duration 2,297 ms. |
| Focused command above | 3 passed, 0 failed, 0 skipped; test runner duration 510 ms. |
| `npx tsc --noEmit` | Exit 0, no TypeScript diagnostics. |
| `npm run lint` | Exit 0, no ESLint diagnostics. |

After both judge backend and frontend were frozen, the same independent review reran the expanded working tree based on `c2c5848`: **210 passed, 0 failed, 0 skipped**, with a test-runner duration of 2,514 ms. TypeScript and full ESLint exited 0 with no source diagnostics. The earlier initial-effect lint issue was corrected before this final rerun. The eleven added judge tests cover distinct signed guests, guest/owner isolation, deployment guards, origin and action validation, no external calls, retained funding records, reset limits and concurrent quota claims.

The final `npm run build` also exited 0: Next.js 16.4.5 compiled successfully, completed its TypeScript pass and generated all 12 static pages. The `/judge` page and judge API remain dynamic routes. This build does not execute the authenticated purchase flow.

The local npm launcher printed `Unknown env config "http-proxy"`. That environment warning was recorded, not suppressed; it was not a TypeScript, ESLint or test failure. The installer, dependency audit, nine-test PostgreSQL gate and browser checks were not rerun as part of these checkpoints. Later source changes need their own results.

The released judge source is `2caa74039fee7c136fb892084225a8235b4b4ea6` on deployment `dpl_Hazv9A9bHbQQmffM74iJU6obvWE3`. The release owner reviewed its build logs: **9/9 real PostgreSQL checks passed**, followed by the checksum-locked migrations and build. That hosted database result is separate from the local SQLite-backed tests above.

Independent hosted HTTP checks then passed against the canonical judge deployment: **21 requests with the expected outcomes**, using two new in-memory guest cookie jars. Cross-guest receipt reads and approval were denied; the second guest's records stayed unchanged. Wrong-origin session creation, owner login and sandbox proposals were rejected. The first guest completed the $180 reservation/$160 budget block, simulated response loss, fresh state read, original-order reconciliation and repeated lookup with unchanged capture and totals. Resetting only that guest's simulation created a new workspace while retaining the earlier receipt.

The reviewer downloaded the actual 4,254-byte operation receipt through HTTPS and ran `scripts/verify-receipt.mjs` successfully against those bytes. This proves the downloaded application's receipt is internally consistent, not provider authenticity or a browser Blob download. The [sanitized hosted report](../evidence/judge-hosted-qa-2026-11-08.json) records request outcomes, source/deployment identity, receipt hash and limits. Cookie values and the raw receipt were not retained. No model, PayPal or owner-browser action was requested by these checks, and the consumed AI grant was not reset.

## Real database integration, separately

An authorized developer with a dedicated PostgreSQL test connection can run:

```sh
node --env-file=/absolute/path/to/private-test.env --test tests/review-postgres-live.mjs
```

The private file should supply `PROOFPAY_TEST_DATABASE_URL`. That value takes precedence over the runtime connection names. Do not commit the file or paste its contents into logs. The connection must permit creation and deletion of a fresh test schema; use a dedicated test database or role.

The test creates a randomly named `proofpay_test_*` schema, applies the checked-in PostgreSQL migrations inside it and removes that schema afterward. It exercises the real PostgreSQL adapter, overlapping reservations, rollback, capture/recovery, profile snapshots and selection/approval races. Model and payment outcomes remain simulated. Missing database configuration fails explicitly rather than silently skipping the checks.

Remote connections use certificate-verified TLS. The existing CI-only loopback test option does not enable a local database fallback in the application. This guide does not run migrations against an owner's active application database or reset its ledger.

## Repeat the browser rehearsal

Open [the public evaluator rehearsal](https://proofpay-evaluation-lab.vercel.app/judge). Its canonical origin is `https://proofpay-evaluation-lab.vercel.app`; use that exact origin for API requests. It creates a random, signed two-hour guest session through **Open judge workspace**; no account, owner key, payment credential or model key is requested. Its server accepts only rehearsal actions. Owner sign-in and owner APIs are disabled there, and judge APIs are disabled on the private owner deployment.

Guest sessions have up to 100 mutation attempts and ten resets after the initial workspace. The deployment admits at most 60 new sessions per hour and 300 in total. A 429 limit response is an expected resource boundary; do not clear counters or rotate identities to bypass it. Reads and exports remain available within the session's valid lifetime. After expiry, begin a new session; the previous guest cookie no longer authorizes its records.

The private owner interface also supports rehearsal, but requires its dedicated owner sign-in. Do not publish that key. The [development guide](DEVELOPMENT.md#interactive-development-and-owner-sessions) documents local HTTPS and database setup for an operator-owned instance. Public guests do not have business settings or workspace history screens. Export guest evidence before resetting.

The public rehearsal starts with $300. For the same amounts in the private interface, use a dedicated test profile with a $300 default allowance before starting a fresh workspace. Existing workspaces retain their previous allowance even after the profile changes.

| Step | Action | Expected observation |
|---|---|---|
| Start | Choose **Open judge workspace** in the judge interface, or start a rehearsal in the private interface's Connections. | Two sample requests: $180 workflow review and $160 design review; $300 available. The mode is explicitly simulated. |
| Reserve | Open the workflow review and approve $180. | $120 available, $180 reserved and $0 paid. |
| Compete | Attempt to approve the $160 design review. | Approval is blocked by the allowance. The workflow reservation remains $180. |
| Create | Open the approved workflow review; choose **Create simulated order**. | The same purchase has a simulated order ID and is ready for simulated capture. |
| Lose response | Select **Drop the capture response**, then capture the simulated payment. | The outcome needs verification. $180 remains reserved; no second capture action is offered. |
| Reload | Choose **Reload page to check persistence**. | The same operation/order remains uncertain and reserved. |
| Recover | Choose **Check simulated outcome**. | The same purchase becomes confirmed; $120 available, $0 reserved, $180 paid. |
| Repeat lookup | Choose **Check the same outcome again**. | The capture ID and amounts remain unchanged. |
| Inspect | Open **Evidence**, select the **Purchase record** and expand **Inspect approved vs observed receipt**; use **Export all receipts** for JSON. | The source/mode remains rehearsal and simulated; IDs, approval binding and checked provider fields can be inspected. |
| Reset | In the public portal, choose **Start fresh demo → Confirm fresh demo**. The private owner interface uses **Reset simulated workspace**. | A new rehearsal is created. Earlier records are retained, not deleted or refunded. The private owner interface exposes Workspace history; the guest interface does not. |

If the execution window expires before capture dispatch, renew the unchanged owner approval before proceeding. Do not retry a dispatched capture. An uncertain sandbox purchase must be resolved in its own workspace; the normal owner flow refuses a reset that would hide held sandbox work.

The public portal has **Overview, Purchases, Approvals, Evidence, Controls, AI & backend and Evaluation lab**. Use **Continue workflow** to resume the next permitted action; Overview's uncertainty shortcut opens the same unresolved purchase. Lab steps use saved operation events and explicitly limited browser observations. To record the reload comparison, use **Reload page to check persistence** while the outcome is uncertain. A page reload is not a server-process restart; a repeated-check comparison is not an external request counter or independent attestation. The local restart test above supplies separate process-level evidence.

For private-owner business settings, save a test identity, create a workspace, then edit the defaults. The old workspace must keep its original name, department, budget and approval records. A stale profile version must return a conflict instead of overwriting a newer save. Two separate browser profiles in the public guest deployment must receive different workspace IDs and must not be able to read or change each other's operation IDs or receipts. Separate tabs in the same browser profile normally share the same cookie and session; they are not an isolation test.

## Verify an actual CSV download

CSV export happens in the browser through a Blob and a download anchor. There is no CSV API route to call. The CSV unit tests exercise the generator and parse its output, but they do not prove that a browser saved those bytes.

The responsive fixture deliberately intercepts external navigation and downloads, including detached anchors. Its build or visual inspection cannot close this check. Use the actual private owner UI in an authorized rehearsal session; no payment or model request is needed to export already-loaded records. The public judge interface exports JSON evidence only, so it does not establish the private interface's CSV download behavior.

1. In a dedicated test profile, use a harmless formula-shaped name such as `=ProofPay export check` and a department containing a comma. Start the $300 rehearsal and complete the browser flow above through recovery, before reset.
2. In Purchases, select a filter that hides one of the two requests. Choose **Export CSV**. Save the resulting file and retain its filename, byte size and SHA-256 alongside the source/deployment revision.
3. Parse the saved file with a CSV reader. It must contain 24 columns and both purchases, including the hidden row. The workflow row must be `CONFIRMED`, the design row `BUDGET_BLOCKED`; the workspace ID must match the UI. Amounts must be `180.00` and `160.00`, the allowance `300.00`, and both mode fields `rehearsal`. The business name must have a leading apostrophe before `=`, and the comma must remain inside one department cell.
4. Open the file in the intended spreadsheet application if that compatibility matters. Confirm that the formula-shaped name is text. Passing a parser check alone is not certification for every spreadsheet application.

For the exact two-row walkthrough, this command checks the downloaded file without network access:

```sh
python3 - /absolute/path/to/downloaded-report.csv <<'PY'
import csv, hashlib, pathlib, sys

path = pathlib.Path(sys.argv[1])
raw = path.read_bytes()
with path.open(encoding='utf-8-sig', newline='') as stream:
    reader = csv.DictReader(stream)
    rows = list(reader)
    assert len(reader.fieldnames) == 24
assert len(rows) == 2
by_item = {row['catalogue_item']: row for row in rows}
assert set(by_item) == {'workflow-review', 'design-review'}
assert by_item['workflow-review']['status'] == 'CONFIRMED'
assert by_item['design-review']['status'] == 'BUDGET_BLOCKED'
assert by_item['workflow-review']['amount'] == '180.00'
assert by_item['design-review']['amount'] == '160.00'
assert by_item['workflow-review']['capture_id']
assert not by_item['design-review']['capture_id']
assert len({row['workspace_id'] for row in rows}) == 1
for row in rows:
    assert row['business_name'] == "'=ProofPay export check"
    assert ',' in row['department']
    assert row['workspace_allowance'] == '300.00'
    assert row['workspace_mode'] == row['provider_mode'] == 'rehearsal'
    assert row['proposal_source'] == 'rehearsal-seed'
print(f'PASS: {len(rows)} rows, 24 columns, {len(raw)} bytes')
print('SHA-256:', hashlib.sha256(raw).hexdigest())
PY
```

The command is an acceptance procedure, not a recorded browser-download result. This review did not download a file or run it against a real browser export. Keep that distinction when reporting completion. CSV is an application report, not an invoice or provider-authenticated receipt.

## Recorded live evidence is a separate result

The [configured live QA record](../evidence/configured-live-qa-2026-11-08.md) describes the already completed model-to-PayPal sandbox run. It uses virtual funds and the consumed reviewed model allowance. Re-running the no-key tests or the browser rehearsal does not create fresh live AI/PayPal evidence and must not be presented that way. Final Devpost submission remains a separate held action.
