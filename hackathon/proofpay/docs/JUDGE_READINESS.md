# ProofPay judge readiness

Updated **8 November 2026**, reviewing public runtime **`cfd1d007`** and local source checkpoint **`26893ed6`**. This is an internal assessment, not an organizer decision or prize prediction. **Final Devpost Submit remains held.**

ProofPay's strongest evidence is one completed model-to-PayPal sandbox purchase that retained its allowance through a deliberately missing capture response, then recovered the matching original outcome. The new seven-section judge portal makes that approval, allowance and recovery workflow easier to inspect. Its local source checkpoint passed **210 tests, TypeScript, full lint and build**. The current deployment passed **nine real PostgreSQL checks without skips**, migrations and build. The expanded browser workflow completed all six observations, and all seven views have responsive evidence.

The earlier 163.521-second Flite/illustrated-presenter video was rejected and has not been published. It is not a release candidate. The replacement V2 is frozen at **141.354362 seconds (2:21.354)**, with **312 narration words, 43 captions and 29 timed shots** of actual captured application states. It uses local Kokoro neural speech and no avatar. Full decode passed; decoded audio peaked at −1.969 dBFS with zero clipped samples. Sampled visual review passed. No independent listening or forced-alignment result is claimed. The [V2 film is public on YouTube](https://youtu.be/D4UXBT-FhcE). Studio confirmed Published/Public on 8 November, and the watch page played with a displayed duration of 2:21. All 43 burned-in captions are present. The exact native transcript was saved for automatic timing; public selectable captions were unavailable at the first watch-page check and remain processing. Native-caption timing QA is not claimed.

## Current product and evidence

A small agency has a $300 workspace allowance. Approving a $180 request reserves that allowance and blocks a competing $160 request. If a payment response disappears, the amount remains reserved. Recovery checks the original order before recording its completed capture. The receipt keeps the purchase decision and observed outcome together.

The catalogue is synthetic: Workflow review ($180), Design review ($160) and Starter review ($90). No paid service is delivered. Scope is one controlled seller, USD and a workspace allowance, not an account-wide PayPal budget.

The [completed external run](../evidence/configured-live-qa-2026-11-08.md) used `openai/gpt-4.1-mini` through Vercel AI Gateway, owner approval, native PayPal sandbox buyer approval and a $180 virtual purchase. The application deliberately dropped the capture response. Browser reload retained $180 reserved/$120 available/$0 paid. A GET of the original order confirmed the matching completed final capture; repeated lookup retained the same capture and totals. Operation `5a01eccf-b306-4c26-9417-2da6b86a577e`, order `9RM583829W779660E` and capture `1PN07056KE8415453` identify that same run.

The reviewed free-credit grant's one model attempt is consumed. Do not reset or retry it for filming. No personal OpenAI key or credits were used. This is one genuine combined sandbox journey, not a fresh model call in every judge session, a production settlement or independently measured aggregate provider-request evidence.

## Seven-section judge portal

Canonical origin: **https://proofpay-evaluation-lab.vercel.app**. The expanded portal's [fresh browser review](../evidence/judge-portal-browser-qa-2026-11-08.json) passed on `cfd1d007`, deployment `dpl_7Vyism59UzSpeNhD2ooWfXnhuKXB`. Earlier anonymous HTTP and two-guest isolation checks remain separately dated evidence; the current review is connected-browser execution, not incognito automation.

The fresh operation `47212f1a-84ee-449a-96a6-cdc2b475481d` reserved $180, blocked the competing $160 request, retained the unresolved $180 through reload, then confirmed the original simulated order. Rechecking retained capture `REH-CAP-f98db68a-6803-439e-ae62-677045a412ed` and $120 available/$0 reserved/$180 paid. Overview selected that same unresolved operation, Evidence inspected its matching receipt and Evaluation lab showed **6/6 observed**. The captured application console was empty.

All seven views were measured at 360, 768 and 1280 pixels: **21 responsive views** without horizontal overflow, with 16px main text. These measurements belong to source `26893ed6`; the subsequent `cfd1d007` change adjusts the preferred fresh workflow selection and leaves layout unchanged. These 21 layout checks must not be confused with the earlier 21 HTTPS checks.

| Section | Purpose in the new interface |
|---|---|
| Overview | Available, reserved and paid totals, unresolved work and the next action. |
| Purchases | Requests and their current payment states. |
| Approvals | Review the exact purchase and reserve its allowance before dispatch. |
| Evidence | Select a purchase, inspect approved versus observed fields and export application receipts. |
| Controls | Inspect the scope and rules used by the rehearsal. |
| AI & backend | Read-only simulated configuration and the recorded historical model/PayPal route. |
| Evaluation lab | Six current-session observations from saved events and limited browser comparisons. |

The entry action is **Open judge workspace**. **Continue workflow** resumes the current request; **Start fresh demo → Confirm fresh demo** creates another rehearsal. A signed two-hour guest session controls an isolated $300 workspace, without account or payment credentials. The backend uses deterministic proposals and a simulated provider with the application's approval, reservation and recovery logic. It constructs no live model/provider client and cannot consume the owner run's grant. Owner APIs and sign-in are disabled on the judge deployment.

A guest can approve, cancel before dispatch, renew eligible expired approval, create/capture a simulated order, check the original outcome and inspect/export receipts. The established backend limits are 100 mutations and 10 resets per session, plus 60 new sessions per hour and 300 total for the deployment. This is bounded free access. [Repeatable local checks](REPEATABLE_TESTING.md) remain a separate fallback; do not bypass limits or call access unlimited.

Evaluation lab's six observations are not six live payments or an independent audit. “Not yet observed” means that evidence has not been recorded in that session. Browser reload is not a hosted backend restart; repeated-check comparison is not a network request counter.

## Official requirements and dates

The [event requirements](https://paypalaihackathon.devpost.com/) require meaningful use of PayPal and AI. [Rules sections 4 and 6](https://paypalaihackathon.devpost.com/rules) distinguish entry requirements, baseline viability and five equally weighted judging criteria. The [resources](https://paypalaihackathon.devpost.com/resources) list REST alongside the Agent Toolkit and MCP; REST is permitted and neither Toolkit nor MCP is mandatory. The actual Gateway proposal is runtime AI evidence; a toolkit installation alone would not establish execution.

| Event | Verified timing |
|---|---|
| Submission | 1 October 2026, 09:15 Pacific, through **12 November 2026, 12:00 PST**: **20:00 UTC / 13 November, 01:30 IST**. |
| Judging | 1 December, 14:00 PST, through 15 December, 08:00 PST. |
| Announcement | 21 December 2026. Rules say approximately 14:00 Pacific; the schedule says 09:00 PST. The announcement time remains inconsistent. |

Sources: [schedule](https://paypalaihackathon.devpost.com/details/dates) and [rules section 1](https://paypalaihackathon.devpost.com/rules), reviewed 8 November 2026. The submission deadline agrees across both pages.

## Entry requirements: evidence and remaining gates

| Official requirement | Evidence | Current gate |
|---|---|---|
| PayPal sandbox and meaningful AI | Actual GPT-4.1-mini proposal, owner/native buyer approvals, $180 capture and original-order recovery in one hosted journey. | **Verified once.** Preserve its records; the public simulation is separate. Organizer acceptance is not established by our assessment. |
| Working, reproducible demo | Source, migrations, [setup](../README.md), completed owner run and current seven-section public rehearsal. Local checks, browser workflow and responsive review passed. | **Current rehearsal verified.** Retain the same-operation evidence and its distinction from the now-published video's saved external-run segment. The consumed model grant does not permit another external run. |
| Public source, open-source license and run instructions | [Project branch](https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay), [Apache-2.0 project license](../LICENSE), lockfile, setup and retained starter notices. | Check final anonymous source access and revision consistency. Source `26893ed6` is the local checkpoint; current runtime `cfd1d007` passed both CI workflows. |
| Functionality description and AI-tool identification | [Story](DEVPOST_STORY.md), [judge guide](JUDGES.md), [architecture](ARCHITECTURE.md), actual model identifier and Gateway route. | Keep product AI separate from coding assistance and the simulated judge path. |
| Public YouTube demonstration under three minutes | [Published V2](https://youtu.be/D4UXBT-FhcE): Studio confirmed Published/Public on 8 November; watch-page playback displayed 2:21. Frozen file duration is 141.354362 seconds. | **Publication verified.** Native selectable captions are still processing; 43 burned-in captions are already present. No independent listening or forced-alignment claim. The Devpost video URL was saved and reopened; the embedded player showed the correct title. |
| Free judge testing through judging | Separate guest database/session, no provider credentials, bounded rehearsal actions and repeatable local tests. | Public entry and the expanded workflow passed their stated checks. Monitor availability through judging; do not promise unlimited sessions. |
| Event-period creation or substantial update | Git history adds ProofPay during November 2026 in the existing AI Evaluation Lab repository. | Identify the parent repository and dependencies; do not claim all underlying work began during the event. |
| English materials | English interface, source documentation, story and narration. | Check the final captions and published version. |
| Eligible entrant and authorized representative | The entrant and Nithya were confirmed on the Devpost roster. | Personal eligibility and representation attestations remain the owner's responsibility. Acceptance does not establish an application role or particular contribution. |
| Rights and third-party permissions | Project/dependency notices. V2 provenance review retained Kokoro-82M Apache-2.0 and kokoro-onnx MIT notices. | Retain notices and review final public assets. No avatar or cloned voice is used in V2. |
| Optional sponsor awards | [Postman collection](../postman/README.md) is authored and checked offline; [resource plan](RESOURCE_PLAN.md) records offers/status. | Actual Postman execution and sponsor-award qualification are not established. |

## Evidence inventory and scope

| Record | Establishes | Does not establish |
|---|---|---|
| [Local source review](../evidence/judge-portal-source-qa-2026-11-08.json), checkpoint `26893ed6` | 210 local tests, TypeScript, full lint and build passed for the seven-section interface. | External execution, browser behavior or final video quality; those need separate records. |
| [Current seven-section browser review](../evidence/judge-portal-browser-qa-2026-11-08.json) | `cfd1d007`: complete six-observation rehearsal, unchanged repeat result, Overview uncertainty shortcut and selected receipt inspection. Other recorded regressions cover selection/cancellation and fresh-demo entry. No captured application console messages. All seven views have 21 responsive measurements at layout-equivalent `26893ed6`. | Incognito automation, new live AI/PayPal calls, full accessibility/security coverage, browser file bytes or independent provider request counts. |
| Current `cfd1d007` deployment logs and CI, reviewed by release owner | Nine real PostgreSQL checks passed with no skips; migrations committed; Next.js 16.4.5 build and TypeScript passed; 12 static routes generated and deployment completed. Both CI workflows passed. | New external payment/model execution or a repeat of every historical manual check. |
| [Public access smoke](../evidence/judge-portal-public-access-2026-11-08.json) | `26893ed6`: canonical anonymous HTML/assets and a new simulated guest session were reachable with expected status/content types. | Browser hydration, clicks, responsive behavior or isolation beyond that smoke; the separate records supply their own scope. |
| [Earlier public browser review](../evidence/judge-browser-qa-2026-11-08.json) | Source `2caa74039`: six observed workflow steps and nine responsive views across the earlier three modules at 360/768/1280px, without horizontal overflow or captured application warnings/errors; 16px main text. | Hosted verification of the expanded seven-section portal. These counts remain historical. |
| [Earlier independent HTTPS review](../evidence/judge-hosted-qa-2026-11-08.json) | 21 expected outcomes across two fresh guests: isolation, denied cross-origin/owner/sandbox actions, response-loss recovery, repeat, own reset and retained old receipt. A 4,254-byte guest receipt passed the offline verifier. Separately attributes the release owner's 9/9 PostgreSQL gate. | A newly executed HTTP review for the expanded release, browser Blob/CSV bytes, direct database inspection, actual model/PayPal calls or signed receipt authenticity. |
| [Configured owner run](../evidence/configured-live-qa-2026-11-08.md) | One actual AI-to-PayPal sandbox purchase/recovery; owner profile/history and rehearsal observations; eight database checks/builds at that dated source. | Current seven-section judge QA, video publication, production funds, global request counts or browser CSV file bytes. |
| Frozen V2 validation; [full metadata](DEMO_SCRIPT.md#voice-and-render-status) | 141.354362 seconds, 7,744,891 bytes, 4,240 video frames; full decode passed. 43 captions retain 312 exact words. Audio peak −1.969 dBFS, zero clipped samples. Scenes 2, 3, 5, 6, 7 and 8 passed sampled visual review. | Independent listening, independent forced alignment or continuous recording of the original external transaction. Public playback is established separately below. |
| [YouTube publication](https://youtu.be/D4UXBT-FhcE), release-owner browser review | Studio showed Published/Public on 8 November; watch-page playback displayed 2:21. Exact native transcript saved for automatic timing; burned-in captions remain visible. | Completion of native selectable-caption processing, native-caption timing QA or full independent listening. Devpost video-field persistence is separately confirmed. |
| Rejected earlier video | Historical 163.521-second Flite/vector-presenter render and its mechanical checks. | Acceptance, publication readiness or satisfaction of the current video deliverable. Do not publish it. |
| [Business local checkpoint](../evidence/business-portal-checks-2026-11-08.json) and [native checkpoint](../evidence/native-vercel-checks-2026-11-08.json) | Earlier 199- and 178-test results and their stated build/audit scopes. | Latest source or hosted results. A later test count does not rewrite an older artifact. |
| [Earlier sandbox diagnostic](../evidence/diagnostic-release-review.json) | A fixed no-AI $180 PayPal sandbox capture/recovery on the former runtime. | The later genuine model journey or current public portal. |
| [Hosted renewal](../evidence/hosted-renewal-review.json), [workspace](../evidence/hosted-workspace-review.json) and [recovery](../evidence/hosted-recovery-review.json) | Their dated simulated expiry, cancellation, allowance and recovery observations. | New source verification, production payments or fresh model execution. |

The receipt inspector compares current purchase fields with stored provider observations: seller, amount, currency, operation/order/capture references and completion status. The exported receipt includes the current catalogue SKU and approval version. Its stored provider verification snapshot does not contain its own historical approval binding or catalogue SKU, so comparing current values does not independently establish what historical version/item the provider verification was bound to.

The [offline verifier](../scripts/verify-receipt.mjs) checks versioned structure, approval binding/digest and limited internal consistency. It is not an authenticity check: an author can replace both data and digest. The prior guest HTTPS download passed that check. The owner's browser CSV/Blob download collection timed out and its file bytes remain unverified.

## Five judging criteria

Names and equal weighting follow [rules section 6](https://paypalaihackathon.devpost.com/rules). The assessment below is ours.

| Criterion | Reason to choose ProofPay for closer review | Reason to hold selection | Next useful evidence |
|---|---|---|---|
| Technological Implementation | A genuine model proposal, explicit approval, reservation, native buyer approval and original-order recovery worked together on Vercel/Neon. | One seller, USD and one observed external run; bounded failure handling and unsigned evidence. | Publish the demonstrated workflow and preserve the completed external result without another model call. |
| Design | The new portal puts overview, purchases, approvals, receipts, controls and evaluation into the same application. State-dependent buttons explain the next action. | The fresh workflow and 21 layouts passed their stated checks. Customer usability and owner browser export bytes remain unverified. | Observe a target buyer completing an approval/recovery task and measure where they need help. |
| Potential Impact | Competing $180/$160 requests against $300 and a missing payment response create a specific operational problem. | Synthetic catalogue; no verified customers, saved hours or revenue. | A qualified agency's current workaround and measured approval/recovery effort under the [pilot plan](COMMERCIAL_PLAN.md). |
| Innovation/Idea | Business approval, shared allowance and recovery evidence stay connected through uncertainty. | Incumbents already offer agent payments, controls and idempotency; processor-parity claims would be unsupported. | Show the business decisions surrounding the payment API and test the [differentiation hypotheses](PRODUCT_STRATEGY.md). |
| Presentation | V2 follows one concrete purchase and leads with its business value, using real product controls. | The earlier presentation was rejected. Replacement V2 is public, mechanically validated and sample-reviewed; no independent listening result is claimed. Native selectable captions are still processing. | Retain the verified public video URL and clear historical/simulated labels. Keep final Submit held. |

## Verdict and next steps

**I would advance ProofPay for technical review because the central model-to-payment recovery workflow has been demonstrated. The public video and its saved Devpost URL are now verified. The final page remains Draft (3/5 steps); final submission stays held at the owner's instruction.** This is not a prediction of a prize or a claim to speak for PayPal's judges.

1. Preserve the completed seven-section browser record and its actual source/operation identities. Keep earlier three-view and two-guest HTTPS evidence separate; neither is a new measurement of the current release.
2. Preserve the verified [public V2 link](https://youtu.be/D4UXBT-FhcE). The video is published and plays at a displayed 2:21; native captions are still processing despite the saved exact transcript. Burned-in captions are already present. No independent listening result is implied by the playback, decode or sampled visual checks.
3. Preserve the verified current draft. The 7,531-character Story, canonical demo/source URLs, seven-view testing instructions, six scenario observations, 21 responsive views and Kokoro/FFmpeg/no-avatar disclosure were saved, reopened and matched. The published video URL, **https://youtu.be/D4UXBT-FhcE**, was also saved and reopened, and the embedded player showed the correct title. Finalization remains **Draft (3/5 steps)** with no final Submit clicked; the earlier terms check was unchecked.
4. Preserve the consumed inference grant and completed order/capture. Keep receipt limits, the unverified owner browser export and the product scope explicit.

Renewal does not extend PayPal order validity. Cancellation releases an unused reservation only before provider dispatch. Unknown create results without an order ID require investigation. Production flow, refunds, webhook handling, fulfillment, externally signed receipts and general exactly-once guarantees are outside this build.

The longer-term opportunity is an operations tool for a purchasing workflow that customers value. [Commercial hypotheses](COMMERCIAL_PLAN.md) and the [product roadmap](PRODUCT_STRATEGY.md) describe how to test that opportunity. Customers, valuation, processor parity and future market share are not established by this prototype.

At the latest handoff, the reviewed browser guest workspace was left fresh with $300 available, $0 reserved, $0 paid and two proposed requests. This is that temporary session's state, not a persistent global demo state. Its existing expiry was unchanged; no model allowance was reset.
