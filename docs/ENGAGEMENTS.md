# Private Evaluation Engagements

AI Evaluation Lab offers fixed-scope private evaluation programs for AI companies, product teams, infrastructure providers, and organizations deploying AI into real workflows.

Commercial work is scoped around **evaluation outcomes and reproducible evidence**, not around commodity task volume.

## Typical engagement types

### Evaluation Readiness Review

For a team that has an AI workflow but no rigorous evaluation system yet.

Typical outputs:

- evaluation-risk map;
- task-contract design;
- verifier opportunities;
- evidence requirements;
- recommended regression strategy;
- prioritized evaluation plan.

### Model / Provider Comparison

For teams choosing between model or provider configurations.

Typical outputs:

- frozen common task contract;
- repeated runs;
- normalized evidence;
- cost / latency observations;
- failure taxonomy;
- reproducibility notes;
- technical recommendation boundaries.

The Lab reports observed tradeoffs rather than declaring a universal “best model.”

### Agent Reliability Sprint

For tool-using or workflow-executing agents.

Typical outputs:

- 20–50 bounded evaluation cases;
- positive and negative controls;
- tool-boundary tests;
- verifier-backed outcomes;
- execution traces;
- failure taxonomy;
- regression pack;
- evidence report.

### Release Regression Program

For teams that need to know whether an AI-system update reintroduces known failures.

Typical outputs:

- reusable regression suite;
- rerun protocol;
- versioned evidence;
- pass/fail gates;
- change log;
- release evidence summary.

### Custom Benchmark / Verifier Engineering

For teams that need domain-specific evaluation infrastructure.

Typical outputs can include:

- task packs;
- schemas;
- deterministic verifiers;
- reference implementations;
- synthetic fixtures;
- CI gates;
- Evaluation Record normalization.

## Engagement principles

Every engagement follows five rules:

1. scope the decision before building the evaluation;
2. freeze success criteria before interpreting results;
3. separate customer-confidential material from public Lab assets;
4. preserve negative and null findings;
5. distinguish observed evidence from broader interpretation.

## Isolation and provenance

Private engagements use isolated workspaces.

Customer data, credentials, restricted benchmark material, and customer-specific work product are not committed to the public repository unless publication rights are explicit and separately agreed.

See [`INDEPENDENCE.md`](INDEPENDENCE.md).

## Founding-pilot stage

The Lab is currently in a founding-pilot stage.

Early engagements are intentionally bounded so both sides can evaluate:

- technical fit;
- evidence quality;
- reproducibility;
- working process;
- repeat demand.

Larger managed programs and continuous evaluation are planned after repeated pilot evidence.
