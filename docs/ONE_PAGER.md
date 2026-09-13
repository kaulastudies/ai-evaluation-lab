# AI Evaluation Lab — One Page

## Reproducible evidence for AI systems and agents

AI Evaluation Lab is an independent engineering lab building provider-neutral evaluation infrastructure for models and agents.

### The problem

As AI agents gain the ability to write code, call tools, browse, and act across real workflows, evaluation is still fragmented across one-off benchmarks, traces, spreadsheets, and vendor-specific dashboards.

A score alone does not answer:

- what exactly was tested;
- what evidence was produced;
- whether a result can be independently verified;
- whether a failure returns after a fix;
- whether the same behavior appears across providers;
- whether the evidence is strong enough to inform a release decision.

### The system

**Task Contract → Isolated Run → Evidence → Verification → Review → Evaluation Record → Regression → Release Evidence**

### Working today

- versioned Evaluation Records;
- deterministic verification;
- disagreement/adjudication model;
- regression linkage;
- Harbor-compatible task runtime;
- independent verifier environment;
- negative and positive controls;
- local Docker + Harbor execution;
- Ollama + Inspect AI baseline;
- canonical record hashing;
- CI-gated public evidence.

Current Harbor and Ollama/Inspect runs validate the infrastructure pipeline. They are not presented as a substantive model-safety benchmark.

### Public-interest program

The next milestone is an **Agent Safety Evaluation Program** focused on concrete, testable failure modes in tool-using agents:

- permission and constraint violations;
- unjustified tool escalation;
- evaluator gaming / reward-hacking-like behavior;
- regression after fixes;
- behavior differences across model/provider configurations.

### 30-day funded milestone

A **$10,000 project grant** would fund:

- 3–5 original safety-relevant task packs;
- at least 3 model/provider configurations;
- machine-checkable verification where feasible;
- positive and negative controls;
- hash-valid Evaluation Records;
- an open regression pack;
- a public technical report with limitations and null results.

A $5,000 partial award can fund the core task-pack, verifier, and cross-model milestone.

### Research standard

The Lab commits to:

- predeclared task contracts;
- evidence before interpretation;
- preservation of negative/null results;
- explicit provenance;
- reproducibility;
- no blanket safety or certification claims.

### Commercial independence

Private evaluation pilots are separately scoped and isolated. Commercial revenue does not buy control over public research conclusions.

### Public proof

Repository: https://github.com/kaulastudies/ai-evaluation-lab

Published evidence: `runs/local/`

Grant brief: `docs/GRANT_BRIEF.md`

Research principles: `docs/RESEARCH_PRINCIPLES.md`
