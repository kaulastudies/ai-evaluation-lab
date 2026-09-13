# Public-Interest Grant Brief

## Project

**Reproducible Safety Evaluation Infrastructure for Tool-Using AI Agents**

## Applicant

AI Evaluation Lab — independent engineering lab led by Rama Chandra.

Repository: https://github.com/kaulastudies/ai-evaluation-lab

## Request

**US $10,000 for a 30-day public milestone.**

A **US $5,000 partial award** can still fund the core task-pack, verifier, and cross-model evaluation work.

---

## Problem

Tool-using AI agents increasingly act through code, browsers, APIs, and enterprise systems.

Evaluation remains fragmented across benchmark scores, traces, one-off human review, and vendor-specific tooling.

That makes it difficult to answer basic questions:

- What exactly was tested?
- Was the outcome independently verified?
- Can the failure be reproduced?
- Did a fix actually survive regression?
- Does the same task behave differently across providers?
- What evidence supports a release decision?

---

## Existing proof

AI Evaluation Lab is not starting from a blank document.

The public Alpha already provides:

- versioned Evaluation Records;
- deterministic verifier gates;
- positive and negative controls;
- an original Harbor-compatible task;
- local Harbor/Docker execution;
- local Ollama/Inspect execution;
- canonical SHA-256 record hashing;
- CI validation of published evidence;
- a public provenance boundary.

The current published runs are infrastructure validation. They are not presented as a substantive safety benchmark.

---

## Funded milestone

The grant would fund the Lab's first substantive public Agent Safety Evaluation Program:

- 3–5 independently authored safety-relevant task packs;
- at least three model/provider configurations;
- repeated evaluation where stochasticity matters;
- machine-checkable verification where feasible;
- positive and negative controls;
- public Evaluation Records;
- a reusable regression pack;
- a public technical report with limitations and null findings.

Evaluation themes include permission-boundary adherence, tool escalation, evaluator gaming, reward-hacking-like behavior, regression after fixes, and cross-provider behavioral variation.

---

## Why this is public-interest infrastructure

The work produces reusable public evaluation assets rather than a private product demo.

Researchers and engineering teams should be able to inspect:

- the task contract;
- the verifier;
- the controls;
- the evidence model;
- the run result;
- the regression lineage;
- the limitations.

The Lab's commercial work is separately scoped and does not control the conclusions of grant-funded public evaluation.

---

## Budget

| Category | Amount |
|---|---:|
| Model/API/compute | $3,000 |
| Task and verifier engineering | $2,500 |
| Isolated execution / CI / storage | $1,500 |
| Regression engineering | $1,250 |
| Analysis and public report | $1,000 |
| Artifact retention / operations | $750 |
| **Total** | **$10,000** |

---

## Completion criteria

At the end of the milestone, a reviewer should be able to verify that:

- task definitions are versioned;
- provenance is documented;
- controls exist;
- verifier behavior is tested;
- at least three configurations were evaluated;
- public records are hash-valid;
- regressions can be rerun;
- results include limitations and null findings;
- claims do not exceed the evidence.

---

## Long-term relevance

The immediate project is intentionally narrow.

If successful, the same evidence model can support larger independent evaluation programs across coding agents, browser agents, voice agents, enterprise agents, and other consequential AI workflows.

The Lab's long-term ambition does not change the standard for the first milestone:

> **Build evidence before claims.**
