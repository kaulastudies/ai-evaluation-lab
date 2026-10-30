# Startup Qatar pitch source

15 core slides and three appendices. Claims match the companion deck. Sources checked 30 October 2026.

## 1. Release checks for coding agents

ProofGate by AI Evaluation Lab

Inspectable evidence for the engineering team deciding whether an AI-generated change is ready to release.

Working prototype. Canonical demo: kaulastudies.github.io/ai-evaluation-lab/proofgate/

Sources: https://kaulastudies.github.io/ai-evaluation-lab/proofgate/; https://github.com/kaulastudies/ai-evaluation-lab

## 2. Passing tests can still hide a broken task

A recorded agent patch silently dropped inactive records in a synthetic transformation task.

| The same AP-005 patch | Observed result |
| --- | --- |
| Public tests | PASS |
| Requirement: retain every input record | FAIL |
| Qualified verifier | VERIFIED_FAIL |



A later recorded repair passed the bounded verifier. This example is synthetic, not a customer incident.

Sources: https://kaulastudies.github.io/ai-evaluation-lab/proofgate/; https://github.com/kaulastudies/ai-evaluation-lab/blob/794602108eba47c806543c01b7f8d2b7ba9345cc/programs/repository-agent-reliability/metrics/summary.json

## 3. A requirement, a check and a reviewable result

The existing demonstration links a task contract to retained artifacts and a verdict.

- **Define**: State required behavior and forbidden changes. Challenge the verifier with negative controls.
- **Check**: Inspect the candidate and run the bounded contract checks against pinned evidence.
- **Review**: Retain PASS, FAIL or HOLD, the reason, source identities and a reproduction path.



Customer installation, execution isolation and release integration are development milestones.

Sources: https://kaulastudies.github.io/ai-evaluation-lab/proofgate/; https://github.com/kaulastudies/ai-evaluation-lab/blob/794602108eba47c806543c01b7f8d2b7ba9345cc/programs/repository-agent-reliability/metrics/summary.json; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/TECHNOLOGY_ROADMAP.md

## 4. 52 retained attempts across five tasks

Failures and unresolved outcomes remain in the public record.

success claims with passing public tests failed the qualified verifier.

49 initial attempts + 3 repairs. The 30-trial replication is included. Selected synthetic tasks do not establish a population failure rate.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/794602108eba47c806543c01b7f8d2b7ba9345cc/programs/repository-agent-reliability/metrics/summary.json

## 5. An engineering lead with a recurring release decision

Software companies and coding-agent integrators are the initial customer hypothesis.

- **Purchase trigger**: AI-generated changes repeatedly need manual checks beyond the current tests.
- **Scope**: One authorized repository task family with an engineering owner and a budget route.
- **Economic test**: At $50 per review hour, a $1,000 monthly fee equals 20 hours of review effort.



The cost comparison is illustrative. Buyer baseline, actual savings, support effort and willingness to pay are unvalidated.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/COMMERCIAL_PLAN.md

## 6. A fair comparison on held-out cases

A proposed $5,000, four-week scope begins after access and funding are ready.

- **Independent cases**: At least 30 buyer/reviewer cases: 10 valid, 10 known critical violations and 10 incomplete-evidence cases.
- **Clear decisions**: Target all 10 critical violations failed, at least 9 valid cases passed and all incomplete cases held.
- **Measured effort**: Compare with the buyer's own checks. Target 20% lower median active review time and exact replay.



Proposed thresholds require buyer agreement before testing. Small samples do not establish production accuracy or safety.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/PILOT_PROTOCOL.md; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/TECHNOLOGY_ROADMAP.md

## 7. The pilot must earn a place beside existing checks

The advantage to test is useful evidence with less contract-design and review effort.

| Alternative | What the buyer already has |
| --- | --- |
| Internal tests and CI | Assertions, logs and engineering review |
| LangSmith | Code evaluators, datasets and regression tests |
| Promptfoo | Assertions, evaluation and CI integration |
| AI Evaluation Lab proposal | Qualified task contracts and replayable evidence handover |



No feature monopoly or measured superiority is claimed. The same buyer workflow and cases define the comparison.

Sources: https://docs.langchain.com/langsmith/evaluation-types; https://www.promptfoo.dev/docs/intro/; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/COMMERCIAL_PLAN.md

## 8. A defined buyer population and explicit assumptions

Annual spend at the proposed $12,000 service price. These are separate geographic models.

- **$20.19m**: U.S. reference scenario; 16,824 employer software-publishing firms in 2022 × assumed 10% fit × $12,000.
- **$0.491m**: Qatar entry SAM scenario; 409 ICT directory listings × assumed 10% serviceability × $12,000.



Sources: U.S. Census and Qatar CRA. Qualification shares and price are unvalidated. Worldwide TAM is unmeasured.

Sources: https://data.census.gov/table/ECNBRIDGE22022.EC2200BRIDGE2?codeset=naics~511210; https://www.cra.gov.qa/Services/ICT-Business/ICT-Business-List/ICT-Business-Directory; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/MARKET_SIZING.md

## 9. A named starting list for finding the release owner

Research targets include iHorizons, malomatia, Mannai and Advancya.

- **Days 1-30**: Target 15 interviews. Find three teams with the same recurring release problem.
- **Days 31-60**: Target three assisted staging installs after access and execution controls are reviewed.
- **Days 61-90**: Seek one signed paid scope or budget-authorized LOI with acceptance rules and procurement steps.



These companies are research targets, not partners, customers or a qualified pipeline. A LOI is not payment.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/QATAR_BUYER_MAP.md; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/COMMERCIAL_PLAN.md

## 10. Installation and repeatability before sector expansion

Milestones begin from an agreed, funded start and actual founder availability.

| Period | Proposed engineering output | Gate to proceed |
| --- | --- | --- |
| By day 90 | Pinned package and reviewed runner | Three installs; independent cases |
| By day 180 | Paid pilot and repeat-release handover | Buyer acceptance; reproducible verdicts |
| By day 365 | Reusable task pack and opt-in CI integration | Two teams reuse the pack with less support |



Customer isolation is unbuilt. Month-4 onward work requires separate funding and an updated operating plan.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/TECHNOLOGY_ROADMAP.md

## 11. Bounded delivery with visible unit economics

Prices and effort are hypotheses to validate through the first purchase.

- **$5,000 pilot**: 60 hours of delivery; $3,750 direct economic cost; $1,250 contribution / 25%; One repository task family
- **$1,000 / month**: 8 hours of recurring support; $500 direct economic cost; $500 contribution / 50%; One recurring workflow



Contribution excludes overhead and tax. Current pricing describes a service. Excess custom work requires a new scope.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/FINANCIAL_PLAN.md

## 12. Reuse determines whether this becomes a product

The reusable unit is a versioned task contract, its controls and evidence interface.

- **First**: One coding workflow improves a release decision enough to earn paid repeat use.
- **Then**: A second team adopts the same pack with less founder setup and support.
- **Later**: Support approvals or other sectors add domain rules only when two teams need the same pack.



Multi-sector potential is a development hypothesis. Hosted service, authenticated connectors and autonomous enforcement are not current capabilities.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/PLATFORM_STRATEGY.md; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/TECHNOLOGY_ROADMAP.md

## 13. Public engineering work and operational experience

Rama Chandra Malayanur / Solo technical founder / India

- **Built and published**: AI Evaluation Lab Alpha in September 2026. ProofGate canonical demo on 29 October.
- **Accepted upstream**: Backstage Community Plugins merged the Periskop Jest 30 migration on 22 September.
- **Relevant experience**: AI evaluation project work, Python engineering, systems support and healthcare workflows.



Proposed reviewers and hires are not current employees. Resume and founder profile provide the supporting record.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/commit/e1a7226f59174608a69c2ca7799e96883bfa5212; https://github.com/kaulastudies/ai-evaluation-lab/pull/33; https://github.com/backstage/community-plugins/pull/10964

## 14. A local validation base with a route to delivery

The proposal fits the program's AI/ML and B2B SaaS priorities.

- **Customer access**: Seek introductions to engineering leads and integrators with authorized staging work.
- **Local capability**: Develop evaluation delivery and independent review. A local engineer is conditional from month 7.
- **Operating route**: Agree entity, presence, costs and eligible spending before local commitments. Re-cost after buyer evidence.



No Qatar customer, entity, partner or relocation is committed. Actual residence and two-year availability answers remain unresolved.

Sources: https://www.qdb.qa/en/Financing-And-Funding/Equity-And-Investment/Startup-Qatar-Investment-Program; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/QATAR_OPERATING_PLAN.md

## 15. A bounded validation decision

Initial funding proposal, subject to program eligibility and agreed investment terms.

Targets: 15 interviews, three assisted installs and one paid scope or budget-authorized LOI.

Follow-on review before month 4. Amount depends on evidence, local quotes and cash available.

$100,000 is a separate no-collection planning envelope. It is not an upfront request or an agreed investment.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/INVESTMENT_CASE.md; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/FINANCIAL_PLAN.md

## 16. Market estimates change with the qualification rate

Annual spend at $12,000 per account. Percentages below are assumptions, not observed adoption.

| Assumed qualified share | U.S. reference firms | Qatar directory listings |
| --- | --- | --- |
| 5% | $10.09m | $245,400 |
| 10% | $20.19m | $490,800 |
| 20% | $40.38m | $981,600 |



U.S. reference: 2022 Census, 16,824 firms. Qatar: CRA, 409 listings retrieved 30 Oct 2026. No nested/global total is claimed.

Sources: https://data.census.gov/table/ECNBRIDGE22022.EC2200BRIDGE2?codeset=naics~511210; https://www.cra.gov.qa/Services/ICT-Business/ICT-Business-List/ICT-Business-Directory; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/MARKET_SIZING.md

## 17. What the existing evidence establishes

Public evidence snapshot 7946021. Technical results are separate from customer validation.

| Evidence | Scope |
| --- | --- |
| 52 retained attempts | 44 pass / 5 fail / 3 hold; five synthetic tasks |
| 30-trial AP-001 replication | Included in 52; three configurations × 10 trials |
| 17 configured critical mutations | All rejected; controls are not exhaustive |
| 12 support-workflow controls | Separate offline prototype, no customer connector |
| Customer execution and security | Isolation unbuilt; security PR #34 remains open |



Replay uses stored artifacts. Hash consistency depends on a trusted reference and does not authenticate a remote event.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/794602108eba47c806543c01b7f8d2b7ba9345cc/programs/repository-agent-reliability/metrics/summary.json; https://github.com/kaulastudies/ai-evaluation-lab/pull/34; https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/EVIDENCE_LEDGER.md

## 18. The first allocation does not fund a full year

Twelve-month operating scenarios if spending continues. USD, before tax and quoted local revisions.

| Measure | Base hypothesis | Downside |
| --- | --- | --- |
| Invoices / collections | $61,000 / $52,000 | $16,000 / $10,000 |
| Operating cash cost | $85,550 | $79,550 |
| Peak unfinanced cash need | $33,550 | $69,550 |
| Year-end balance with initial $12k only | -$21,550 | -$57,550 |



Both scenarios need a funding or stop decision before month 4. Historical financial balances remain unreconciled.

Sources: https://github.com/kaulastudies/ai-evaluation-lab/blob/feat/startup-qatar-jury-readiness/docs/startup-qatar/FINANCIAL_PLAN.md
