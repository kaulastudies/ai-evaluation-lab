# ProofGate — Independent verification for coding agents

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](../../LICENSE)

ProofGate is the judge-facing product built on AI Evaluation Lab's Repository Agent Reliability Benchmark (RARB). It is the existing **Nebius × NVIDIA Global AI Hackathon** entry, in **Coding and Agentic Engineering**.

A coding agent can pass ordinary tests and still break the task contract. ProofGate qualifies the verifier, evaluates the candidate, preserves failures and HOLDs, and supports bounded repair with reproducible evidence.

## Team and mentorship

**With mentorship from Prof. Nithya Ravi Kumar.** Rama Chandra leads implementation, experiments and evidence curation. We thank Prof. Nithya Ravi Kumar for her mentorship.

Her proposed methodology and evidence review responsibilities are documented in the [team record](TEAM.md), with a [research review pack prepared for her](submission/MENTOR_REVIEW_PACK.md). These reviews are pending; no completed review or approval is claimed.

![ProofGate team and mentorship](submission/media/proofgate-team-card.svg)

## Judge demo: execute real checks in the browser

The first page now runs the actual Python public tests and qualified verifier using Pyodide. Judges can execute a recorded false-green, its repair, a Nebius/Nemotron candidate, a preserved failure, or six qualification controls. Results are produced at runtime; no API key or installation is needed in the hosted demo. The browser run is clearly labeled as current-verifier re-execution, separate from historical source-exact replay and new model inference.

## Start here

- [Open the browser demo](https://kaulastudies.github.io/ai-evaluation-lab/proofgate/)
- [Watch the 119-second captioned walkthrough](https://kaulastudies.github.io/ai-evaluation-lab/proofgate/proofgate-walkthrough.mp4)

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
git switch main
python hackathon/nebius-nvidia-rarb-demo/prepare_browser_runtime.py
python hackathon/nebius-nvidia-rarb-demo/serve.py
```

Open `http://127.0.0.1:8080`. Select a case and click **Re-execute verifier locally**. This really runs the historical Python evaluator with the recorded candidate, without model inference. The app shows the returned report, including failed outcomes.

For fresh inference, set `NEBIUS_API_KEY` in the server environment before launch. **Run it yourself → Generate & verify one candidate** makes one runtime request to Nebius Token Factory using `nvidia/nemotron-3-super-120b-a12b`, then runs admission, public validation and the qualified verifier. The key stays server-side. Source must be committed; all outcomes are staged under a unique `runs/live/rarb/proofgate-nebius-*` directory and are not silently promoted into the published ledger.

The interface contains secure PowerShell setup commands. Do not put keys in source files or the browser.

**Execution boundary:** the server binds only to loopback and validates Host, Origin, a session token and an evidence allowlist. It is not a public execution API or an OS sandbox. Run fresh model candidates in a disposable development environment. AST admission alone is not an isolation guarantee.

## Hosted execution and evidence mode

The static site includes the executable Python verifier lab and supports five stored evidence cases, code/gate/provenance inspection, a searchable 52-attempt ledger, qualification controls, SHA-256 artifact checks, and evidence download. It clearly labels stored evidence and enables browser verification. Only server-side inference and full historical replay require the local server. It does not claim that browser hash checks execute the evaluator or call Nebius.

The canonical public demo is deployed from this repository by [ProofGate GitHub Pages](../../.github/workflows/proofgate-pages.yml): https://kaulastudies.github.io/ai-evaluation-lab/proofgate/ . Pull requests build the site; changes merged into `main` publish it. The root Pages URL presents AI Evaluation Lab as the parent project.

The app, local server, evidence generators, deployment workflow, media, screenshots and media-build script are all in this public repository. The build downloads the pinned open-source Pyodide runtime and verifies its file sizes and SHA-256 hashes before publishing. The running site serves these runtime files from GitHub Pages. It has no dependency on the earlier ChatGPT-hosted demo.

To build the same static site from a fresh clone:

```bash
python hackathon/nebius-nvidia-rarb-demo/build_pages.py
python -m http.server 8080 --directory .proofgate-pages
```

Open `http://localhost:8080/proofgate/`. The output includes an explicit allowlist of public files; it does not publish the local server or environment files. `proofgate/deployment.json` records the deployed source commit, canonical evidence commit and file hashes. Use a new or empty output directory for each build, or pass `--output /path/to/empty-directory`.

GitHub Pages serves the browser verifier and recorded evidence. Fresh Nebius inference and historical source-exact replay use `serve.py` locally; they require a Python server and are not executed by GitHub Pages. The existing Vercel root-directory configuration remains available for other hosting.

## Nemotron repairs the recorded failure

The local **Ask Nemotron to repair AP-005** action makes one Nebius request using the fixed, recorded AP-005 failure as its parent. It calls the existing bounded repair engine with failed gate IDs, at most 600 diagnostic characters, no hidden verifier/reference source, and repair index 1. It then applies the same qualified verifier. The provider key is required; this new route has not yet been exercised against the live service in the current build environment. Test fixtures are never counted as model evidence.

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
