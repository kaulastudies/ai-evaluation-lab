# ProofPay recording and publication checklist

Updated 8 November 2026. The current rendered file is **163.521 seconds (2:43.521)**, using the **347-word narration** in [DEMO_SCRIPT.md](DEMO_SCRIPT.md). Completed items below are supported by the current release evidence. Unchecked items remain release checks; a local file does not establish public publication.

## Evidence and judge access

- [x] One actual AI-to-PayPal sandbox run is recorded in [configured hosted QA](../evidence/configured-live-qa-2026-11-08.md): operation `5a01eccf-b306-4c26-9417-2da6b86a577e`, order `9RM583829W779660E`, capture `1PN07056KE8415453`, $180 paid/$0 reserved/$120 available after reconciliation.
- [x] The video separates **Saved evidence — completed sandbox run** from **Fresh rehearsal — deterministic proposals, simulated provider**. It is an edited walkthrough of actual captured application states, not a continuous recording of the original transaction.
- [x] Public judge access is verified at **https://proofpay-evaluation-lab.vercel.app**. **Try the demo** creates an isolated temporary session without login. Purchase desk, read-only AI & backend and Evaluation lab are available.
- [x] The judge route makes no real AI or PayPal calls. Six hosted UI checks and [21 independent HTTPS checks across two guests](../evidence/judge-hosted-qa-2026-11-08.json) cover the reviewed flow and isolation boundaries.
- [x] The release has 210 passing local checks and nine deployed PostgreSQL checks. Nine responsive views cover the three judge modules at 360/768/1280 pixels, with no horizontal overflow, 16px main text and no captured application warnings/errors.
- [x] One actual guest receipt downloaded over HTTPS passed the offline consistency verifier. This is not a browser Blob/CSV-download check or a provider attestation; the earlier owner browser download remains unverified.

## Preserve the real result

- [ ] During final public-asset review, confirm the saved-run labels and past-tense narration remain visible and accurate. No continuous original buyer-approval or capture recording exists.
- [ ] Keep the consumed free-credit grant unchanged. Do not request another model proposal, reset its attempt limit, recapture the confirmed order or stage another PayPal purchase for filming.
- [ ] Keep credentials, owner sign-in, cookies, personal buyer/funding details and unrelated account screens out of the final public material. Use sanitized run metadata for the model evidence.
- [ ] Preserve the distinction between the actual external run and each simulated operation. Do not splice different operations to suggest continuous recovery or independently measured provider request counts.

## Presenter, audio and render

- [x] The presenter is original illustrated artwork, labelled **Synthetic presenter**, with offline Flite SLT speech. It is not Rama, a teammate or a PayPal representative; no voice clone or HeyGen generation was used.
- [x] Mouth animation uses actual Flite phoneme segments. Extracted source audio matched the original narration waveforms byte-for-byte before timing adjustment.
- [x] The layout reserves a separate presenter column and labels the footage **Edited actual UI states · Synthetic narration**. Product screens remain the main visual.
- [x] `proofpay-narrated-review-cut.mp4` measures 163.521 seconds: 1920×1080, 30 fps, H.264/AAC. Full decode passed; audio peaked at −3.446 dBFS with no full-scale samples. All 35 subtitle entries fit within the duration.
- [x] The narration says **two hundred ten local checks**. Its exact approved text is in [DEMO_SCRIPT.md](DEMO_SCRIPT.md).
- [ ] Review the entire final video at normal playback speed for intelligibility, caption synchronization, labels, amounts and presenter placement. Subtitle timing is estimated, not forced-aligned; mechanical checks do not replace listening review.
- [ ] If any frame, title or outro changes, rerender and remeasure. Keep the whole delivered file below three minutes; the current cut also meets the stricter 2:50 production target.

## Factual review

- [ ] Preserve “virtual sandbox funds,” application-injected response loss and browser reload. Do not imply a hosted backend restart was tested.
- [ ] Describe receipts as unsigned application records. An offline consistency pass does not verify provider authenticity, historical authority, event completeness or fulfillment.
- [ ] Keep the historical approval-version/catalogue-item limits visible. Opening the receipt inspector reads stored evidence and is not a new payment or provider lookup.
- [ ] Keep local, database, hosted UI and HTTPS checks separate. One observed external sandbox purchase does not establish production readiness or general exactly-once behavior.
- [ ] Confirm the source link, public judge link and final video facts match the existing Devpost draft. No customer, revenue, prize or valuation claim is supported.

## Publish and update the draft

- [ ] Publish the final video to YouTube as **public** and verify playback at its exact URL in a fresh viewer session. **Public YouTube URL: pending.**
- [x] Save and reopen Devpost Project Details: the clean 6,410-character story, six implemented technology tags, canonical judge URL and GitHub source link matched. The draft was saved without a video URL.
- [ ] Add only the verified public YouTube URL to the existing Devpost draft after upload. The required video field remains empty. Keep the no-login judge path labelled simulated and the actual external run separately identified.
- [ ] Recheck the published video duration and public accessibility after upload; the local render result alone does not establish either public condition.
- [ ] **Do not click final Devpost Submit.** Nithya's team acceptance is already confirmed and is separate from application access.

Sources: [official submission requirements](https://paypalaihackathon.devpost.com/) and [rules](https://paypalaihackathon.devpost.com/rules), reviewed 8 November 2026. Public YouTube footage under three minutes and runnable judge access are separate requirements.
