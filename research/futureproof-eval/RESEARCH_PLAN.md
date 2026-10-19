# FutureProof Eval: quantum-verification pilot (proposal)

**Status:** experimental research plan; no quantum-hardware validation claimed.  
**Parent:** [AI Evaluation Lab](../../README.md).  
**Existing work:** retain and reuse the repository's Qiskit SDK 2.x CI workflow and current reproducibility conventions.

## Research question

Can a provider-neutral evaluator catch incorrect claims about single-qubit measurement outcomes, while controlling statistical false rejection and recording enough provenance to replay the verdict?

## First benchmark slice

- Define ideal Born-rule probabilities for an `Ry(theta)` gate applied to `|0⟩`.
- Include prepared states with known expectations, plus deliberately biased observations as negative controls.
- Record the circuit specification, shots, counts, backend/simulator version, seed when applicable, and verifier version.
- Compare counts to the ideal reference using a **predeclared statistical decision procedure**; do not treat a fixed absolute tolerance as a calibrated test.
- Run across at least two independent implementations before introducing hardware.
- Track false-positive/false-negative behavior through repeated seeded trials and report confidence intervals.
- Include a classical simulation baseline, execution time, shots and provider costs where known.
- Produce canonical JSON evidence and SHA-256 digests; hashes establish content identity, not authenticity.

## Acceptance criteria

1. Deterministic fixture tests cover valid, invalid, boundary and intentionally erroneous counts.
2. A frozen spec fixes significance level, seed policy, shot regimes and evaluation metric before testing.
3. Known-good controls pass at the expected empirical rejection rate, with appropriate statistical uncertainty.
4. Known-bad controls are detected at measured rates, without calling this quantum advantage.
5. Identical input evidence generates identical digests; changes to counts change the digest.
6. The CI remains green without network access or paid QPU credentials.

## Explicit non-claims

No quantum advantage, device certification, hardware reproducibility, fault tolerance or general AI safety guarantee is established by this pilot.

## Funding alignment

The repository currently advertises a **$10,000 / 30-day** public agent-evaluation milestone (and $5,000 partial-award scope). This exploratory quantum track is **not a replacement funding request**. Public applications should preserve that stated ask unless a separately scoped proposal and budget are approved.

## Next milestones

- Incorporate calibrated shot-aware tests and independent simulation checks.
- Establish failure taxonomy for quantum measurements and AI-authored quantum code.
- Approach India's quantum-computing thematic hub for collaborator/eligibility advice.
- Publish a short, reproducible methods note with negative findings included.
