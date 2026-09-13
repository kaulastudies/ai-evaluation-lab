# AI Evaluation Lab

## The evidence layer for AI systems and agents

**AI Evaluation Lab is an independent emerging lab building reproducible infrastructure to test, verify, compare, and govern AI behavior before it reaches production.**

Models are becoming systems. Systems are becoming agents. Agents are beginning to act.

The next infrastructure problem is not simply generating better outputs. It is producing **credible evidence that an AI system behaved as expected, under a known task contract, with a reproducible verifier, and with enough history to make a release decision.**

That is the layer we are building.

> **North Star:** become neutral evaluation infrastructure for the trillion-dollar AI economy.

This is an ambition and category thesis, not a claim that the Lab currently has a trillion-dollar valuation.

---

## The thesis

AI does not need another leaderboard.

It needs an operating layer that can answer:

- What exactly was tested?
- Against which task and criteria version?
- Which model or agent produced the result?
- What evidence was generated?
- What did an independent verifier observe?
- Where did reviewers disagree?
- What changed between a failed run and a passing regression?
- Can the result be reproduced?
- Is there enough evidence to ship?

AI Evaluation Lab turns those questions into structured, machine-readable evaluation operations.

```text
Task Contract
     |
     v
Environment
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
     +--> Human Review
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
Release Evidence
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

### Alpha v0.2A — Evaluation Operations

The current runtime adds:

- an original Harbor-compatible task package;
- a frozen task contract;
- a deliberately broken negative control;
- a passing reference implementation;
- a separate verifier environment;
- deterministic contract gates;
- local Docker/Harbor execution;
- local Ollama/Inspect evaluation;
- normalized hashed Evaluation Records;
- CI validation of published evidence;
- a public provenance and IP boundary.

Current public evidence includes:

- **Harbor Oracle:** verifier reward `1.000`, zero exceptions;
- **Ollama `llama3:latest` through Inspect AI:** match accuracy `1.000`;
- canonical public record hashes under [`runs/local/`](runs/local/).

See:

- [`ROADMAP.md`](ROADMAP.md)
- [`docs/VISION.md`](docs/VISION.md)
- [`docs/EVALUATION_OPERATIONS.md`](docs/EVALUATION_OPERATIONS.md)
- [`docs/INDEPENDENCE.md`](docs/INDEPENDENCE.md)
- [`runs/local/`](runs/local/)

---

## The emerging category

AI evaluation is moving from one-off benchmarking toward continuous operational infrastructure.

The Lab is designed around five layers:

| Layer | Purpose |
|---|---|
| **Task & Evidence** | Define what is being tested and what counts as evidence |
| **Execution** | Run models and agents across reproducible environments |
| **Verification** | Judge observable outcomes independently |
| **Review & Adjudication** | Resolve subjective or conflicting determinations |
| **Regression & Release** | Track failures, fixes, regressions, and release readiness |

Over time these layers can support an **Evaluation Operations System** used by AI teams, model providers, agent builders, regulated organizations, research groups, and independent evaluators.

---

## Trillion-scale ambition

AI systems may mediate enormous amounts of economic activity.

If AI becomes embedded in software engineering, finance, healthcare, logistics, research, operations, and autonomous digital work, then evaluation cannot remain an occasional manual exercise. It becomes infrastructure.

Our long-term thesis is therefore simple:

> **The larger the AI economy becomes, the more valuable independent, reproducible evidence about AI behavior becomes.**

We are not presenting a current valuation claim.

We are building with the ambition that evaluation, verification, regression, provenance, and release evidence can become a foundational control layer for an AI economy measured in trillions of dollars.

Read the full thesis in [`docs/VISION.md`](docs/VISION.md).

---

## From open infrastructure to a durable business

The Lab is being built as a permanent technical institution with several compatible economic layers:

```text
Open evaluation infrastructure
        |
        v
Sponsored public evaluation work
        |
        v
Fixed-scope private evaluation pilots
        |
        v
Managed evaluation programs
        |
        v
Evaluation Operations platform / API
        |
        v
Continuous regression + release evidence
        |
        v
Evaluation network and specialist ecosystem
```

Public infrastructure remains reusable and inspectable.

Private customer work belongs in isolated workspaces with explicit scope, permissions, and data controls.

---

## Founding evaluation pilots

The first commercial engagements are intentionally narrow.

A founding pilot can include:

- 30–50 evaluation tasks;
- one defined workflow;
- 2–4 model or configuration variants;
- deterministic verification where possible;
- independent human review where necessary;
- failure taxonomy;
- regression pack;
- technical evidence report.

The objective is not to produce a vanity score.

The objective is to leave the engineering team with **reusable evidence and regression assets**.

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
- original synthetic task packages;
- verifier gates;
- roadmap state;
- compact public Evaluation Records;
- reproducible local evidence.

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

## Support the Lab

The current public-infrastructure target is **US $5,000**.

Support can fund verifier runs, model comparisons, original synthetic tasks, mini benchmark packs, compute, CI/sandbox infrastructure, documentation, and the next public evaluation milestones.

- **GitHub Sponsors:** https://github.com/sponsors/kaulastudies
- **Direct international support:** https://www.paypal.com/paypalme/malayanur92
- **Funding details:** [`FUNDING.md`](FUNDING.md)

Support does not grant equity, ownership, exclusive IP, private repository access, confidential data access, contributor permissions, or consulting unless separately agreed in writing.

---

## Status

**Alpha v0.2A is complete.**

Next: multi-provider evaluation, cost/performance normalization, provider provenance, redacted run logging, reviewer operations, and the first public cross-provider evaluation report.

See [`ROADMAP.md`](ROADMAP.md).
