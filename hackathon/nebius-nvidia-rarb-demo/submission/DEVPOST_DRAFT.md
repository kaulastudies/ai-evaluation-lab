# ProofGate — Devpost submission draft

## Project name

ProofGate — Independent Verification for Coding Agents

## Tagline

The tests passed. The patch was still wrong. Verify the verdict before trusting the agent.

## Track

Coding and Agentic Engineering

## Inspiration

Coding agents can change a repository, run its tests and report success. That still leaves a practical question for the engineer reviewing the work: did the change satisfy the task, or did the tests miss the bug?

We built ProofGate for teams evaluating coding agents and reviewing their outputs. It makes the evidence behind a verdict inspectable, including the cases where the model fails or produces output that cannot be admitted.

## What it does

ProofGate runs repository tasks through a coding model, evaluates the candidate against a frozen contract and records VERIFIED_PASS, VERIFIED_FAIL or HOLD. Before trusting a verifier, it checks a reference implementation, a known-bad implementation and critical mutations.

The hosted demo executes the actual Python tests and verifier in the browser, with no installation or API key. Judges can select a recorded candidate, run it, inspect the fresh result, and introduce a known fault.

The demo follows a real data-transformation failure. Public tests pass, but four independent gates catch failures in row preservation, falsy values, optional fields and input mutation. A bounded repair receives failed-gate IDs and diagnostics; the same verifier then accepts the replacement. This repair example was generated with Ollama.

A separate case shows NVIDIA Nemotron 3 Super generating an AP-001 repository patch through Nebius Token Factory. Judges can inspect the candidate, returned gates, token counts, latency, source commit and hashes. The ledger retains every committed attempt, including failures and malformed-output HOLDs.

## How we built it

The underlying Repository Agent Reliability Benchmark, or RARB, uses Python and task adapters to control model-visible context, candidate admission, public tests, verifier execution and trusted-file checks. Nebius Token Factory supplies inference through its OpenAI-compatible chat-completions API. The recorded NVIDIA model is `nvidia/nemotron-3-super-120b-a12b`.

The frontend is dependency-free HTML, CSS and JavaScript. Its evidence bundle is generated from repository artifacts, rather than handwritten outcome summaries. It can verify candidate and response SHA-256 hashes and export the selected evidence.

The local workbench adds real source-exact replay: it checks out the evaluator commit used in the original run and re-executes it against the recorded response. With a server-side Nebius key, it can generate and verify one fresh AP-001 candidate. New results remain separate staging records until reviewed. Hosted mode now includes real Python verifier execution through Pyodide, alongside the stored-evidence explorer. Browser execution uses the bundled verifier; the full historical evaluator replay remains a separate local action. Neither is described as fresh inference.

A second local action asks Nemotron to repair the fixed AP-005 failure. It sends bounded failed-gate evidence and applies the same verifier to the returned candidate. This route is implemented; a new live provider result must be verified before it is claimed in the submission.

## Challenges we ran into

The verifier itself needed testing. Ordinary test coverage could miss exactly the behavior we intended to evaluate. We added reference, known-bad and mutation controls before treating the verifier's result as qualified evidence.

Reproducibility also required preserving the evaluator version. Re-running an old candidate against today's evaluator is not the same experiment. Source-exact replay uses the original source commit and compares the reproduced record with the preserved one.

Malformed responses and failed repairs needed their own outcomes. We retained them instead of silently cleaning the output or retrying until the demo looked successful.

## Accomplishments

The current committed ledger contains 52 attempts: 44 VERIFIED_PASS, 5 VERIFIED_FAIL and 3 HOLD. All five synthetic tasks have qualified verifiers, with zero escapes among 17 critical mutations.

Phase 12 fixed one task, three configurations and ten trials per configuration. It retained 29 passes and one failure, with all 30 recorded source-exact replays verified. The ten Nebius/Nemotron trials all passed their AP-001 contract. These are bounded observations, not a claim of general model superiority.

The workbench now connects the product story to the actual artifacts: the faulty code, the failed gates, the repair, the source commit and the reproduced verdict.

## What we learned

A useful evaluation needs a clear boundary. A browser animation, a hash match, an evaluator replay and fresh inference are different kinds of evidence. Keeping those distinctions visible makes the result easier to assess and reproduce.

## What's next

Broader repository tasks, isolated execution workers, stronger request-level model provenance and measured operating cost. The original AP-001-specific false-green → repair → pass sequence remains open; the AP-005 repair does not close it.

## Team and mentorship

ProofGate is developed by Rama Chandra, with mentorship from Prof. Nithya Ravi Kumar. We thank her for her mentorship.

A research review pack has been prepared for Prof. Nithya Ravi Kumar covering experiment design, verifier qualification, claim-to-evidence checks and demo clarity. These are proposed review responsibilities; her review and feedback are pending. Existing code and experimental results are attributed to their recorded contributors and providers.

## Built with

Python, Pyodide/WebAssembly, JavaScript, HTML, CSS, Git, NVIDIA Nemotron 3 Super, Nebius Token Factory, Ollama, GitHub Actions.

## Submission fields requiring completion

- Public repository: https://github.com/kaulastudies/ai-evaluation-lab
- Updated implementation: public repository `main`; executable workbench merged in PR #28.
- Demo URL: https://kaulastudies.github.io/ai-evaluation-lab/proofgate/
- Public YouTube video: upload and verify the 119-second captioned walkthrough, or record the spoken flow using VIDEO_SCRIPT.md; maximum three minutes. The MP4 is available at https://kaulastudies.github.io/ai-evaluation-lab/proofgate/proofgate-walkthrough.mp4 . YouTube upload is still outstanding.
- Significant updates: use SIGNIFICANT_UPDATES.md.
- Platform feedback: use NEBIUS_NVIDIA_FEEDBACK.md.
- IRL city: select only an event actually attended.

Do not describe a new live model run as completed until its returned evidence has been inspected. Final Devpost submission has not been confirmed.
