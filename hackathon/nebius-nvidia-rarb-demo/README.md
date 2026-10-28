# ProofGate — Independent verification for coding agents

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](../../LICENSE)

ProofGate is the judge-facing product built on AI Evaluation Lab's Repository Agent Reliability Benchmark (RARB). It is the existing **Nebius × NVIDIA Global AI Hackathon** entry, in **Coding and Agentic Engineering**.

A coding agent can pass ordinary tests and still break the task contract. ProofGate qualifies the verifier, evaluates the candidate, preserves failures and HOLDs, and supports bounded repair with reproducible evidence.

## Start here

- [Recovered project context and completion checklist](submission/PROJECT_CONTEXT.md)
- [Devpost description](submission/DEVPOST_DRAFT.md)
- [Judge testing instructions](submission/JUDGE_TESTING.md)
- [Under-three-minute recording script](submission/VIDEO_SCRIPT.md)
- [Significant submission-period updates](submission/SIGNIFICANT_UPDATES.md)
- [Nebius and NVIDIA feedback](submission/NEBIUS_NVIDIA_FEEDBACK.md)

## Run the working app

Python 3.10+ and Git are required. Clone with full history; source-exact replay needs historical commits.

```bash
git clone https://github.com/kaulastudies/ai-evaluation-lab.git
cd ai-evaluation-lab
git switch feat/proofgate-hackathon-judge-demo
python hackathon/nebius-nvidia-rarb-demo/serve.py
```

Open `http://127.0.0.1:8080`. Select a case and click **Re-execute verifier locally**. This really runs the historical Python evaluator with the recorded candidate, without model inference. The app shows the returned report, including failed outcomes.

For fresh inference, set `NEBIUS_API_KEY` in the server environment before launch. **Run it yourself → Generate & verify one candidate** makes one runtime request to Nebius Token Factory using `nvidia/nemotron-3-super-120b-a12b`, then runs admission, public validation and the qualified verifier. The key stays server-side. Source must be committed; all outcomes are staged under a unique `runs/live/rarb/proofgate-nebius-*` directory and are not silently promoted into the published ledger.

The interface contains secure PowerShell setup commands. Do not put keys in source files or the browser.

**Execution boundary:** the server binds only to loopback and validates Host, Origin, a session token and an evidence allowlist. It is not a public execution API or an OS sandbox. Run fresh model candidates in a disposable development environment. AST admission alone is not an isolation guarantee.

## Hosted evidence mode

The static site supports five evidence cases, code/gate/provenance inspection, a searchable 52-attempt ledger, qualification controls, SHA-256 artifact checks, and evidence download. It clearly labels stored evidence and disables runtime controls. It does not claim that browser hash checks execute the evaluator or call Nebius.

To host, serve `index.html`, `style.css`, `app.js`, and `evidence.json` together over HTTPS. The existing Vercel root-directory configuration remains supported. A private review preview has also been prepared through Sites; make the intended judge URL publicly accessible before submitting.

## Rebuild the evidence bundle

```bash
python hackathon/nebius-nvidia-rarb-demo/build_evidence.py
```

The builder reads canonical artifacts and verifies candidate/response hashes. It pins evidence links to the last commit changing RARB evidence. No model outcomes are authored in the interface.

## Validation

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python programs/repository-agent-reliability/demo/run_demo_check.py
node --check hackathon/nebius-nvidia-rarb-demo/app.js
```

The server integration tests exercise actual Nemotron evidence replay, actual repair replay, hostile Origin/Host rejection, missing credentials, unknown evidence identifiers, duplicate execution, and canonical bundle consistency.

## Evidence scope

The current canonical ledger contains **52 attempts: 44 VERIFIED_PASS, 5 VERIFIED_FAIL, 3 HOLD**. Phase 12 is one AP-001 task, three fixed configurations and ten attempts each: 29/30 passes, 30/30 recorded source-exact replays, and 10/10 Nemotron passes. The AP-005 false-green → repair example uses **Ollama**, not Nemotron. The original AP-001 Section 9 sequence remains open. These observations do not establish production reliability or general model superiority.
