# Agent Safety Evaluation Program

## Purpose

The Agent Safety Evaluation Program is AI Evaluation Lab's first bounded public-interest evaluation program.

It is designed to produce reproducible evidence about specific behaviors of tool-using AI agents under explicit task contracts.

It is **not** intended to certify that a model or agent is generally safe.

---

## Research question

Can safety-relevant agent behaviors be evaluated in a way that is:

- provider-neutral;
- reproducible;
- independently verifiable;
- regression-aware;
- explicit about uncertainty and disagreement;
- useful to researchers and engineering teams?

---

## Initial evaluation themes

The first task packs will focus on a small set of observable behaviors.

### 1. Permission and constraint adherence

Does an agent remain within explicit task, data, or tool boundaries?

### 2. Tool escalation

Does an agent invoke higher-impact tools or actions when a lower-impact path is sufficient, or when escalation is explicitly disallowed?

### 3. Evaluator gaming

Can an agent obtain a passing surface-level result while violating the intended task contract?

### 4. Regression after repair

When a failure is fixed, does the fix remain stable across reruns, nearby scenarios, and provider/model changes?

### 5. Cross-provider behavioral variation

Under the same task contract, do different model/provider configurations fail in materially different ways?

These themes are hypotheses for evaluation design, not claims that any specific model exhibits the failure.

---

## Task-pack standard

Each public task pack should contain:

- a stable task ID and version;
- a written task contract;
- explicit success and failure criteria;
- synthetic or otherwise publishable inputs;
- provenance notes;
- an isolated execution environment where appropriate;
- a negative control;
- a reference or positive control;
- a verifier;
- a documented reward/decision rule;
- expected artifacts;
- reproducibility instructions.

Where a deterministic verifier is impossible, the task should document the human-review rubric and disagreement process.

---

## Evaluation pipeline

```text
Research Question
      |
      v
Task Contract
      |
      v
Controls
      |
      v
Isolated Execution
      |
      v
Artifacts
      |
      v
Independent Verification
      |
      +--> Human Review if needed
      |
      v
Evaluation Record
      |
      v
Regression Rerun
      |
      v
Public Result + Limitations
```

---

## 30-day milestone

The first funded milestone targets:

- 3–5 original safety-relevant task packs;
- at least three model/provider configurations;
- repeated runs where stochasticity matters;
- deterministic verification wherever feasible;
- hash-valid public Evaluation Records;
- an open regression pack;
- a technical report.

The report will include:

- task definitions;
- provider/model configuration;
- observed results;
- verifier behavior;
- disagreements;
- failures to reproduce;
- negative/null findings;
- limitations;
- follow-up hypotheses.

---

## What counts as success

The program succeeds if the evidence is rigorous and reproducible.

It does **not** require finding a dramatic safety failure.

A clean result, a null result, or a result showing that the task design was inadequate can all be valuable if they are documented honestly.

---

## What the program will not claim

The program will not claim:

- that one task proves a model is safe or unsafe;
- that a passing run implies production readiness;
- that the Lab provides certification;
- that synthetic tasks perfectly predict real-world behavior;
- that a single score captures all relevant risk.

---

## Independence and conflicts

Public program results should be reported according to the predeclared task contract and evidence.

If a company financially supports a public task, that support does not grant the company editorial control over the result.

Private customer evaluations remain private unless there is explicit written permission to publish them.

See [`INDEPENDENCE.md`](INDEPENDENCE.md) and [`RESEARCH_PRINCIPLES.md`](RESEARCH_PRINCIPLES.md).
