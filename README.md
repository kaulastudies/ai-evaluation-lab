# AI Evaluation Lab

**Independent infrastructure for reproducible evaluation of AI systems and agents.**

This repository is Rama Chandra's public engineering workspace for evaluation tooling that makes model and agent decisions inspectable: tasks, evidence, model runs, deterministic verification where possible, independent review, disagreement, adjudication, regression history, and release evidence.

> Status: **Alpha v0.2 - Evaluation Operations foundation.** The repository ships a runnable synthetic record pipeline plus an original verifier-backed task package and CI gates. This is not a certification service or production safety guarantee.

## Core flow

```text
Task
  -> Evidence / expected behavior
  -> Model or agent run
  -> Artifacts
  -> Independent verification
  -> Review
  -> Disagreement / adjudication when needed
  -> Evaluation Record
  -> Regression
  -> Release evidence
```

Every accepted run becomes a versioned **Evaluation Record** rather than a loose score.

## Alpha v0.1

The first alpha includes:

- a versioned task format;
- an offline mock provider;
- configuration-driven Gemini and OpenAI-compatible adapters;
- deterministic verification;
- independent-review fields;
- disagreement detection;
- synthetic adjudication examples;
- immutable record hashing;
- regression linkage;
- five synthetic evaluation tasks;
- generated JSON evaluation records;
- unit tests and GitHub Actions CI.

Run the tests:

```bash
python -m unittest discover -s tests -v
```

Run the offline demo:

```powershell
$env:PYTHONPATH = "src"
python -m eval_lab.alpha_demo
```

## Evaluation Operations v0.2

The next layer adds task contracts, reference/negative controls, independent verifier gates, local agent execution, and normalized evidence across runners.

See:

- `docs/EVALUATION_OPERATIONS.md`
- `docs/RESOURCE_PLAN.md`
- `docs/INDEPENDENCE.md`
- `ROADMAP.md`

The intended low-cost stack is deterministic verification first, then existing local Ollama models, then free/credited providers, then paid inference only when justified.

The first original runtime task is at ops/tasks/route-policy-repair, with a frozen instruction contract, intentionally broken starting state, reference solution, separate verifier, and negative/positive controls.

## Evaluation Record

A record captures evaluation/task IDs, rubric version, provider/model, raw response, reviewer decision, verifier evidence, disagreement, adjudication, latency/token/cost fields, regression linkage, final status, and a canonical SHA-256 hash.

See `schemas/evaluation-record.schema.json`.

## Data and IP boundary

This public repository is developed from Rama-controlled work, public/open-source references used according to their licenses, and synthetic/public data.

Do not commit client/contractor confidential information, private task-platform artifacts, customer-specific deliverables, regulated data, credentials, production secrets, or material with uncertain provenance.

See `docs/INDEPENDENCE.md`.

## Commercial direction

The Lab supports public infrastructure/sponsored research and separately scoped private evaluation pilots. Private customer work belongs in isolated customer workspaces, not this public repository.

## Support the Lab

The current public-infrastructure target is **US $5,000**.

- GitHub Sponsors: https://github.com/sponsors/kaulastudies
- Direct support: https://www.paypal.com/paypalme/malayanur92
- Funding details: [FUNDING.md](FUNDING.md)

Support does not grant equity, ownership, exclusive IP, private repository access, confidential data access, contributor permissions, or consulting unless separately agreed in writing.

## Security and privacy

Read `SECURITY.md` before using the Lab with non-public data. Do not send confidential material to a provider until its current data handling, retention, and training terms have been reviewed for that project.
