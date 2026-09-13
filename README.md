# AI Evaluation Lab

**Independent infrastructure for reproducible evaluation of AI systems and agents.**

This repository is the public engineering workspace for Rama Chandra's AI Evaluation Lab. The goal is to make evaluation work inspectable: tasks, evidence, model runs, independent review, deterministic verification where possible, disagreement, adjudication, accepted evaluation records, and regression history.

> Status: **Alpha v0.1**. The repository ships a runnable synthetic end-to-end evaluation pipeline. It is not a certification service and should not be treated as a production safety guarantee.

## Why this exists

Model demos are easy to produce. Reliable release decisions are harder.

```text
Task
  -> Evidence / expected behavior
  -> Model run
  -> Independent review
  -> Deterministic verification
  -> Disagreement detection
  -> Adjudication
  -> Accepted evaluation record
  -> Regression rerun
  -> Release evidence
```

Every accepted run becomes a versioned **Evaluation Record** rather than a loose score.

## Alpha v0.1

The first alpha includes:

- a versioned task format;
- provider abstraction;
- an offline mock provider for fully reproducible demos;
- configuration-driven adapters for Gemini and OpenAI-compatible APIs;
- deterministic verification rules;
- independent-review fields;
- disagreement detection;
- synthetic adjudication examples;
- immutable record hashing;
- regression linkage;
- five synthetic evaluation tasks;
- generated JSON evaluation records;
- unit tests and GitHub Actions CI.

The five synthetic cases cover:

1. clean pass;
2. unsupported factual claim;
3. correct substance with an output-format defect;
4. reviewer/verifier disagreement followed by adjudication;
5. a failed response followed by a regression pass.

## Quick start

Python 3.12+ is recommended.

```bash
python -m unittest discover -s tests -v
```

Run the full offline alpha:

```powershell
$env:PYTHONPATH = "src"
python -m eval_lab.alpha_demo
```

The demo writes evaluation records to `runs/alpha/`.

## Optional live providers

The core Alpha works with no paid API and no network access.

For live runs, set only the providers you intend to use. Never commit API keys.

Adapter shapes included in Alpha:

- Gemini through the Google Generative Language REST API;
- Groq, OpenRouter, Cerebras and Fireworks through OpenAI-compatible endpoints;
- Sarvam remains behind a configuration boundary until the exact production endpoint/model contract is selected.

The provider is deliberately separate from the evaluation logic. A model provider can change without changing the task, verifier, reviewer or accepted-record schema.

## Evaluation Record

A record captures:

- evaluation and task IDs;
- task and rubric version;
- provider/model/run label;
- raw response;
- reviewer decision and reason;
- verifier decision and evidence;
- disagreement state;
- adjudication result when required;
- latency/token/cost fields when available;
- regression linkage;
- final status;
- canonical SHA-256 record hash.

See `schemas/evaluation-record.schema.json`.

## Data boundary

Alpha v0.1 uses only synthetic examples. No Handshake, Fieldborne, hospital, client, patient, proprietary benchmark, or confidential task data is included.

## Commercial direction

The intended operating model is a compact evaluation engineering lab rather than a high-headcount annotation marketplace:

```text
Client / research project
        -> Work package
        -> Evaluation tasks
        -> Model runs
        -> Independent review
        -> Verification
        -> Adjudication
        -> Regression suite
        -> Release evidence / technical report
```

Early paid work can be delivered as narrow, fixed-scope evaluation pilots. The software layer should progressively absorb task management, evidence provenance, model execution, reviewer separation, adjudication, regression testing and reporting.

## Support

If this work is useful, you can support Rama Chandra's independent technical work:

- GitHub Sponsors: https://github.com/sponsors/kaulastudies
- Direct support: https://www.paypal.com/paypalme/malayanur92

Funding supports public evaluation infrastructure, testing, documentation, hosting and maintenance. It does not automatically purchase consulting, private repository access, contributor permissions, confidential data access or exclusive IP rights.

## Security and privacy

Read `SECURITY.md` before using the Lab with non-public data. Free model tiers can have different data-use terms from paid enterprise/API plans. Do not send confidential customer material to a provider until its current data handling and retention terms have been reviewed for that project.
