# Capabilities

AI Evaluation Lab is an independent, provider-neutral engineering lab for reproducible AI-system and agent evaluation.

The Lab is built around one operating principle:

> **Build evidence before claims.**

## Core capabilities

### Task-contract and verifier engineering

Design evaluation tasks with:

- explicit objectives;
- allowed and prohibited operations;
- frozen success criteria;
- positive and negative controls;
- deterministic or machine-checkable verification where feasible;
- versioned contracts and provenance.

### Cross-provider evaluation

Run the same frozen task contract across multiple model or provider configurations and compare:

- objective completion;
- constraint adherence;
- tool-use behavior;
- output validity;
- trace behavior;
- latency;
- token usage;
- estimated cost;
- reproducibility.

Comparisons are reported as observed evidence under a defined contract, not as blanket claims about a provider or model.

### Agent and tool-use evaluation

Current public work focuses on failure modes that become important when models can act through tools, files, APIs, browsers, code, and enterprise workflows.

Examples include:

- permission-boundary violations;
- unjustified tool escalation;
- invalid execution sequences;
- evaluator gaming;
- repeatability failures;
- regressions after repair.

### Regression and release evidence

Evaluation results can be converted into reusable regression assets so a previously observed failure can be rerun after:

- model changes;
- prompt changes;
- tool changes;
- policy changes;
- application releases.

The goal is to make evaluation part of release engineering rather than a one-time report.

### Evaluation-record normalization

Accepted runs can be normalized into versioned Evaluation Records containing:

- task and rubric versions;
- provider and model identity;
- observable evidence;
- verifier outcomes;
- human review where needed;
- disagreement/adjudication state;
- latency, token and cost information;
- regression lineage;
- canonical SHA-256 hashes.

## Delivery modes

The Lab currently supports two bounded modes:

1. **Public-interest evaluation** — independently authored, reproducible research artifacts published openly.
2. **Private evaluation programs** — fixed-scope engagements for a defined model, agent, workflow, release, or benchmark.

Private customer material is isolated and does not automatically become public Lab infrastructure.

## What the Lab is not

AI Evaluation Lab is not positioned as:

- a general-purpose annotation marketplace;
- a staffing marketplace;
- a leaderboard-only benchmark site;
- a blanket safety-certification authority.

The Lab is building a technical evidence layer for AI evaluation and release decisions.
