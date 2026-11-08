# ProofPay video script

Updated 8 November 2026. The completed review cut is **163.521 seconds (2:43.521)**, including its opening and closing frames. It uses the exact **347-word narration** below, thirteen actual captured screens and an original illustrated presenter. Public YouTube URL: **pending publication and fresh-viewer verification**.

## Evidence and recording boundary

The video is an **edited walkthrough of actual captured application states**, not a continuous transaction recording. Its first part shows saved evidence from the [completed AI-to-PayPal sandbox run](../evidence/configured-live-qa-2026-11-08.md). Its second part shows a separately captured, fresh simulated rehearsal. These modes remain visibly labelled.

One genuine model-to-PayPal sandbox purchase succeeded. Vercel AI Gateway recorded `openai/gpt-4.1-mini`, HTTP 200, 242 input/48 output tokens and a displayed USD0.0002 request cost. Its proposal continued through owner approval, native buyer approval, capture with deliberate application response loss and original-order reconciliation. No personal OpenAI key or personal credits were used. The reviewed free-credit grant's one model attempt is consumed; filming does not authorize another model call or payment.

No continuous recording of that original external transaction exists. The captured saved record is labelled **Saved evidence — completed sandbox run**. The rehearsal is labelled **Fresh rehearsal — deterministic proposals, simulated provider**. Do not describe its simulated outcomes as additional live PayPal results.

## Exact recorded narration

This block contains only the spoken words. Scene directions and production notes are separate. The final offline narration uses these nine paragraphs.

```text
ProofPay helps an owner approve purchases, share an allowance across requests, and understand what happened when a payment response disappears. Our example is a small studio with three hundred dollars for outside review work.

This first view shows saved evidence from a completed run, not a replay. A real model, GPT four point one mini through Vercel AI Gateway, proposed the one hundred eighty dollar purchase. The owner approved it, and the sandbox buyer separately approved on PayPal. No personal OpenAI credits were used.

During that run, the application deliberately dropped the capture response. After a browser reload, one hundred eighty dollars remained reserved. A lookup of the original PayPal order confirmed the matching completed capture. Another check preserved the same capture and totals: one hundred eighty paid, zero reserved, and one hundred twenty available. These are virtual sandbox funds.

Now we switch to a fresh, separately labelled rehearsal. Its proposals are deterministic, and its provider is simulated. It makes no model or PayPal calls.

Approving the one hundred eighty dollar request reserves its allowance. The competing one hundred sixty dollar request is blocked because only one hundred twenty remains. An alternative would require a new proposal and approval.

Here, we create a simulated order and deliberately drop its capture response. The purchase needs verification, and the reservation stays held. Reloading preserves that state. Checking the original simulated order records the payment. Checking again leaves the totals unchanged.

The receipt inspector compares stored seller, amount, currency and payment references. It also shows missing information. These are unsigned application records. They do not independently prove the historical approval version or catalogue item. Opening the inspector reads stored evidence; it does not make a new payment.

The reviewed build passed two hundred ten local checks, with separate PostgreSQL and hosted workflow evidence. Tests have limits, and one sandbox purchase is not production readiness.

ProofPay currently covers one controlled seller, US dollars and a workspace allowance. The opportunity is a practical purchase desk where a business decision stays connected to its payment outcome. Source and setup instructions accompany the project.
```

## Final scene map — not narration

The render is 1920×1080 at 30 fps. Times below are rounded to the nearest tenth of a second, except the final file duration. Actual captured screens are held and edited within each scene; this table does not imply a continuous click recording.

| Final time | Paragraph | Captured content and evidence boundary |
|---|---:|---|
| 0:00–0:15.4 | 1 | Product overview: **ProofPay Purchase Desk**, the $300 studio example and readable purchase information. |
| 0:15.4–0:38.9 | 2 | Saved completed sandbox operation `5a01eccf-b306-4c26-9417-2da6b86a577e`, its AI proposal source and sanitized model/run evidence. Persistent label: **Saved evidence — completed sandbox run**. This is not footage of the original buyer approval. |
| 0:38.9–1:05.1 | 3 | Saved response-loss/reconciliation evidence and the completed receipt: order `9RM583829W779660E`, capture `1PN07056KE8415453`, $180 paid/$0 reserved/$120 available. Historical held amounts come from the run record. Caption identifies application-injected response loss and virtual funds. |
| 1:05.1–1:16.6 | 4 | Explicit transition to the separately captured **Fresh rehearsal — deterministic proposals, simulated provider**. |
| 1:16.6–1:31.5 | 5 | Actual rehearsal approval/reservation and competing-request rejection states: $180 reserved, $120 available; $160 request over allowance. An alternative is described conditionally, not claimed to have executed in this cut. |
| 1:31.5–1:50.6 | 6 | Captured states from simulated order creation, dropped capture response, retained reservation after reload, original-order check and unchanged repeated outcome. Keep the simulated mode visible. |
| 1:50.6–2:13.4 | 7 | The receipt inspector's stored seller/amount/currency/reference comparisons and its historical approval-version/catalogue-item limitation. Inspection is not a new provider call. |
| 2:13.4–2:26.2 | 8 | Current **210 local checks**, with separate PostgreSQL and hosted-workflow evidence. These counts are checks, not live transactions. |
| 2:26.2–2:43.521 | 9 | Product scope and source/setup reference. The public judge workspace is available separately at the canonical URL below; do not add a URL or closing card beyond the measured file duration without rerendering and rechecking. |

## Presenter, sound and source

The presenter is original illustrated artwork, labelled **Synthetic presenter**. It does not depict Rama, a teammate, the PayPal CEO or any PayPal employee. Its own side column keeps it clear of product amounts, statuses and controls. The header states **Edited actual UI states · Synthetic narration**.

Speech was generated locally with Flite's SLT voice. Mouth shapes follow actual synthesizer phoneme segments; the extracted source audio was checked byte-for-byte against each original narration waveform before processed timing was applied. This is simple illustrated animation, not a voice clone or photorealistic person. No HeyGen generation, hosted avatar service, subscription or generation credits were used. Original artwork and pipeline source are included in the separate source bundle with dependency notices.

The final file is `proofpay-narrated-review-cut.mp4`, SHA-256 `a5d5b982281fb36618463b393e4b36acdc8237e40ca8684de042ec2eac00b1a2`. Validation recorded a successful full decode, 1920×1080 H.264 video, mono AAC audio, a −3.446 dBFS decoded audio peak and no full-scale samples. All 35 subtitle entries fit within the duration. Caption timing is estimated from speech lengths and punctuation, not forced-aligned; these signal checks do not establish a complete human listening review.

## Access and test context

[Open the public judge workspace](https://proofpay-evaluation-lab.vercel.app), choose **Try the demo**, then use **Purchase desk**, **AI & backend** or **Evaluation lab**. No login is required. Each visitor receives an isolated, temporary rehearsal session. AI & backend exposes read-only configuration/history. The judge path uses deterministic proposals and a simulated provider; it never calls the real model or PayPal. The completed external run remains separate from each judge's rehearsal.

Current evidence comprises 210 passing local checks, nine deployed PostgreSQL checks, six observed hosted UI checks and [21 independent HTTPS checks using two guest sessions](../evidence/judge-hosted-qa-2026-11-08.json). Nine responsive checks covered the three judge modules at 360, 768 and 1280 pixels, with no horizontal overflow, 16px main text and no captured application warnings/errors. These are distinct verification scopes.

The independent HTTPS review downloaded one actual guest receipt and passed the offline consistency verifier. That result does not verify provider authenticity or the owner's previously timed-out browser CSV/Blob download. See [repeatable testing](REPEATABLE_TESTING.md) for session limits and instructions.

## Publication checkpoint

- Public judge URL: **https://proofpay-evaluation-lab.vercel.app** — verified no-login isolated rehearsal.
- [Public source and setup](https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay).
- Public YouTube URL: **pending**. A rendered file is not evidence of publication. Add the actual URL only after public playback is verified.
- **Final Devpost Submit remains held.** Video publication and draft updates are authorized separately.

Before publication, complete the remaining items in [RECORDING_CHECKLIST.md](RECORDING_CHECKLIST.md). Keep owner sign-in, payment credentials, cookies, buyer details and account screens out of the public material. Do not imply another live model run, production readiness, signed receipts or independently measured aggregate provider request counts.

The [official requirements](https://paypalaihackathon.devpost.com/) and [rules](https://paypalaihackathon.devpost.com/rules), reviewed 8 November 2026, require publicly visible YouTube footage under three minutes. The measured cut meets the duration requirement; its public URL remains pending.
