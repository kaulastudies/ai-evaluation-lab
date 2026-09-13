# AI Evaluation Lab

## Reproducible evidence for AI systems and agents

**AI Evaluation Lab is an independent engineering lab building provider-neutral infrastructure to test, verify, compare, and reproduce the behavior of AI systems and agents.**

As AI systems become more capable of acting through tools, code, browsers, APIs, and enterprise workflows, evaluation has to become more than a leaderboard score. Teams and researchers need evidence that is versioned, inspectable, reproducible, and useful for identifying regressions before deployment.

The Lab is building that evidence layer.

> **Operating principle:** build evidence before claims.

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
- canonical public record hashes under [`runs/local/`](runs/local/).

**Important:** these current runs validate the evaluation infrastructure and evidence pipeline. They are not presented as a substantive safety benchmark or a blanket claim about model quality.

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

## Commercial evaluation pilots

Commercial work is separately scoped.

A founding pilot can include:

- 30–50 evaluation tasks;
- one defined workflow;
- 2–4 model or configuration variants;
- deterministic verification where possible;
- independent human review where necessary;
- failure taxonomy;
- regression pack;
- technical evidence report.

Commercial revenue does not change the evidentiary standard used in public evaluation work.

---

## Funding

The current public-interest project ask is **US $10,000** for the first substantive Agent Safety Evaluation Program milestone.

A **US $5,000 partial award** can still fund the core task-pack, verifier, and cross-model evaluation work.

Funding supports a defined public project rather than an unbounded claim of startup runway.

See [`FUNDING.md`](FUNDING.md) and [`docs/GRANT_BRIEF.md`](docs/GRANT_BRIEF.md).

Support routes:

- GitHub Sponsors: https://github.com/sponsors/kaulastudies
- Direct international support: https://www.paypal.com/paypalme/malayanur92

---

## Status

**Alpha v0.2A is complete.**

Next engineering milestones:

- live multi-provider validation;
- the first original safety-relevant agent task pack;
- cost/performance normalization;
- provider provenance and redacted run logging;
- a public cross-provider evaluation report;
- reviewer operations and agreement measurement.

See [`ROADMAP.md`](ROADMAP.md).
