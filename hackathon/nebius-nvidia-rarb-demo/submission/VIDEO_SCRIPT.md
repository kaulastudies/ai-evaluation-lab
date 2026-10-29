# ProofGate — executable demo recording (target 2:35)

Use the public hosted app. Record real button clicks and returned results. The browser checks are fresh executions of previously generated candidates; they are not fresh model calls.

## 0:00–0:15 · Show the problem

“An AI coding agent can pass the tests and still produce a broken change. ProofGate lets an engineer inspect the contract, test the verifier and reproduce the verdict. Let's run it.”

Screen: Run the verifier, default false-green candidate. Click Run Python checks.

## 0:15–0:40 · Public PASS, independent FAIL

“This is an actual recorded data-transformation candidate. The public test passes. Four independent gates fail: row preservation, values and types, optional notes, and input mutation. These results have just been computed by Python in the browser.”

Screen: the returned PASS/FAIL comparison and gate diagnostics. Briefly open candidate code.

## 0:40–1:00 · Repair under the same contract

“This replacement was produced after the agent received bounded failed-gate evidence, without the hidden verifier or reference solution. The same checks now pass. This archived repair was generated with Ollama.”

Screen: Check the repair → Run Python checks; show the fresh result.

## 1:00–1:25 · Challenge the verifier

“Now we introduce a specific fault: turning zero into null. The ordinary test still passes, but the value-and-type gate catches it. We also test the verifier itself: a correct reference passes, while a known-bad baseline and four deliberate mutations fail.”

Screen: zero-to-null mutation, then all-six-controls result. Keep the important failing gate visible.

## 1:25–1:55 · Show NVIDIA and Nebius

“NVIDIA Nemotron 3 Super generates repository-task candidates through Nebius Token Factory. Here is a preserved Nemotron candidate from our fixed Phase 12 experiment. We can execute its actual Python checks in the browser and inspect its source, provider and hashes. Ten of ten Nemotron trials passed this one task; we don't treat that as a general model ranking.”

Screen: Verify Nemotron code → Run Python checks; then inspect its provenance in the evidence workbench.

## 1:55–2:15 · Runtime and repair integration

“The local workbench can make a new Nemotron generation request or ask it to repair the recorded AP-005 failure. A server-side key is required. Every returned result is retained. Source-exact replay is separate: it reruns the full evaluator at the historical Git commit without calling a model.”

Screen: Run it yourself. If a new live request has actually been completed, show the real returned report. Otherwise show the controls and state that live inference requires configuration; never imply it ran.

## 2:15–2:35 · Close with scope

“ProofGate is for engineering teams reviewing coding-agent changes. The open-source ledger keeps 52 attempts, including failures and HOLDs. The current evidence covers five synthetic tasks, not production reliability. Every claim has code and an inspectable artifact behind it.”

Screen: ledger, then public repository and setup instructions.

## Upload checklist

- Keep the finished video under three minutes and publicly visible on YouTube.
- Show working execution and readable results; no credentials or unrelated tabs.
- Preserve the distinction between browser verification, historical replay and fresh inference.
- Add the public video URL to Devpost and verify signed-out playback.
