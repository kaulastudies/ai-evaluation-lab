# Try ProofPay as a judge

Open **[proofpay-evaluation-lab.vercel.app](https://proofpay-evaluation-lab.vercel.app)** and choose **Open judge workspace**. You do not need a Vercel account, a ProofPay owner login, a PayPal account, API keys or a local database. The workspace is interactive and keeps your own simulated purchases separate from other visitors.

This guide describes the verified seven-view portal. The [current browser review](../evidence/judge-portal-browser-qa-2026-11-08.json) reached **6/6 workflow observations** on `cfd1d007`. All seven views passed **21 responsive checks** at 360/768/1280px, without horizontal overflow and with 16px main text. The local checkpoint `26893ed6` passed 210 tests, types, lint and build; the current deployment passed nine real PostgreSQL checks with no skips, migrations and build. The layout measurements use `26893ed6`; the subsequent change affects preferred workflow selection only.

## The problem to try

A studio has $300 for outside reviews. Two requests cost $180 and $160. Approving one leaves too little allowance for the other. If a payment response then disappears, the owner needs to know what remains reserved and how to check the original outcome.

The public workspace lets you make those decisions yourself. Its requests and payment provider are explicitly simulated. A separate, completed owner run used an actual AI proposal and PayPal sandbox purchase; you can review that recorded route in **AI & backend** without making another model call.

## Explore the workspace

| View | What you can do |
|---|---|
| Overview | See available, reserved, paid and unresolved amounts, then continue a purchase. |
| Purchases | Open a request, inspect its seller/amount and use the next permitted action. |
| Approvals | Review requests and reserve allowance for an exact purchase. |
| Evidence | Inspect recorded approvals, provider observations and operation receipts. |
| Controls | Read the rules; use the workspace’s **Start fresh demo** action to repeat the flow. |
| AI & backend | Review the simulated configuration and the recorded real model-to-PayPal route. This view is read-only. |
| Evaluation lab | Follow six observations as you complete the workflow. An unobserved item is not a failed test. |

Your guest role controls this rehearsal only. The private owner workspace is a separate application and is not needed for judging.

## Complete one purchase, including a missing response

1. Start with **$300 available, $0 reserved and $0 paid**. If your earlier demo is already complete, choose **Start fresh demo**, then **Confirm fresh demo**. These actions are available in every loaded section. This creates a fresh simulation; it does not erase the previous receipt or touch a real payment.
2. In **Approvals**, approve the **$180 Workflow review**. Confirm that $180 is reserved and $120 remains available.
3. Try to approve the **$160 Design review**. It should be blocked because only $120 remains. The first purchase keeps its reservation. Use **Continue workflow** to return to its next action when needed.
4. Return to Workflow review in **Purchases** and choose **Create simulated order**. Enable **Drop the capture response**, then choose **Capture simulated payment**.
5. Inspect the unresolved result: **$180 reserved, $120 available, $0 paid**. Choose **Reload page to check persistence**. The same operation, order and held amount should return.
6. Choose **Check simulated outcome**. The original order is checked, then the totals become **$180 paid, $0 reserved, $120 available**.
7. Choose **Check the same outcome again**. The capture reference and totals should remain unchanged. This is an outcome lookup, not another capture.
8. Open **Evidence** to inspect the purchase and provider fields, then **Evaluation lab** to review the six observed steps. Choose the **Purchase record**, open **Inspect approved vs observed receipt**, or use **Export all receipts** to export simulated JSON evidence from the app.

For an extra approval case, choose **New sample request**, ask for a cheaper $90 Starter review and select **Create sample proposal**. Approve it, then cancel it before creating a provider order. The reservation should be released while the request remains recorded. A new sample request always needs its own approval.

## What the actual AI and PayPal run proved

On 8 November, the private owner application completed one `openai/gpt-4.1-mini` proposal through Vercel AI Gateway, followed by owner approval and native PayPal sandbox buyer approval. The application deliberately dropped the $180 capture response. The reservation survived browser reload; a GET of the original PayPal order confirmed the matching completed capture, and another check preserved the same totals.

The [recorded run](../evidence/configured-live-qa-2026-11-08.md) identifies the model, operation, order and capture. It used virtual sandbox funds. The reviewed one-attempt free-credit grant is consumed: judging uses the repeatable simulation and existing evidence, with no new AI request, payment or grant reset.

The receipt inspector shows stored application observations. The exported receipt includes the current SKU and approval version; its provider verification snapshot lacks its own historical approval binding/catalogue SKU. These are unsigned application records. Browser reload is a persistence check, not a hosted backend restart.

## Access and verification

Guest sessions last two hours, with up to 100 mutations and 10 resets. The deployment admits at most 60 new sessions per hour and 300 total. These limits keep the public rehearsal bounded; they do not spend model credits. If a session expires, begin another isolated workspace from the public landing page, subject to those limits.

The earlier public release at source `2caa74039` passed 210 local tests and nine real PostgreSQL checks. [Independent HTTPS QA](../evidence/judge-hosted-qa-2026-11-08.json) passed all 21 expected outcomes, including two-guest isolation, rejected owner/sandbox/cross-origin actions, recovery and retained receipts after reset. [Browser QA](../evidence/judge-browser-qa-2026-11-08.json) observed the full six-step flow and checked the preceding three-view interface at phone, tablet and desktop widths. Those records retain their earlier scope. The current seven-view browser and 21-layout results are separate: the earlier 21 HTTPS outcomes are not the new responsive count. The captured application console for the current workflow was empty.

An actual 4,254-byte receipt downloaded through the evidence API passed the offline consistency verifier. Browser Blob/CSV download bytes remain a separate unfinished check. The guest portal exports JSON evidence; the private owner portal also has CSV reporting.

The replacement [Kokoro V2 video](../tools/demo-video-v2/README.md) is frozen at **141.354362 seconds (2:21.354)**, with 43 captions preserving all 312 narration words and 29 timed shots of actual captured UI states. It uses no avatar. Full decode, audio/caption checks and sampled visual review passed; no independent listening or forced-alignment result is claimed. Scene six is clearly labelled saved evidence from the completed external run. The old Flite presentation was rejected and is not the current video.

**Public YouTube URL: pending manual MP4 selection/upload and fresh-viewer playback.** The current Devpost Story, demo/source links and testing/AI-tool disclosures were saved and reopened successfully. Its video field remains empty and final Submit remains held.

For technical review after trying the app: [repeatable checks](REPEATABLE_TESTING.md), [architecture](ARCHITECTURE.md), [readiness assessment](JUDGE_READINESS.md) and [source](https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay). The prototype covers one sample seller and USD; it does not implement production payments, refunds or fulfillment.
