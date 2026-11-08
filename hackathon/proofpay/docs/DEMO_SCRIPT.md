# Demonstration recording script

Target duration: **2 minutes 45 seconds**. This is a recording plan, not evidence that the described external integrations have succeeded. PayPal sandbox OAuth and create/GET preflight passed; the current build has no verified genuine model invocation or buyer-approved sandbox capture. Use the rehearsal wording until the corresponding external run is recorded.

## Before recording

- Verify the application and mode labels are legible at the recording resolution.
- Use the synthetic catalogue and a clean demonstration workspace.
- Keep credentials, tokens and unrelated account records out of the recording.
- Record the exact source commit, model configuration and environment privately with the run evidence.
- Complete a normal run and the interruption/recovery run before filming. Retain failures and the source version used.
- If external integrations are unavailable, label the recording as a rehearsal and say which actions are simulated. Do not present it as the final real-integration demonstration.

## Story and footage

| Time | Action | Suggested narration |
|---|---|---|
| 0:00–0:15 | Choose **Start $300 rehearsal**; keep the mode visible | “Our studio has $300 for outside review work. This recording uses the labelled simulated provider. The owner controls each purchase.” |
| 0:15–0:40 | Show the $180 and $160 requests. Approve $180, then attempt $160 | “These requests cannot both fit. Owner approval reserves $180. The second request is blocked because only $120 remains.” |
| 0:40–0:55 | Choose **Request an alternative**, enter “Suggest a cheaper Starter review package”, then **Create sample proposal** | “A smaller package can fit. It is a new proposal that still needs owner approval. In rehearsal, this selection uses a rule; it is not a model call.” |
| 0:55–1:15 | Return to the $180 request, choose **Create simulated order** | “The approved item, merchant, currency and amount stay attached to this operation. This is the simulated order we will check later.” |
| 1:15–1:35 | Select **Drop the capture response**, then **Capture simulated payment** | “The simulated provider processes the capture, but the application discards its response. The outcome stays unresolved and the $180 stays reserved.” |
| 1:35–2:00 | Show the unresolved state, then **Check simulated outcome** | “Recovery reads the original order. It checks the references, merchant, full amount, currency and completed capture before recording payment.” |
| 2:00–2:25 | Show **Simulated payment confirmed**, **Check outcome again** and exported evidence | “The reservation becomes recorded spend. Checking again does not add another $180 in this run. The receipt keeps the operation and provider evidence together.” |
| 2:25–2:45 | Show setup, architecture and actual validation results | “This build covers one controlled merchant, USD and the documented cases. Real model and PayPal sandbox verification remain separate from this rehearsal.” |

## Practical editing

Use a cursor that is easy to follow. Keep the product visible rather than alternating between long slides. Cuts may shorten waiting periods if their meaning is clear. Do not conceal failed attempts or splice a simulated result into a real-sandbox sequence. A short caption can identify the run, environment, injected fault or skipped wait.

Record a normal purchase separately as preflight evidence. The main sequence uses one interrupted purchase so the allowance and operation remain easy to follow. Do not approve the $90 alternative during this sequence; it is there to show a useful next proposal without distracting from the $180 recovery.

If demonstrating a backend process restart, stop and restart the server with the same persisted database before choosing **Check simulated outcome**. Preserve the process evidence and label any edit. Say “The operation survived a backend restart” only when that exact result has been observed. A browser refresh or a fresh service object is not the same test.

## Recording the external integration

After successful real-provider preflight, substitute **Start PayPal sandbox workspace** and **Ask AI for a proposal** for seeded rehearsal. Show the resulting model proposal, owner approval, **Create PayPal order**, **Open PayPal approval**, **Capture approved order**, and **Check PayPal outcome**. Native buyer approval is part of the flow; do not edit it into an implied autonomous purchase. Identify any skipped wait with a caption.

Replace the rehearsal narration with the actual model and PayPal sandbox facts. If using **Drop the capture response**, describe it as an application fault injection after the sandbox action, not as a PayPal outage. Keep the **PayPal sandbox** mode label visible and preserve the matching sandbox order/capture evidence. Do not splice a simulated recovery into this sequence.

## Final checks

- Narration, screenshots and project description match the same delivered source version.
- No claim of real AI inference appears without a recorded model call.
- No claim of PayPal confirmation appears without actual sandbox evidence.
- No generic production-safety or exactly-once guarantee appears.
- The result is understandable without knowledge of internal state-machine names.
- The final video is under three minutes and publicly viewable on YouTube to meet the official rules.
- The submitted repository and demonstration are accessible to judges. The current private owner-only Site is not judge-access ready.

## Closing line

Use only once the corresponding workflow is demonstrated:

> ProofPay gives the owner a clear spending decision and an inspectable answer about what happened to the payment.

## Slow buyer approval

If the 15-minute application approval expires before capture, show **Renew approval**, review the unchanged purchase and confirm the renewal. The same order and reservation remain in place. This renews application authority only; it does not extend PayPal order validity. Never renew or retry a dispatched or uncertain capture.
