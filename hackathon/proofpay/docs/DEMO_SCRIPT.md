# ProofPay video script

Updated 8 November 2026 from source checkpoint `c2c5848` and the [configured hosted QA record](../evidence/configured-live-qa-2026-11-08.md). The actual run used public source `d17ec6c9`; the runtime was unchanged at this documentation checkpoint.

**Deliverable:** one narrated video with a generic stock AI presenter in a corner, edited to **2:50 maximum**, including all titles and closing frames. The exact HeyGen narration below is **348 words**. Start around 130 words per minute, render a voice preview, and measure the result; the estimate is not a verified video duration.

## Evidence and recording boundary

One genuine model-to-PayPal sandbox purchase succeeded. Vercel AI Gateway recorded `openai/gpt-4.1-mini`, HTTP 200, 242 input/48 output tokens and a displayed USD0.0002 request cost. Its proposal continued into native buyer approval, capture with deliberate response loss and original-order reconciliation. No personal OpenAI key or personal credits were used.

**No continuous original transaction recording exists.** Film the persisted completed purchase, its stored receipt and the sanitized run record. Label these frames **“Saved evidence — completed sandbox run”**. Describe past actions in the past tense. Do not fabricate a checkout replay, recreate the buyer-approval screen or splice another operation into this history.

The reviewed grant's one model attempt is consumed. Do not reset it, request another model proposal or make another sandbox payment for filming. Demonstrate interactive approval, budget blocking and recovery only in a **fresh, separately labelled rehearsal**, which makes no model or PayPal calls. The main video uses those two evidence layers, with an explicit transition.

## Exact narration for HeyGen

Copy only the following block into HeyGen. Scene labels, timestamps and production notes belong outside the narration field.

```text
ProofPay helps an owner approve purchases, share an allowance across requests, and understand what happened when a payment response disappears. Our example is a small studio with three hundred dollars for outside review work.

This first view shows saved evidence from a completed run, not a replay. A real model, GPT four point one mini through Vercel AI Gateway, proposed the one hundred eighty dollar purchase. The owner approved it, and the sandbox buyer separately approved on PayPal. No personal OpenAI credits were used.

During that run, the application deliberately dropped the capture response. After a browser reload, one hundred eighty dollars remained reserved. A lookup of the original PayPal order confirmed the matching completed capture. Another check preserved the same capture and totals: one hundred eighty paid, zero reserved, and one hundred twenty available. These are virtual sandbox funds.

Now we switch to a fresh, separately labelled rehearsal. Its proposals are deterministic, and its provider is simulated. It makes no model or PayPal calls.

Approving the one hundred eighty dollar request reserves its allowance. The competing one hundred sixty dollar request is blocked because only one hundred twenty remains. An alternative would require a new proposal and approval.

Here, we create a simulated order and deliberately drop its capture response. The purchase needs verification, and the reservation stays held. Reloading preserves that state. Checking the original simulated order records the payment. Checking again leaves the totals unchanged.

The receipt inspector compares stored seller, amount, currency and payment references. It also shows missing information. These are unsigned application records. They do not independently prove the historical approval version or catalogue item. Opening the inspector reads stored evidence; it does not make a new payment.

The reviewed build passed one hundred ninety nine local checks, with separate PostgreSQL and hosted workflow evidence. Tests have limits, and one sandbox purchase is not production readiness.

ProofPay currently covers one controlled seller, US dollars and a workspace allowance. The opportunity is a practical purchase desk where a business decision stays connected to its payment outcome. Source and setup instructions accompany the project.
```

## Scene directions — not narration

Use the actual application, not the read-only visual-test harness. Target 1920×1080. Reserve a small corner for a licensed generic stock AI presenter; use a normal supplied voice. The presenter must not resemble or claim to be Rama, the PayPal CEO, a teammate or a PayPal employee. Add a small **“AI presenter”** label. Never cover the mode, amounts, status, receipt fields or action buttons.

| Final time | Narration paragraph | Screen capture and captions |
|---|---:|---|
| 0:00–0:16 | 1 | Product overview and a simple title: **ProofPay Purchase Desk**. Keep the business/allowance example readable. The avatar can introduce the product without an extra title-card delay. |
| 0:16–0:40 | 2 | Open the existing completed sandbox operation `5a01eccf-b306-4c26-9417-2da6b86a577e`. Show **AI model** as proposal source, USD180 and stored approval/payment identifiers. Briefly show the sanitized Gateway row from the QA record, including model and HTTP200. Persistent caption: **Saved evidence — completed sandbox run**. No new model call or approval action. |
| 0:40–1:07 | 3 | Show saved response-loss/reconciliation events and the completed receipt. Where historical held amounts are needed, show the labelled QA record, not a recreated unresolved app state. Show order `9RM583829W779660E`, capture `1PN07056KE8415453` and current USD180 paid/USD0 reserved/USD120 available. Caption: **Application-injected response loss · virtual funds**. No new provider request is needed. |
| 1:07–1:20 | 4 | Visible transition card: **Fresh rehearsal — deterministic proposals, simulated provider**. Start a new isolated $300 rehearsal, retaining the completed sandbox history. Keep the rehearsal banner visible for the rest of the interactive sequence. |
| 1:20–1:37 | 5 | Open Workflow review; choose **Approve & reserve $180.00**. Show $180 reserved/$120 available. Attempt the $160 Design review approval; hold on **Over allowance**. Do not create or approve an alternative in this short take. |
| 1:37–1:57 | 6 | Reopen the $180 rehearsal operation. Choose **Create simulated order**, select **Drop the capture response**, then **Capture simulated payment**. Show unresolved/$180 reserved, reload, reopen the same operation, choose **Check simulated outcome**, then **Check outcome again**. Show stable $180 paid/$120 available. Capture the full take; shorten loading waits with **“Wait shortened; same simulated operation”** if needed. |
| 1:57–2:20 | 7 | Expand **Inspect approved vs observed receipt** for the rehearsal purchase. Keep its simulated source visible. Show seller/amount/currency/reference comparisons and the historical approval-version/catalogue-item limitation. Opening the inspector reads stored evidence; do not substitute a new PayPal lookup. |
| 2:20–2:33 | 8 | Show the dated **199/199 local checks** record and a brief **8 real PostgreSQL checks · separate hosted QA** caption. Use the current evidence file, not a fabricated terminal success screen. Do not display a general security certificate or guarantee. |
| 2:33–2:50 | 9 | Return to the product and end with the existing public source/setup reference. If the independent judge rehearsal is verified before rendering, add its actual URL as a screen caption. Otherwise show **Judge rehearsal access: pending** in the preparation cut; do not imply it is available. No invented video URL or extra closing seconds. |

The source and setup reference may use [the public ProofPay branch](https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay). The canonical [Vercel application](https://proofpay-purchase-desk.vercel.app) currently requires owner access. A public URL alone does not establish independent judge access.

## Production notes

- Record the completed evidence before starting a fresh rehearsal. Workspace history must retain the sandbox operation. Do not reset its grant or mutate its confirmed purchase.
- The isolated public judge rehearsal is under design. Its URL, independence from owner records and fresh-session behavior remain pending until the release owner supplies verified evidence. Until then, any rehearsal footage uses the actual authenticated rehearsal and is labelled accordingly.
- Use readable app footage as the main visual. Keep the avatar small and steady; no cloned voice, first-person founder introduction or PayPal branding suggesting endorsement.
- Keep owner sign-in, passwords, session cookies, payment credentials, buyer identity/funding details and developer dashboards offscreen. Use sanitized QA metadata instead of raw Gateway/account screens.
- Record narration separately from desktop audio. Include accurate English captions. Cut waiting time, not a failure or a change of operation. Do not use an export-success toast as proof of downloaded file contents.
- The model/capture evidence is from the completed run. The fresh rehearsal's outcomes must be observed in its own take. If a rehearsal step fails, investigate and record a new clearly identified rehearsal rather than borrowing a successful result.
- Measure the final rendered file and leave the title/end card inside the 2:50 budget. Review the avatar, captions, mode labels and numbers at normal playback speed.

## Publication checkpoint

Public YouTube URL: **pending — no recording or publication is established by this document**. Independent judge rehearsal URL: **pending**. See [RECORDING_CHECKLIST.md](RECORDING_CHECKLIST.md).

The [official requirements](https://paypalaihackathon.devpost.com/) and [rules](https://paypalaihackathon.devpost.com/rules), reviewed 8 November 2026, require publicly visible YouTube footage under three minutes. The owner authorized video publication and draft updates; **final Devpost Submit remains held**.
