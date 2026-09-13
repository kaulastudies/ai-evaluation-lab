# Fund AI Evaluation Lab

## Current public-interest project

AI Evaluation Lab is seeking **US $10,000** to execute a defined 30-day public milestone:

> **Reproducible Safety Evaluation Infrastructure for Tool-Using AI Agents**

This is a project grant request for concrete public outputs. It is not a claim of general model safety and it is not an unrestricted request to fund startup runway.

A **US $5,000 partial award** would still fund the core task-pack, verifier, and cross-model evaluation milestone.

---

## Why fund this now

The core evaluation infrastructure already exists.

The public Alpha includes:

- versioned Evaluation Records;
- deterministic verifier gates;
- positive and negative controls;
- an original Harbor-compatible task;
- local Harbor/Docker execution;
- local Ollama/Inspect execution;
- canonical SHA-256 evidence records;
- CI validation of published evidence;
- an explicit provenance and independence boundary.

Current published runs validate the infrastructure and evidence pipeline. They are not presented as substantive safety results.

Funding would move the Lab from **infrastructure proof** to its first **substantive public agent-evaluation program**.

---

## 30-day deliverables

The funded milestone will produce:

1. **3–5 independently authored safety-relevant agent task packs**;
2. explicit task contracts and success criteria;
3. positive and negative controls;
4. execution across **at least three model/provider configurations**;
5. deterministic or machine-checkable verification wherever feasible;
6. hash-valid public Evaluation Records;
7. a reusable regression pack;
8. a public technical report describing observed outcomes, limitations, and null results;
9. reproducibility instructions from a clean environment.

Candidate failure modes include permission-boundary violations, unjustified tool escalation, evaluator gaming, reward-hacking-like behavior, and regressions after a previously passing fix.

The project does not assume those failures will occur. Null findings are valid outcomes and will be reported.

---

## Budget

| Category | Amount | Purpose |
|---|---:|---|
| Model/API/compute | $3,000 | Cross-provider and repeated evaluation runs |
| Task + verifier engineering | $2,500 | Original task contracts, controls, and machine-checkable verifiers |
| Isolated execution infrastructure | $1,500 | CI, sandboxing, hosting, storage, and reproducibility |
| Regression engineering | $1,250 | Repeatable suites, lineage, and evidence normalization |
| Analysis + public report | $1,000 | Technical analysis, documentation, and reproducibility write-up |
| Artifact retention / operations | $750 | Public evidence storage and operational costs |
| **Total** | **$10,000** | |

If donated compute or credits reduce one category, the saved amount will remain allocated to the same public evaluation milestone or be returned/re-scoped according to funder requirements.

---

## Success criteria

The milestone is successful if:

- every public task has a versioned task contract;
- every task has documented provenance;
- every task has a verifier and control strategy;
- at least three model/provider configurations are evaluated;
- every published Evaluation Record validates its canonical hash;
- regressions can be rerun from documented instructions;
- the report distinguishes observed evidence from interpretation;
- negative and null results are retained rather than filtered out.

Success is **not** defined as demonstrating that a model is unsafe.

---

## Public accountability

Progress is visible through:

- GitHub commits and pull requests;
- automated CI gates;
- `ROADMAP.md`;
- original synthetic task packages;
- versioned Evaluation Records;
- public regression artifacts;
- a final technical report.

The operating principle is:

> **Build evidence before claims.**

---

## Independence

Public grant-funded work remains governed by the repository's provenance boundary.

It will not include:

- confidential customer or contractor material;
- private benchmark artifacts;
- restricted task-platform material;
- real sensitive personal data;
- customer-specific foreground deliverables;
- credentials or production secrets.

See [`docs/INDEPENDENCE.md`](docs/INDEPENDENCE.md).

---

## Commercial work is separate

AI Evaluation Lab also offers fixed-scope private evaluation pilots.

Commercial engagements use isolated customer workspaces and written scopes. A customer payment does not purchase control of public research conclusions, public task results, or the Lab's general evaluation methodology.

---

## Support routes

### GitHub Sponsors

https://github.com/sponsors/kaulastudies

### Direct international support

https://www.paypal.com/paypalme/malayanur92

For formal grants or sponsored research, the Lab can use the payment and reporting process required by the funder.
