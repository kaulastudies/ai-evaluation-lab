# Research and Evaluation Principles

AI Evaluation Lab uses the following principles for public evaluation work.

## 1. Evidence before claims

Claims should be no broader than the evidence that supports them.

A successful infrastructure test is not a safety benchmark. A passing benchmark task is not a general safety guarantee.

## 2. Predeclare the contract

Define the task, version, success criteria, failure criteria, expected artifacts, and verifier before interpreting the result.

If those rules change, create a new task version.

## 3. Prefer independent verification

Where possible, verify observable outcomes from artifacts or environment state rather than relying on the evaluated model's own explanation.

## 4. Use controls

Public task packs should include a negative control and a reference/positive control when feasible.

A verifier that cannot distinguish known-bad from known-good behavior is not ready to support a substantive conclusion.

## 5. Preserve null and negative results

Do not discard a result because it is uninteresting.

If no failure appears, report that. If a task is inconclusive, report that. If the verifier is weak, report that.

## 6. Separate observation from interpretation

Evaluation Records should preserve what happened.

Technical reports should distinguish:

- observed evidence;
- verifier decision;
- reviewer interpretation;
- broader hypothesis.

## 7. Treat disagreement as data

When reasonable reviewers disagree, preserve the disagreement and adjudication path.

Do not force consensus into the raw record.

## 8. Make provenance explicit

Public work should use independently authored synthetic material, appropriately licensed public references, or material with explicit publication authority.

See [`INDEPENDENCE.md`](INDEPENDENCE.md).

## 9. Minimize benchmark leakage

Do not publish hidden benchmark answers or restricted task artifacts.

Original Lab tasks should be independently authored.

## 10. Avoid safety theater

The Lab will not market narrow tests as comprehensive certification.

It will not use the words "safe", "secure", "aligned", or "production-ready" as blanket conclusions unless a specifically defined claim is supported by the evaluation.

## 11. Preserve commercial independence

A sponsor or customer does not purchase a desired result.

Public research conclusions follow the evidence and stated methodology.

Private engagements are scoped separately and remain subject to their own confidentiality terms.

## 12. Reproducibility is part of the result

A public result should include enough information for a competent third party to understand what was run and, where licensing and infrastructure allow, reproduce the evaluation.

---

## Current maturity

The existing Harbor and Ollama/Inspect public runs validate the Lab's execution and evidence pipeline.

The Agent Safety Evaluation Program is the next step from infrastructure validation to substantive, safety-relevant evaluation.
