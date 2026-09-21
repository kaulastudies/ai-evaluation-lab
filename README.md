# AI Evaluation Lab

## Reproducible evidence for AI systems and agents

**AI Evaluation Lab is an independent engineering lab building provider-neutral infrastructure to test, verify, compare, and reproduce the behavior of AI systems and agents.**

As AI systems become more capable of acting through tools, code, browsers, APIs, and enterprise workflows, evaluation has to become more than a leaderboard score. Teams and researchers need evidence that is versioned, inspectable, reproducible, and useful for identifying regressions before deployment.

The Lab is building that evidence layer.

> **Operating principle:** build evidence before claims.


### Current technical state

The public Lab now has two original agent-evaluation task packs plus a repository-agent reliability program:

- **AS-001 — Permission Boundary / Constraint Adherence**, with published Ollama and Groq runs under the same frozen task contract;
- **AS-002 — Least-Privilege Tool Escalation**, with deterministic reference and known-bad controls and live-provider runs intentionally not yet claimed;
- **RARB v0.1 — Repository Agent Reliability Program**, with five verifier-qualified synthetic repository tasks, frozen live evidence, bounded repair, and source-exact no-model replay.

The AS task packs remain CI-gated. RARB v0.1 is merged into `main`; its deterministic
runner, replay, repair-replay, metrics, and demo-evidence checks are gated in CI.

[RARB program](programs/repository-agent-reliability/README.md) | [RARB evidence brief](programs/repository-agent-reliability/demo/EVIDENCE_BRIEF.md) | [RARB demo status](programs/repository-agent-reliability/demo/DEMO_STATUS.md)

[Capabilities](docs/CAPABILITIES.md) | [Evidence catalog](docs/EVIDENCE_CATALOG.md) | [Private engagements](docs/ENGAGEMENTS.md)

---

## Capabilities

AI Evaluation Lab currently works across four technical layers:

- **task-contract and verifier engineering** — explicit objectives, controls, frozen criteria, and machine-checkable verification;
- **cross-provider evaluation** — common contracts, repeated runs, normalized evidence, latency/token/cost observations;
- **agent and tool-use evaluation** — permission boundaries, tool escalation, execution discipline, evaluator gaming, and regressions;
- **regression and release evidence** — reusable suites and evidence for model, prompt, tool, policy, or application changes.

Commercial work is scoped around evaluation outcomes and reproducible evidence rather than commodity task volume.

See [`docs/CAPABILITIES.md`](docs/CAPABILITIES.md).


### Current funding window - 30-day public milestone

AI Evaluation Lab is currently seeking **US $10,000** to execute its next reproducible agent-evaluation milestone. A **US $5,000 partial award** funds the core task-pack, verifier, and cross-model evaluation work.

The ask is tied to defined public engineering outputs rather than unrestricted runway.

[Funding details](FUNDING.md) | [Grant brief](docs/GRANT_BRIEF.md) | [GitHub Sponsors](https://github.com/sponsors/kaulastudies) | [Direct support via PayPal](https://www.paypal.com/paypalme/malayanur92)

---

## Mission

AI Evaluation Lab has two compatible tracks with a clear boundary between them.

### Public-interest evaluation

Open work focused on reproducibility, agent reliability, safety-relevant failure modes, verification, regression, and evaluation methodology.

Outputs may include:

- independently authored synthetic task packs;
- deterministic or machine-checkable verifiers;
- reproducible model/agent runs;
- public Evaluation Records;
- regression suites;
- technical reports;
- open evaluation methodology.

### Private evaluation programs

Fixed-scope work for AI companies and product teams that need independent evaluation of a defined model, agent, workflow, or release.

Private engagements use isolated workspaces and do not automatically become public Lab assets.

---

## Current public-interest program

### Agent Safety Evaluation Program

The next public milestone is a bounded evaluation program for tool-using and increasingly autonomous AI agents.

The program will investigate concrete, testable failure modes such as:

- constraint or permission-boundary violations;
- unsafe or unjustified tool escalation;
- evaluator gaming and reward-hacking-like behavior;
- failures that disappear in one run but return under regression;
- behavioral differences across model/provider configurations under the same task contract.

The goal is **not** to claim broad model safety.

The goal is to produce reproducible evidence about specific observed behaviors under explicit task contracts.

See [`docs/AGENT_SAFETY_PROGRAM.md`](docs/AGENT_SAFETY_PROGRAM.md).

---

## Evaluation model

```text
Task Contract
     |
     v
Isolated Environment
     |
     v
Model / Agent Run
     |
     v
Artifacts + Evidence
     |
     v
Independent Verification
     |
     +--> Human Review when needed
     |       |
     |       +--> Disagreement / Adjudication
     |
     v
Evaluation Record
     |
     v
Regression History
     |
     v
Release Evidence / Research Result
```

Every accepted run becomes a versioned **Evaluation Record**, not just a score.

---

## What exists today

### Alpha v0.1 — Evaluation Records

The first layer established:

- versioned task definitions;
- deterministic verification;
- reviewer decisions;
- disagreement detection;
- adjudication fields;
- canonical SHA-256 record hashing;
- regression linkage;
- provider abstractions;
- synthetic test cases;
- automated tests;
- GitHub Actions CI.

### Alpha v0.2A — Evaluation Operations foundation

The current runtime adds:

- an original Harbor-compatible task package;
- a frozen task contract;
- a deliberately broken negative control;
- a passing reference implementation;
- a separate verifier environment;
- deterministic contract gates;
- local Docker/Harbor execution;
- local Ollama/Inspect execution;
- normalized hashed Evaluation Records;
- CI validation of published evidence;
- a public provenance and IP boundary.

Current public evidence includes:

- **Harbor Oracle:** verifier reward `1.000`, zero exceptions;
- **Ollama `llama3:latest` through Inspect AI:** match accuracy `1.000`;
- **AS-001 cross-provider evidence:** under the same frozen v1.0.0 task contract, Ollama `llama3:latest` produced 0/3 overall passes because of repeated `OUTPUT_WRITE_COUNT_INVALID`, while Groq `openai/gpt-oss-20b` produced 3/3 overall passes; both configurations satisfied the objective and preserved the permission boundary in all three runs.
- canonical public record hashes under [`runs/local/`](runs/local/).

**Important:** these current runs validate the evaluation infrastructure and evidence pipeline. They are not presented as a substantive safety benchmark or a blanket claim about model quality.

### Independent open-source contribution context

Rama Chandra also contributes independently to [MLCommons ModelBench](https://github.com/mlcommons/modelbench). Current public contributions under review include:

- [#1650 - dynamic SUT listing for OpenAI and Together dedicated](https://github.com/mlcommons/modelbench/pull/1650)
- [#1661 - Mistral SUT model-ID handling](https://github.com/mlcommons/modelbench/pull/1661)
- [#1662 - Anthropic refusal and readiness handling](https://github.com/mlcommons/modelbench/pull/1662)

These contributions are separate from AI Evaluation Lab and **do not imply MLCommons sponsorship, partnership, certification, or endorsement** of the Lab.

---

## Why this matters

AI evaluation is increasingly fragmented across benchmark scripts, agent traces, model-provider dashboards, spreadsheets, human review, and one-off release checks.

The Lab is designed to connect those pieces into a reproducible evidence system:

| Layer | Purpose |
|---|---|
| **Task & Evidence** | Define what is being tested and what counts as evidence |
| **Execution** | Run models and agents in reproducible environments |
| **Verification** | Judge observable outcomes independently |
| **Review & Adjudication** | Resolve subjective or conflicting determinations |
| **Regression & Release** | Track failures, fixes, regressions, and release readiness |

The long-term category thesis is described in [`docs/VISION.md`](docs/VISION.md). Public-interest research claims remain deliberately narrower than the long-term business vision.

---

## 30-day public milestone

The proposed Agent Safety Evaluation milestone will produce:

1. **3–5 original safety-relevant agent task packs** with explicit contracts and independently authored synthetic scenarios;
2. execution across **at least three model/provider configurations**;
3. deterministic verification wherever the task permits it;
4. positive and negative controls for each public task pack;
5. hash-valid Evaluation Records and regression lineage;
6. a reusable open regression pack;
7. a public technical report describing observed outcomes, limitations, null results, and reproducibility instructions.

Success is defined by the quality and reproducibility of the evidence—not by finding a predetermined failure.

See [`docs/GRANT_BRIEF.md`](docs/GRANT_BRIEF.md).

---

## Research and evaluation principles

The Lab follows several rules:

- define the task and success criteria before interpreting the result;
- distinguish infrastructure validation from model-performance evidence;
- prefer machine-checkable verification where possible;
- preserve negative and null results;
- record disagreement rather than hiding it;
- make provenance explicit;
- separate public research assets from private customer material;
- never market a narrow evaluation as a general safety certification.

See [`docs/RESEARCH_PRINCIPLES.md`](docs/RESEARCH_PRINCIPLES.md).

---

## Evaluation Record

A record can capture:

- evaluation and task IDs;
- task and rubric version;
- provider, model, and run label;
- prompt and expected behavior;
- raw response;
- reviewer decision;
- verifier decision and evidence;
- disagreement state;
- adjudication result;
- latency, tokens, and cost;
- regression lineage;
- final label and status;
- canonical SHA-256 record hash.

See [`schemas/evaluation-record.schema.json`](schemas/evaluation-record.schema.json).

---

## Low-cost execution philosophy

Evaluation should spend expensive inference only after cheaper evidence has been exhausted.

```text
1. Deterministic verification
2. Existing local models
3. Free / credited providers
4. Paid inference when justified
```

The current stack includes Harbor, Docker, Ollama, Inspect AI, GitHub Actions, and provider adapters.

---

## Public accountability

The Lab publishes technical progress through:

- source commits and pull requests;
- automated tests and CI;
- independently authored synthetic task packages;
- verifier gates;
- roadmap state;
- compact public Evaluation Records;
- reproducible local evidence;
- technical reports that include limitations and null results.

This repository is not a certification service and does not represent a blanket safety guarantee.

---

## Data, provenance, and independence

This public repository is developed from Rama-controlled independent work, public/open-source references used according to their licenses, and synthetic or otherwise authorized material.

Do not commit:

- confidential client or contractor information;
- private task-platform artifacts;
- customer-specific deliverables;
- regulated or sensitive personal data;
- credentials or production secrets;
- materials with uncertain provenance or publication rights.

See [`docs/INDEPENDENCE.md`](docs/INDEPENDENCE.md).

---

## Private evaluation engagements

Commercial work is separately scoped around a defined evaluation decision, workflow, model/agent release, or benchmark need.

Typical engagements include:

- evaluation-readiness reviews;
- model/provider comparisons;
- bounded agent-reliability sprints;
- custom benchmark and verifier engineering;
- regression and release-evidence programs.

A founding pilot may include 20–50 bounded evaluation cases, 2–4 model/configuration variants, deterministic verification where possible, a failure taxonomy, reusable regression assets, and a technical evidence report.

Commercial revenue does not change the evidentiary standard used in public evaluation work, and private customer material does not automatically become public Lab infrastructure.

See [`docs/ENGAGEMENTS.md`](docs/ENGAGEMENTS.md).

---

## Funding

The current public-interest project ask is **US $10,000** for the first substantive Agent Safety Evaluation Program milestone.

A **US $5,000 partial award** can still fund the core task-pack, verifier, and cross-model evaluation work.

Funding supports a defined public project rather than an unbounded claim of startup runway.

See [`FUNDING.md`](FUNDING.md) and [`docs/GRANT_BRIEF.md`](docs/GRANT_BRIEF.md).

Support routes:

- GitHub Sponsors: https://github.com/sponsors/kaulastudies
- Direct international support: https://www.paypal.com/paypalme/malayanur92

## License

Unless otherwise noted, original source code and documentation in this repository are licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE).

Third-party dependencies and referenced external materials remain subject to their respective licenses and terms.

---

## Status

**Alpha v0.2A is complete, and AS-002 is now merged into the public Agent Safety Evaluation Program.**

**RARB v0.1 is merged and CI-green.** Its committed evidence now contains 11 live attempts across five verifier-qualified tasks: 5 `VERIFIED_PASS`, 3 `VERIFIED_FAIL`, and 3 `HOLD`. Configured critical verifier mutations show 0 / 17 escapes, and one of two bounded-repair episodes converted to `VERIFIED_PASS`. The evidence includes one preregistered, source-exact replayable AP-001 `VERIFIED_PASS` from Nebius Token Factory using `nvidia/nemotron-3-super-120b-a12b`. These figures describe the committed RARB evidence set only, not general coding-agent performance.

RARB still records three explicit evidence boundaries: the original AP-001-specific Section 9 sequence as written, repeated multi-model/statistically meaningful benchmarking, and production-scale runtime, reliability, and economic-cost evidence.

Next engineering milestones:

- expand RARB validation across repeated model/provider configurations;
- publish live-provider evidence for AS-002 under its frozen contract;
- normalize all current runs into hash-valid Evaluation Records;
- add complete provider-cost capture and performance normalization;
- add provider provenance and redacted run logging;
- publish the first reproducible cross-provider technical report;
- begin reviewer operations and agreement measurement.

See [`ROADMAP.md`](ROADMAP.md).
