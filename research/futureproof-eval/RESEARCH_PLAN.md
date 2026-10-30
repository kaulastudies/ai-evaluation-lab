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

- Freeze a repeated-trial protocol covering shot regimes, false-positive/false-negative rates and confidence intervals; complete this before making calibrated decision claims. Current Wilson intervals remain uncorrected screening only.
- Extend the independent ideal-state cross-check to seeded sampling and publish all outcomes, including failures. The ten-angle Qiskit 2.6.1 ideal-state check now runs in CI.
- Establish failure taxonomy for quantum measurements and AI-authored quantum code.
- Approach India's quantum-computing thematic hub for collaborator/eligibility advice.
- Publish a short, reproducible methods note with negative findings included.

## Readiness review — 30 October 2026

- The existing draft PR #26 contains the illustrative tolerance verifier, Wilson screening CLI and local HTTP API. These remain distinct from Quantum Agent Gate's execution policy checks.
- Rejected inputs now include duplicate JSON keys, boolean angles/counts, non-finite and unrepresentable angles, malformed IDs and unexpected fields. Tests check that invalid HTTP input returns 400 and leaves the service responsive.
- The original example still reports three cases and one review flag. No original evidence, examples or historical result records were rewritten.
- The independent simulator check covers ideal single-qubit probabilities, not repeated-sampling calibration. Provider authenticity, multiple-testing control and hardware evidence remain open.
- Security remediation in [PR #34](https://github.com/kaulastudies/ai-evaluation-lab/pull/34) is separate and unmerged. Its follow-up scan and review are required before broader candidate-execution claims; it is not evidence that this ProofQ API has been security reviewed.
- The near-term customer deliverable remains a human-reviewed offline report for up to ten eligible single-qubit Ry/Z-basis cases. Scope, inputs and payment must be agreed before work starts. No customer, payment or grant award is established by these tests.
