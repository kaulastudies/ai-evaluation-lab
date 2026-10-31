# Reviewer Case Sheet and Scoring Template — DRAFT (no collected responses)

**Study protocol:** [PROTOCOL_DRAFT_v0.2.md](PROTOCOL_DRAFT_v0.2.md).  
**Status:** Template only; do not treat sample fields as human-review data. Final case packets, rubric, consent, and procedures must be frozen before recruitment.

## A. Case preparation (researcher, not shown to participant)

| Field | Required record |
| --- | --- |
| Pseudonymous case ID | To assign |
| Task family + immutable task-contract SHA | To assign |
| Frozen evidence source commit + artifact SHA-256 | To assign |
| Verifier/control version | To assign |
| Public-test status | To assign |
| Qualified verifier status | To assign |
| Gate-level findings / limitations | To assign |
| Related cases and leakage controls | To assign |
| Selection and exclusion decision | To assign |
| Packet A version/hash | To assign |
| Packet B version/hash | To assign |
| Rubric version/hash | To assign |

**Packet A (baseline) may show only:** objective, approved patch excerpt, public-test results, and neutral task context. Do not display case identifiers, hidden gate names/outcomes, repair lineage, final labels, or links that expose Packet B.

**Packet B (revealed evidence):** all of Packet A *plus* permitted qualified-verifier gates, evidence provenance, replay details and explicit uncertainty. Do not present replay as a fresh model execution.

## B. Participant-facing Stage A — public-test-only

Case ID: _______  Reviewer pseudonym: _______  Packet A hash: _______

1. Review disposition (choose one): ACCEPT / REPAIR / HOLD / REJECT / CANNOT DETERMINE.
2. Why is this warranted based **only** on the currently shown evidence? _______
3. What important evidence is still missing? _______
4. How confident are you in this limited review decision (0–100)? _______
5. Are you already familiar with the case or its results? No / Possibly / Yes. If yes, describe without looking up results: _______

**Save Stage A as immutable before revealing Packet B.**

## C. Participant-facing Stage B — qualified-verifier evidence

Case ID: _______ Reviewer pseudonym: _______ Packet B hash: _______

1. Updated disposition: ACCEPT / REPAIR / HOLD / REJECT / CANNOT DETERMINE.
2. What changed, if anything, and which specific evidence supports that change? _______
3. Which limitations or missing evidence still matter? _______
4. Updated confidence (0–100): _______
5. Did the additional evidence reveal a problem or uncertainty that was not apparent from public tests? _______

## D. Independent scoring sheet (not participant-facing)

Prior to recruitment, an independent scorer or panel freezes a **case-specific set of defensible dispositions** for each stage. Do not equate decision change with improvement.

| Score field | Stage A | Stage B |
| --- | --- | --- |
| Scored adequate / inadequate / unscorable |  |  |
| Correct interpretation of evidence availability |  |  |
| Avoids extrapolating beyond configured checks |  |  |
| Correct handling of HOLD and uncertainty |  |  |
| Adequate reasons and explicit missing evidence |  |  |
| Independent scorer's justification |  |  |
| Adjudication (if disputed; retain initial scores) |  |  |

**Case anchors, to verify against frozen records (not automatically correct answers):**

- **AP-005 pre-repair:** public-pass false green; after reveal, HOLD/REPAIR may be warranted.
- **AP-005 post-repair:** task-specific verifier pass; qualified acceptance may be considered but never production authorization.
- **AP-003 terminal:** qualified failure after repair budget; HOLD/REJECT may be warranted.
- **Admission HOLD:** output not admitted; no candidate execution verdict; request admissible submission.
- **AP-001 replay:** provenance shows stored-verdict reproducibility; no claim of provider-wide reliability.

**Adjudication and de-identification:** keep reviewer answers separate from identifying recruitment data; preserve every independent rating, exclusion, disagreement and revision note. No real responses are present in this template.
