# ProofGate — recording plan (target 2:45)

Record the actual interface and local runner. Upload the finished video to a public YouTube URL. This script is preparation, not a produced or published video.

## 0:00–0:20 · The problem

Screen: AP-005 false-green case, with public PASS and VERIFIED_FAIL visible.

“An AI coding agent can pass the tests and still produce a broken change. ProofGate makes that gap visible. This is a real recorded candidate: its public tests passed, but four independent checks failed.”

## 0:20–0:50 · Show the failure

Open Candidate code, then Verifier gates. Point at the actual diagnostics.

“The task is a data transformation. Its contract requires preserving rows, zero and false values, optional notes and the original input. These four gates caught failures the public tests missed. Before using this verifier, we tested it against a reference, a known-bad implementation and deliberate mutations.”

## 0:50–1:15 · Show the repair

Click Bounded repair, then Verify again. Open Provenance to show the parent hash.

“The repair receives the failed-gate IDs and bounded diagnostics, not the hidden verifier or reference solution. The same verifier evaluates the replacement. This attempt passes, and its record links back to the original failure. This specific repair was generated with Ollama.”

## 1:15–1:50 · Show Nebius and NVIDIA

Select AP-001 · Nebius / Nemotron. Show the model ID, source commit and latency. If the local key is configured, perform a fresh run before recording and show its returned report. If no fresh run is available, clearly say this is preserved runtime evidence.

“We also run NVIDIA Nemotron 3 Super through Nebius Token Factory. Here is a preserved repository-task execution, including its candidate, token usage, latency and exact evaluator source. Ten fixed Nemotron trials passed this AP-001 contract. That is one bounded experiment, not a general model ranking.”

## 1:50–2:20 · Actually replay

In the local workbench, click Re-execute verifier locally and show the returned status and record hashes. No key is needed for replay.

“This action runs the historical evaluator again against the recorded candidate. It does not call a model. The reproduced verdict and record hash match the original evidence. The hosted browser can separately check artifact hashes; those checks are not evaluator execution.”

## 2:20–2:45 · Scope and close

Show the full ledger, filter VERIFIED_FAIL, then show the public repository.

“The ledger keeps all 52 attempts, including five failures and three HOLDs. Five tasks are verifier-qualified, with zero observed escapes among 17 mutations. ProofGate helps engineering teams inspect why an agent's change passed, and reproduce that decision. The code, setup instructions and evidence are open source.”

## Before uploading

- Keep the final cut under three minutes.
- Show the app working, not only slides.
- Keep credentials and unrelated browser tabs out of the recording.
- Do not label a recorded result as fresh inference.
- Use the public YouTube URL in Devpost and check it while signed out.
