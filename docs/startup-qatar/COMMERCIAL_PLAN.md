# Commercial plan: verifiable release checks for coding agents

Status: proposed commercial strategy, 30 October 2026. No buyer interviews, signed
pilot, Qatar customer, product revenue, or willingness to pay are established by
this document. The numerical assumptions below are planning inputs, not market
research findings or a financial offer.

The [platform and launch strategy](PLATFORM_STRATEGY.md) extends this first-pilot
plan toward reusable software and multiple sectors. Its expansion gates and beta
targets are proposed. They do not change the current scope, pricing assumptions
or customer-evidence status.

## The first purchase decision

An engineering lead at a SaaS/software company or coding-agent integrator is
reviewing an AI-generated change. Existing tests pass, but the buyer still needs
to know whether the change satisfies the agreed task contract and preserves
behavior that the tests did not cover. The AP-005 demonstration makes one such
failure inspectable; it is a synthetic example, not a customer incident.

AI Evaluation Lab's proposed first offer is a bounded release evidence pack for
one repository task family. ProofGate is the existing coding-agent demonstration;
customer installation, reviewed execution isolation and reusable repository
adapters remain proposed work. The separate offline support/approval example is
an expansion prototype, not the initial customer integration.

The first customer profile is a SaaS/software engineering team or coding-agent
integrator that:

- has a recurring agent-generated code workflow and a defined release decision;
- can authorize a bounded task family, test repository and inspectable artifacts;
- has a named engineering owner, release date and person who controls budget;
- changes code, models, prompts or tools often enough to reuse the checks;
- can describe a relevant regression, missing check or costly review process.

The engineering or platform lead is the likely champion. The head of engineering
or product is the proposed budget owner. Security and procurement may veto
access or a purchase. These roles must be identified for each prospect; a helpful
developer or an accelerator introduction alone is not a qualified buyer.

Exclude the first pilot if it requires live financial transfers, production
credentials, regulated personal data, unrestricted agent execution, or a general
safety certificate. A team needing only response-quality scoring is outside this
initial offer unless interviews reveal a concrete coding-release verification need.

## Why investigate this now

Stack Overflow's 2026 trust question had 14,304 respondents: 48.0% selected trust
conditional on easy output verification, while 6.6% selected trust including
important work decisions. This self-selected survey motivates discovery; it does
not measure the Lab's customer demand or market size. No cross-year comparison
is inferred. Source: [Stack Exchange Inc., 2026 Developer Survey](https://survey.stackoverflow.co/2026/ai/data/ai-trust),
ODbL 1.0 response data; checked 30 October 2026.

## What the buyer receives

One repository task family, one frozen acceptance contract, a small qualified
test set, a comparison with the buyer's existing checks, and a reproducible evidence
report. A four-week delivery scope is proposed after authorized access, execution
isolation and independent review are ready.
The [pilot protocol](PILOT_PROTOCOL.md) specifies the measurements and stop rules.
The handover includes the observed failures, clean outcomes, unresolved cases,
case-level evidence, and rerun instructions. It does not promise a safe agent or
an absence of future failures.

Start as a fixed-scope service. Only build reusable software features after two
pilots reveal the same repeated need. A customer can keep its current tracing and
evaluation stack; a new dashboard or platform migration is not a prerequisite.
Adapters, hosted deployment, and enterprise security controls must be costed and
validated separately when requested.

## Existing alternatives and the test for added value

| Alternative | Existing capability | What the pilot must establish |
| --- | --- | --- |
| The buyer's own CI, assertions, and incident review | Workflow-specific checks and staff who understand the system | A measured gap or reduction in review effort worth buying, after accounting for integration time |
| LangSmith | Offline and online evaluation, regression testing, custom code evaluators, and other evaluator methods | A qualified workflow contract and evidence package add value to this buyer; deterministic checks alone are not unique |
| Promptfoo | Evaluation and red teaming through a CLI/library, assertions, provider integrations, and CI/CD use | Outcome checks and replay can solve a specific remaining problem; no claim that these capabilities are impossible in Promptfoo |
| A specialist consultant or internal hire | Custom test design and implementation | The Lab can deliver a repeatable scope at an acceptable cost with credible evidence and handover |

Primary product documentation reviewed on 30 October 2026:
[LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types)
and [Promptfoo introduction](https://www.promptfoo.dev/docs/intro/).
This is a limited comparison, not an exhaustive feature or price audit. No
head-to-head performance result has been produced.

The differentiation hypothesis is the combined delivery of explicit repository
task contracts, tests of the verifier itself, retained failures, and inspectable
release evidence. Each component can be reproduced by others. Any lasting
advantage must come from validated task expertise, lower adoption effort, and
repeat customer value. Proprietary customer artifacts cannot become a public
benchmark or commercial asset without separate publication and reuse rights.

## Proposed pricing and delivery economics

All values are USD, before tax. Validate the scope and price with actual buyers.

| Offer | Proposed price | Included scope | Economic direct-cost assumption |
| --- | ---: | --- | ---: |
| First pilot | $5,000 | One workflow; up to 60 engineering hours; independent case review; bounded local/staging runs and handover | 60 hours × $50 + $500 reviewer + $250 compute/storage = $3,750 |
| Recurring regression support | $1,000/month | One previously accepted workflow; up to eight engineering/review hours; agreed rerun cadence and report | Eight hours × $50 + $100 compute/storage = $500/month |

Pilot contribution is $1,250, or 25%, before sales time, general overhead, tax,
and other costs. Recurring contribution is $500, or 50%, on these assumptions.
Unpaid founder time is still an economic cost; it is not necessarily a cash
payment. The recurring plan is a hypothesis, not an existing subscription.

The scope must state an execution cap before a quote is issued. Additional
workflows, custom adapters, new contracts, hosted infrastructure, or more hours
require a revised scope. Do not recover overruns through unapproved usage charges.
If a pilot needs 100 engineering hours at the same rate, its direct economic cost
becomes $5,750 and the $5,000 price loses $750 before overhead. That result is a
reason to narrow scope or change pricing, not evidence of scalable margins.

## Source-anchored market scenarios

The [market sizing note](MARKET_SIZING.md) replaces earlier unsourced 50/200-account
illustrations. At the $12,000 annual service hypothesis, 16,824 U.S. employer
software-publishing firms in the 2022 Census with an assumed 5-20% fit produce a
$10.09m-$40.38m annual-spend reference range, with $20.19m at 10%. Qatar CRA's
409 displayed ICT companies with an assumed 5-20% screened serviceability produce
$245,400-$981,600, with $490,800 at 10%.

The qualification rates and price are unvalidated. Worldwide TAM remains
unmeasured. Qatar is not a subset of the U.S. reference and the scenarios must
not be nested or summed as a worldwide total. The directory needs activity
screening and purchasing-group deduplication. Ten [named research targets](QATAR_BUYER_MAP.md)
provide a starting point, not customers or a qualified pipeline.

The operating model's base scenario remains nine $5,000 pilot invoices and
16 recurring customer-months at $1,000: $61,000 invoiced, $52,000 collected and
668 delivery hours. Timing, collection and capacity assumptions govern feasibility.
The only current initial funding request is $12,000; it funds validation only.
Month-4 onward delivery requires a new funding/cost decision. See the
[financial plan](FINANCIAL_PLAN.md) for cash and stop conditions.

## Discovery that can disprove the idea

Target 15 buyer interviews with relevant engineering/release owners across at least
five organizations. This is a proposed research sample, not 15 scheduled
meetings. Start with Qatar-serving teams for relevance, but record Qatar and other
markets separately rather than disguising international evidence as local demand.

Ask these questions before showing the proposed solution:

1. Describe the last agent-generated code change you reviewed. What requirement
   and release decision did it affect?
2. What failed or took longest to verify? Show a redacted or synthetic example if
   you are permitted to share one.
3. Which checks caught the problem? Which evidence was missing? What happened next?
4. How many people and hours did review and repair require? Which costs are measured
   and which are estimates?
5. What do you already use for tests, evaluation, CI and manual code review?
6. Who could approve a pilot, from which budget, and on what procurement timescale?
7. What repository permissions, data rules or execution-isolation requirements
   would prevent a staging installation?
8. After seeing the exact pilot scope and $5,000 hypothesis: what would you remove,
   what would make it worth paying for, and what concrete next step could you take?

Record the date, role, workflow, observed problem, source of cost estimates,
current alternative, budget owner, purchase conditions, and disposition.
Separate direct statements from interpretation. Permission to quote an interview
does not imply permission to publish artifacts or name the organization.

Proposed discovery continuation gate: at least three distinct organizations
describe the same recurring coding-release problem using a specific example,
three are suitable for assisted staging installs, and at least one names a budget
owner and a plausible paid-pilot procurement route. A pleasant call, mailing-list signup, unpaid
collaboration, or vague interest does not satisfy this gate. If the gate is
missed after 15 relevant buyer interviews, revise the workflow or buyer segment before
expanding the product. Report the failure honestly.

## Ninety-day execution and stop decisions

The clock begins with the approved, funded validation stage; external access and
human review may change the schedule. Proposed owners are roles, not employees or committed hires.

| Period | Work and proposed owner | Reviewable output | Continue only if |
| --- | --- | --- | --- |
| Days 1–30 | Founder: 15 buyer interviews, eligibility screen and ProofGate walkthrough | Dated discovery log; three teams describing the same recurring coding-release problem | The discovery gate above is met or one explicit segment revision is justified |
| Days 31–60 | Founder + buyer engineers: three assisted staging installs | Authorized artifacts, reviewed isolation, buyer-authored cases, setup/assistance time and baseline comparison | Access is lawful, execution controls are adequate, and at least one workflow has plausible value |
| Days 61–90 | Founder + buyer budget owner + independent reviewer: scope and procurement | One signed paid scope or budget-authorized LOI; frozen acceptance rules, price, data boundary and delivery budget | Buyer ownership and procurement are real and the delivery economics fit |

The base financial scenario starts completed paid delivery and invoicing in month 4,
with recurring service from month 6. The first three months prepare that decision;
staging installs, written interest and an LOI are not completed pilots or sales.
An LOI must state whether it is binding and which conditions remain. Both the
schedule and the 15/3/1 targets are proposed, not achieved milestones.

No signed pilot or buyer access means no claimed customer validation. A letter of
intent, if obtained, should say whether it is binding and identify its conditions;
it is neither revenue nor a completed pilot. Collecting payment is not authorized
by this plan. Contracts, prices, commitments, and outreach require their own
appropriate execution steps.

## How this strengthens the Qatar proposal

Qatar should be a place to conduct useful customer validation and build a credible
operation, rather than an address added to qualify for funding. The immediate
local contribution hypothesis is evaluation engineering for software teams and
coding-agent integrators. Support/approval workflows and buyer-required
Arabic–English cases are later extensions needing qualified review. No Arabic capability, local buyer, institutional
partner, resident founder, or local hire is claimed today.

The application becomes stronger with one permissioned buyer case, a baseline
comparison the buyer accepts, a paid scope or documented purchase process, and a
realistic delivery-cost ledger. None of these can be replaced by a larger market
number or additional synthetic benchmark runs alone.
