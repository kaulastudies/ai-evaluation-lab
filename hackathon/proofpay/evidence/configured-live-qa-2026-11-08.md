# Configured hosted QA — 8 November 2026

This record summarizes the release owner's observed Vercel, AI Gateway and application/browser results. It contains sanitized identifiers, not credentials or raw account/network logs. The runtime was unchanged; this checkpoint configured the existing deployment and exercised its hosted workflow.

## Deployment and configuration

| Item | Recorded result |
|---|---|
| Public source at this run | `d17ec6c93442d065c17870faad0708447432cdaa`; runtime unchanged from the reviewed business increment. |
| Canonical application | https://proofpay-purchase-desk.vercel.app |
| Production | `dpl_9Yn4n3TeamFJHcAnKj63cdyQn7V3` — READY. |
| Preview | `dpl_GMKP1hHzjNrAmeMxN7M85obNcQF6` — READY. |
| Database/build gates | Both builds passed eight real PostgreSQL checks and migrations. Filtered build-log review found no warnings/errors. |
| Owner configuration | `OWNER_ID` saved as a nonsecret value; `OWNER_PASSWORD_HASH` and `SESSION_SECRET` saved as sensitive values in Production and Preview. |
| PayPal configuration | `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` and `PAYPAL_MERCHANT_ID` saved as sensitive values in Production and Preview. No values are included here. |
| Hosted owner access | Owner sign-in succeeded. Business profile persisted as **AI Evaluation Lab / ProofPay sandbox QA / USD300 default workspace allowance**. |

The [199-test local checkpoint](business-portal-checks-2026-11-08.json), passing types/lint/builds and zero-finding full dependency audit remain the existing source evidence. No new source-test run or audit is claimed here. The [preceding production record](business-portal-release-2026-11-08.json) remains a historical setup-pending browser checkpoint; it is not rewritten by this run.

## Hosted rehearsal

The authenticated rehearsal used a simulated provider and deterministic sample proposals, not AI or PayPal.

| Action | Observed state |
|---|---|
| Approve USD180; create simulated order; capture with response deliberately dropped | USD180 reserved, USD120 available, USD0 paid. |
| Reload the browser | Same unresolved purchase and held amounts persisted. |
| Reconcile the original simulated order | USD180 paid, USD0 reserved, USD120 available. |
| Check the outcome again | Same outcome and totals; no second accounting transition observed. |
| Attempt the competing USD160 approval | Blocked by the remaining USD120 allowance. |
| Approve a separate USD90 cheaper alternative, then cancel before dispatch | Reservation released; the paid USD180 purchase remained intact. |

This establishes the stated hosted rehearsal and browser-reload behavior. It is not a hosted backend-process restart test.

## Authenticated interface checks

All eight signed-in sections were opened at actual viewport widths of 360, 768 and 1280 pixels. All 24 heading checks passed; no page had horizontal document overflow or the earlier setup-pending message. The mobile body font was 15px and navigation targets were 48px high. The viewport override was reset afterwards. The captured warning/error console collection was empty. The [configured Controls screenshot](configured-controls-2026-11-08.jpg) shows the authenticated control panel without credentials or transaction identifiers.

Workspace history listed the original rehearsal and the genuine sandbox workspace separately. Opening the rehearsal preserved its three operations and USD180 simulated payment; switching back preserved the sandbox capture and USD120 available / USD0 reserved / USD180 paid. No new provider transaction was initiated by selection. Sign-out cleared the private records; reloading required the owner key again. Signing back in restored the same sandbox workspace and totals.

## Actual runtime AI

Before the call, the release owner observed **$4.93 of Vercel AI Gateway free credit**, no BYOK provider keys and disabled automatic reload. The Gateway request record identifies project authentication for `proofpay-purchase-desk`.

| Gateway field | Observed value |
|---|---|
| Request time | `2026-11-08T11:26:14Z` |
| Status | HTTP 200 |
| Model | `openai/gpt-4.1-mini` |
| Provider | OpenAI through Vercel AI Gateway |
| Input / output tokens | 242 / 48 |
| Displayed request cost | USD0.0002 |
| Displayed duration | 1.18 seconds |

This was an actual runtime proposal used in the sandbox purchase below, not a seeded diagnostic. It used the reviewed Vercel free-credit route; no personal OpenAI key or personal OpenAI credits were used. The cost is the displayed request record, not a final invoice or a post-run balance reconciliation.

**The reviewed grant's one bounded attempt has been consumed.** Do not reset it or make another model request to repeat this demonstration. Preserve the existing proposal and purchase evidence.

## Combined AI-to-PayPal sandbox purchase

| Identity | Recorded value |
|---|---|
| Operation | `5a01eccf-b306-4c26-9417-2da6b86a577e` |
| PayPal sandbox order | `9RM583829W779660E` |
| PayPal sandbox capture | `1PN07056KE8415453` |
| Purchase amount | USD180, virtual sandbox funds |
| Verification record | `459207d2-e886-495a-a778-a535ecdad756` |
| Verification source | `paypal-sandbox-orders-get` |

The hosted sequence was a genuine model proposal, explicit owner approval, order creation, native sandbox buyer **Complete Purchase**, capture with the application deliberately dropping its response, and original-order reconciliation.

After the dropped capture response, the browser refresh retained the unresolved operation with **USD180 held / USD120 available / USD0 paid**. A GET of the original PayPal order then reconciled the operation to `CONFIRMED`. The recorded order and capture were `COMPLETED`, `final_capture` was true, and the checked amount, currency, seller and operation/order/capture references matched. The resulting accounting was **USD180 paid / USD0 reserved / USD120 available**.

Repeating the outcome check retained the same capture and totals. No second capture action was observed in this sequence; aggregate external request counts were not independently measured. This is a sandbox result with virtual funds, not production settlement, service fulfillment or a general exactly-once guarantee.

## Limits and remaining gates

- The receipt's stored verification schema still lacks the historical approval version and catalogue SKU. Matching current fields does not independently establish those historical values. The receipt is unsigned application evidence, not a signed PayPal/model attestation.
- The browser CSV download collection timed out. Exported browser file bytes were **not verified**; do not infer them from an export action or success indication. No offline-verifier result for a newly downloaded receipt is claimed here.
- Successful owner access and the persisted profile do not establish every authorization/session failure path, multi-user access, every history/concurrency action or every possible responsive state. Local regression evidence has its own scope.
- Independent judge access and the required public YouTube demonstration remain unfinished. The one-attempt grant does not supply unrestricted judge inference.
- Nithya's Devpost team acceptance was previously confirmed. Team membership does not grant an application role.
- **Final Devpost Submit remains held.** No submission or external message is implied by this QA record.
