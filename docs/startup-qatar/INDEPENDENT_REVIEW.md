# Internal adversarial review

Review date: 30 October 2026. This review was performed by a separate AI-assisted
QA workstream from the authors of the new workflow verifier and planning model.
It is **internal agent review**, not an independent human audit, a customer
validation, a financial audit or a Startup Qatar committee assessment.

This document records the earlier engineering review. The current proposal's
initial request is $12,000; $100,000 is a separate stress envelope. See
[INVESTMENT_CASE.md](INVESTMENT_CASE.md) for the superseding funding recommendation.
The new finance tests verify that unpriced follow-on reviews add no assumed cash.

## Disposition

The new material is suitable for a draft PR and founder/technical review after
the corrections below. It is not a production-release approval or a completed
funding application. No unresolved defect was found in the narrow new-code
checks described here; this is not a claim of exhaustive verification.

The proposal states its main remaining weaknesses accurately: no verified paying
Lab customer or Qatar pilot, no demonstrated customer ROI, founder decisions and
historical financial records still open, and security remediation in a separate
unmerged PR. These are substantive diligence dependencies, not problems a more
polished document can remove.

## Findings and corrections

| Finding | Scope and reproduction | Resolution verified |
| --- | --- | --- |
| Nonfinite financial assumptions were accepted | In `financial_model.py`, the initial `validate()` accepted `float('nan')` as the labor economic rate; `build()` then returned NaN unit-economics fields. This was a planning-integrity defect, not a production exploit. | Finite numeric checks now reject NaN and infinities; serialization uses strict JSON. Independent retest rejected these inputs. |
| Hiring capacity could be configured inconsistently | The initial validator allowed fractional/out-of-range start months and different dates for engineer capacity and salary. | Start months require integers in 1–12, and engineer salary/capacity start together. Independent retest rejected invalid months and early unpaid capacity. |
| Receipt semantics could overstate duplicate detection | Two distinct `applied` receipt IDs were interpreted as two effects. In a real log, two deliveries might describe one effect. | [Demo documentation](DEMO.md) now states the synthetic meaning explicitly and requires a real connector to establish distinct effects. The code does not claim to solve receipt authentication or log completeness. |
| Commercial and finance examples differed | A separate four-pilot commercial illustration could be confused with the finance model's base scenario. | Commercial text now uses the same nine-pilot, sixteen-recurring-month example: $61,000 invoicing and $52,000 collections. Both remain assumptions, not observed sales. |

## Checks performed

| Check | Observed result | Limit |
| --- | --- | --- |
| Separately authored valid workflow case plus 46 mutation/integrity assertions | Passed. Missing fields, truthy non-boolean claims, unknown authority, mismatched receipt references, unobserved retries, duplicate effects and contradictory receipts did not become PASS. Report hashing and deterministic regeneration agreed. | A bounded set of API-level cases; not exhaustive fuzzing or an external trust-boundary test. |
| New workflow unit suite | 23 tests passed, including separate two-actor/two-ticket fixtures and committed-control regeneration. | Test counts do not establish general safety or customer performance. |
| Workflow control report | 12 synthetic controls: 2 PASS, 4 FAIL, 6 HOLD; the mixed suite blocks release. | No new model inference or customer execution; these controls must not be added to the historical 52 attempts. |
| Evidence snapshot check | Passed: 52 historical attempts, 49 scored-record hashes and 265 input-file hashes. | Checks stored artifacts and arithmetic; does not authenticate their external origin. |
| Auditor corruption probes in a temporary copy | A changed nested verdict failed its record hash; an inflated qualification rejection count failed its summary check. Restoring bytes reproduced the same snapshot. | Original evidence was unchanged; this does not validate every possible artifact attack. |
| Financial arithmetic | Pilot direct economic cost $3,750 and contribution $1,250; recurring direct cost $500; separate stress envelope $100,000. Both scenarios reconcile invoices, collections, receivables, costs and cash deltas. | Inputs are unquoted assumptions. Historical accounts remain null. |
| Financial invalid-input retest | Fourteen separate invalid numeric, month and salary/capacity configurations were rejected after the fix. Committed output check passed. | The script is a planning calculator, not accounting software or a contractual investment model. |
| Proposal consistency | Reviewed the pitch, founder profile, application, jury, evidence, commercial, pilot, finance, operating and submission documents. Historical evidence, synthetic demonstration, hypotheses and unresolved commitments remain distinct. | No new buyer interviews, program confirmation, identity verification or independent human review was conducted. |

The 46 workflow and 14 financial checks above were additional reviewer probes,
not new model trials. They are separate from the checked-in unit-test count.
Two maintained regression tests in `tests/test_startup_qatar_financials.py` now
cover the nonfinite-input and hiring-timing defects, including parameterized
invalid cases. The earlier integrated suite passed 47 tests. Current revision validation is recorded in the PR; do not treat this historical count as the current suite total.

## Reproduce the maintained checks

From the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_workflow_release.py -v
python programs/startup-qatar/evidence_snapshot.py --check
python programs/startup-qatar/financial_model.py --check
PYTHONPATH=src python -m eval_lab.workflow_release \
  --contract examples/workflow-release/contract.json \
  --evidence examples/workflow-release/controls.json \
  --output /tmp/workflow-review-report.json
diff -u examples/workflow-release/report.json /tmp/workflow-review-report.json
```

The demo command without `--gate` returns success when it generates a valid
report, even when that report blocks release. With `--gate`, this deliberately
mixed control suite must return 1. Invalid input returns 2. These exit semantics
must not be mistaken for a passing customer release.

## Boundaries that remain open

1. The workflow contract and receipt log are trusted inputs. There is no signed
   receipt source, completeness proof, chronology, revocation, tenant-aware live
   connector or runtime enforcement. Internally consistent fabricated evidence
   can pass. Hashes alone do not address that problem.
2. The first customer pilot still needs a real buyer owner, an actual baseline,
   independent human case authorship, measured false acceptance/false blocks and
   review effort, plus permissioned data and a commercial decision. An agent's
   review cannot supply those facts.
3. [Security remediation PR #34](https://github.com/kaulastudies/ai-evaluation-lab/pull/34)
   was open and unmerged at head `b81aec5ae4e143fe06e15e2b65dad6a2a7966e35`
   when checked. Its own description requires security review and a follow-up
   scan. This branch starts from main and does not inherit those unmerged fixes.
   This review did not retest or close the existing security findings.
4. The financial model does not substantiate prices, salaries, demand or local
   costs. Founder availability, historical accounts, legal structure, Qatar
   commitments and investment terms need their actual owners' decisions.
5. The proposed review roles and workstreams are not additional employees,
   contracted advisers, program endorsements or selection odds.

Proceed with review of the PR and the [submission gates](SUBMISSION_GATES.md).
Do not turn this internal QA disposition into an external certification or a
statement that the application is ready to submit unchanged.
