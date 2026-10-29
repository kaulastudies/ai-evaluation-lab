# ProofGate / RARB — recovered project context

Consolidated October 29, 2026 (India Standard Time).

## Decision

Continue the existing **AI Evaluation Lab / Repository Agent Reliability Benchmark (RARB)** entry under the product name **ProofGate — Independent Verification for Coding Agents**. The track is **Coding and Agentic Engineering**. Starting an unrelated project would discard working evaluation, provider integration and reproducible evidence.

Deadline: **October 30, 2026, 10:30 PM IST**. Official rules: https://nebiusglobalaihackathon.devpost.com/rules

## Recovered history

- September 19: RARB execution engine, task adapters, qualified verifiers, source-exact replay and bounded repair developed within AI Evaluation Lab.
- September 21: Nebius/Nemotron AP-001 pilot; fixed Phase 12 matrix; provider evidence and replay checks; first hackathon interface and submission package.
- October 13: ProofGate proposed as the clearer product name for the same reliability system.
- Later Phase 13: IBM Bob AP-001 evidence added. The canonical ledger advanced from 51 attempts / 43 passes to 52 attempts / 44 passes.
- October 26–28: earlier context reported a Devpost draft named “Untitled.” Registration/draft existence is not final submission. Current Devpost fields have not been read or edited in this implementation pass.
- October 29: recovered repository and prior decisions; replaced the old presentation with the ProofGate workbench, generated evidence bundle, local execution interface, current ledger and submission package.

## Source of truth

Public repository: https://github.com/kaulastudies/ai-evaluation-lab

Public implementation: `main`. The original development branch was `feat/proofgate-hackathon-judge-demo`; its work is merged.

Demo path: `hackathon/nebius-nvidia-rarb-demo/`

Canonical RARB evidence: `programs/repository-agent-reliability/`

Evidence snapshot used by the workbench: `666aa1c08cbad1103c575d580234a1b2e577417c`. Generation source commits remain separately recorded per attempt. Existing frozen records were not rewritten.

## Verified evidence

| Item | Current result | Boundary |
| --- | --- | --- |
| Canonical attempts | 52: 44 PASS, 5 FAIL, 3 HOLD | Includes later IBM Bob pass; older demo's 51 was stale |
| Verifier qualification | 5/5 tasks; 0/17 critical mutation escapes | Only the supplied synthetic tasks and controls |
| Phase 12 | 29/30 pass; 30/30 recorded source-exact replay | AP-001 only, three configurations, ten trials each |
| NVIDIA Nemotron on Nebius | Pilot plus ten Phase 12 runs preserved; Phase 12 10/10 pass | Historical inference; not fresh inference this session |
| False-green → bounded repair | AP-005 failure and successful repair | Ollama llama3, not Nemotron |
| AP-001 Section 9 sequence | Still open | AP-005 repair does not close this task-specific requirement |
| Fresh source-exact replay | Nemotron pass, AP-005 failure and AP-005 repair reproduced in this implementation session | Uses recorded response; no new inference |

## Judge-focused product decisions

- **Implementation:** expose real gates, hashes, source commits and runtime reports. Keep historical replay separate from inference.
- **Design:** start with one understandable failure; let judges inspect code and diagnostics in the same workbench.
- **Impact:** focus on engineers evaluating coding agents and reviewing generated changes. Do not invent customers, adoption, time savings or production results.
- **Idea:** test the verifier with controls before trusting its verdict; preserve failed runs and reproduce decisions against the original evaluator.

## Completed in this pass

- Five inspectable cases: false-green, repair, Nebius/Nemotron pass, preserved public-test failure and admission HOLD.
- Searchable ledger generated from all 52 canonical attempts, with unavailable fields displayed honestly.
- Candidate, raw response, raw evaluation, parent links, source provenance and downloadable evidence.
- Browser-side SHA-256 artifact checking on HTTPS/localhost.
- Loopback local server for genuine source-exact replay and an optional single Nebius AP-001 run.
- Server request checks and integration tests; fresh runs require a key and clean committed source.
- Updated Devpost description, judge instructions, video recording plan and significant updates.

## Remaining before submission

1. Configure a Nebius key in the local runtime and inspect one fresh candidate run. The key was not available in this execution environment. Do not paste it into chat.
2. Public demo: https://kaulastudies.github.io/ai-evaluation-lab/proofgate/ . Public access is enabled; perform a final signed-out check before submitting.
3. Upload and verify the 119-second captioned walkthrough on public YouTube, or record the spoken flow. The walkthrough uses real browser execution screenshots; see VIDEO_PROVENANCE.md. YouTube upload is not yet complete.
4. Merge the reviewed implementation or clearly provide the exact public branch for judging.
5. Complete the existing Devpost draft, replace “Untitled” if still present, add demo/video/repository links, feedback and significant updates, and submit before the deadline.

## Explicit limits

The hosted app executes bundled Python checks and displays recorded evidence. It is not a hosted inference service. The local runner uses AST admission and temporary workspaces, not an OS security sandbox. A production deployment would need isolated execution workers. Provider cost is not fully measured. No winning outcome can be promised.

## Competitive refinement, October 29

The hosted app now executes actual Python checks, instead of requiring local installation for all execution. It bundles the existing public tests and verifiers unchanged, offers ten fixed candidates and runs the six AP-005 qualification controls together. Native validation confirms all expected outcomes, including a public-pass zero-to-null mutation caught by AP005-G02. Browser execution has been observed on the recorded false-green, its repair, the zero mutation, all six controls and the archived Nebius/Nemotron candidate. This mode is distinct from full historical source-exact replay.

The local runtime now also offers a one-call Nemotron repair of the fixed AP-005 parent failure, with the existing bounded diagnostics and verifier. A fresh service result remains pending a configured Nebius key. See JUDGE_REVIEW.md for the criterion-by-criterion assessment and the focused demonstration sequence.


## Mentorship and team update

At Rama Chandra's request, Prof. Nithya Ravi Kumar is acknowledged as a mentor for ProofGate. A substantial methodology and evidence review pack has been prepared for her. Responsibilities are proposed and reviews remain pending; no historical code, experiments or approvals are attributed to her without a contribution record. See TEAM.md and submission/MENTOR_REVIEW_PACK.md.

Final Devpost submission remains on hold at the user's request. Invitation acceptance must be checked in Devpost separately. The public browser demo is live, the executable workbench is merged in PR #28, and the updated captioned video is 119 seconds including mentorship credits. YouTube upload remains outstanding.
