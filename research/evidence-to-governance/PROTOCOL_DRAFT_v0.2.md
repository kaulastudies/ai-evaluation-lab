# Evidence-to-Governance: Prospective Human-Review Study Protocol (DRAFT v0.2)

**Author:** Rama Chandra M, AI Evaluation Lab

**Prepared:** 31 October 2026

**State:** Working protocol for critique, not preregistered; no human-review data have been collected and no outcome has been measured.

**Related outline:** [Research outline](OUTLINE_2026-10-31.md) | [Evidence version register](EVIDENCE_VERSION_REGISTER.md) | [Case-sheet template](REVIEWER_CASE_SHEET_TEMPLATE.md)

## 1. Narrow research question

For defined AI-generated repository changes under frozen task contracts, how does revealing independently qualified-verifier evidence, compared with ordinary public-test evidence alone, affect the **adequacy, confidence, and justification** of an independent human code-review disposition?

This is a *human evidence-interpretation* study, not a model-ranking experiment, security certification, organizational risk assessment, or deployment-authorization study.

## 2. Hypotheses and prespecified outcomes (proposed, not yet preregistered)

- **H1 (primary):** More review dispositions will satisfy a prespecified case-specific evidence-adequacy rubric after qualified-verifier evidence is revealed than before it is revealed.
- **H2 (secondary):** Some reviewers will change or qualify their dispositions, including through appropriate use of CANNOT DETERMINE. A change by itself does **not** establish improved decision quality.
- **H3 (exploratory):** Reasons and confidence may become better calibrated to the evidence's limitations; no direction or effect size is assumed.

**Primary outcome:** case-level adequate-disposition indicator (yes/no) at each stage, assessed against an independently authored and frozen rubric. The descriptive estimand for the pilot is the within-reviewer difference in adequacy proportion, reported with numerators, denominators and uncertainty; do not treat reviewer-by-case observations as independent if estimating population effects.

**Secondary outcomes:** disposition-change rate, adequate abstention rate, documented reasons citing relevant gates/uncertainties, confidence (0–100), reviewer disagreements, and cases with insufficient evidence. Keep baseline and follow-up denominators explicit. Do not label changed decisions automatically as better.

## 3. Provenance and case selection

Freeze all cases *before reviewer recruitment* using [EVIDENCE_VERSION_REGISTER.md](EVIDENCE_VERSION_REGISTER.md). For each case, record task contract, evidence version, source commit, candidate and verifier identifiers, exact artifact paths and SHA-256 hashes, public-test result, qualified-verifier status, known defects, and what may legitimately be inferred.

**Prespecified pilot case families, separated to limit leakage:**

1. AP-005 pre-repair: public tests passed; qualified verifier rejected four edge-case gates.
2. AP-005 post-repair: follow-up candidate passed the same qualified gates; original failure remains visible in the final evidence packet.
3. AP-003 terminal repair: public-test success did not satisfy idempotency checks within the repair budget.
4. Admission HOLD: rejected before candidate evaluation; no executed-code verdict.
5. AP-001 source-exact replay: recorded results reproduce at frozen source state; cross-task reliability remains unmeasured.

AP-005 before/after cases are related and must not be presented to the same participant consecutively or as independent model trials. Consider separate reviewer assignments when feasible. AP-001 30-trial subset is part of the 52 attempts, not a new dataset. Cases must be synthetic/public, free of undisclosed private customer material, and documented well enough for third-party examination.

**Exclusions:** unavailable evidence, materially changed contracts, missing source pin, unqualified verifier, real customer data, participants who authored the case/verifier, or cases whose outcome is exposed in the baseline packet. Record every exclusion and reason.

## 4. Independent reviewers and conflicts

**Recruitment criteria (proposed):** adult developers, software reviewers, AI evaluation researchers, or assurance practitioners with relevant repository-testing or risk-review experience. Record years/type of experience using voluntary ranges, not identifying employment details.

**Independence:** reviewers should not have authored the RARB candidate, verifier, case labels, or decision rubric. Collect a conflict disclosure and exclude direct contributors from primary analysis. Any lab-affiliated pilot feedback must be marked exploratory and separate from independently recruited responses.

**Sample-size rationale:** a first *feasibility pilot* of approximately 6–10 independent reviewers is a proposed design choice, not a power calculation or a committed recruitment count. Use the pilot to quantify task time, comprehension, missing evidence and outcome variability; determine any larger sample size *after* documenting assumptions and before a confirmatory round. With five nonrandom cases, report descriptive effects; avoid broad population claims, significance claims or a purportedly powered experiment.

**Consent and ethics:** before recruitment provide a participant information statement describing purpose, voluntary participation, expected time, withdrawal rules, retention period, de-identification, contact details, and absence of compensation if applicable. Determine whether a venue or jurisdiction requires ethics review before data collection. Do not publicly identify reviewers without specific permission.

## 5. Two-stage procedure, leakage and order effects

**Stage A — baseline.** Show a controlled packet containing task objective, patch excerpt, public-test result and only the evidence ordinarily available to a code reviewer. Do not expose hidden gate results, names that reveal the case, known fixes, terminal conclusions or source links that reveal the answer. Ask the reviewer independently to choose one disposition, provide reasons, record missing evidence and state confidence (0–100). Save the answer before continuing.

**Stage B — evidence reveal.** Show the additional qualified-verifier results, gate failures/passes, source and replay provenance, and relevant uncertainties. Re-ask the *same* disposition/reason/confidence fields. Make the Stage A answer immutable. Clearly distinguish a verifier verdict from any assertion about real deployment authorization.

**Disposition choices:** ACCEPT / REPAIR / HOLD / REJECT / CANNOT DETERMINE. ACCEPT means *consider task-specific code-review acceptance subject to ordinary human review*, never permission to deploy.

**Order controls:** randomize or counterbalance case order. To reduce cross-case learning, do not sequence related AP-005 cases together, mask identifying case names, and record prior familiarity. The same reviewer cannot be blinded to evidence after it has been shown. A future confirmatory design may compare separate randomized groups receiving public-only versus public-plus-qualified evidence; that design would be separately frozen and powered.

**No live model runs or policy interventions** are required to complete the human-review exercise. Frozen evidence is not revised to make the hypothesis come true.

## 6. Freeze a case-level adequacy rubric before ratings

An independent methods reviewer (or an explicit adjudication panel independent of case authors) must approve an answer key using the frozen contract and evidence, *before* seeing participant responses.

General requirements for an **adequate** disposition:

- identifies the correct evidence state: admission HOLD, public-test-only, qualified VERIFIED_PASS, qualified VERIFIED_FAIL, or replay of a stored verdict;
- does not describe a public-test pass as comprehensive correctness;
- does not infer an executed patch result from an admission HOLD;
- does not infer production approval, provider-wide superiority or security certification from the bounded gates;
- records missing deployment-specific evidence where needed;
- provides reasons consistent with the displayed stage, not hindsight from unavailable evidence.

Dispositions may be **defensible alternatives** rather than a single answer. For example AP-003 terminal failure may warrant HOLD or REJECT; AP-005 post-repair may support consideration of task-specific acceptance or continued HOLD pending local review. CANNOT DETERMINE may be adequate when the presented evidence cannot justify a stronger assertion. Do not mechanically score a particular label as correct without the case's stated evidence and uncertainty.

The rubric will classify (a) adequate, (b) inadequate, or (c) genuinely unscorable, with explicit decision rules and missing-evidence notes. An adjudicator resolves disagreements only *after* independent initial scoring; retain both initial judgments and the rationale for resolution.

## 7. Data capture and analysis

Record: randomized case identifier, blinded reviewer ID, eligibility/conflict status, packet version/hash, stage, disposition, reasons, claimed evidence, confidence, unanswered fields, exposure order, assessment time, adequacy judgments, rubric version, and adjudication notes. Never store unnecessary contact details alongside decisions.

**Analysis, proposed:** tabulate each case and stage, present a paired baseline-versus-reveal transition matrix, and count changes independently of changes in adequacy. Display reviewer-level and case-level variability; for a feasibility pilot emphasize exact counts and ranges. If later testing statistical comparisons, preregister hierarchical/paired handling of repeated reviewers/cases and the missing-data rule before collecting confirmatory data. Do not use simple independent-sample tests on clustered judgments.

**Missingness:** report number invited, eligible, consenting, starting, completing both stages, and excluded. Never assume dropout is random. No imputation in the feasibility pilot.

**Negative findings:** publish zero changes, harmful changes, unjustified confidence increases, disagreement and evidence-insufficiency cases as observed.

## 8. Boundaries of the conclusions

Engineering verifier results answer whether the candidate met the specified frozen contract under configured checks. A human research disposition answers what a reviewer believes warranted by an evidence packet. **Operational deployment authorization** requires a designated accountable owner, application-specific risk assessment, security review, current permissions, monitoring, incident response and rollback readiness; it is not awarded by the research protocol.

Seventeen recorded configured-mutation detections are not exhaustive verifier or security assurance. [Security hardening PR #34](https://github.com/kaulastudies/ai-evaluation-lab/pull/34) is currently unmerged; do not represent proposed mitigations or CI results as production-hardened behavior.

This document is an independent AI Evaluation Lab research draft. It neither names outside observers as research supervisors nor represents a STANAIC/academic endorsement, independent audit or formal peer review.

## 9. Gates before any participant study

- [ ] Reconcile README and metrics snapshot; pin the 52-attempt commit and distinguish older 51-attempt report.
- [ ] Freeze sample cases and actual artifact SHA-256 values; verify all source-exact replay paths locally.
- [ ] Produce distinct, leakage-checked Stage A and Stage B case packets.
- [ ] Approve independent case rubric and written reviewer instructions.
- [ ] Finalize pilot eligibility, consent/privacy and any required ethics review.
- [ ] Commit a dated protocol version before recruitment (and externally preregister if the venue requires it).
- [ ] Recruit independent reviewers and collect both stages without retroactively changing the rubric.
- [ ] Publish de-identified evidence, exclusions, disagreements, negative findings and limitations.
