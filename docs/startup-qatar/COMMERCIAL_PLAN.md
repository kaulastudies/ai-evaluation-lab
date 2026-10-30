# Commercial plan: verifiable release checks for agent workflows

Status: proposed commercial strategy, 30 October 2026. No buyer interviews, signed
pilot, Qatar customer, product revenue, or willingness to pay are established by
this document. The numerical assumptions below are planning inputs, not market
research findings or a financial offer.

The [platform and launch strategy](PLATFORM_STRATEGY.md) extends this first-pilot
plan toward reusable software and multiple sectors. Its expansion gates and beta
targets are proposed. They do not change the current scope, pricing assumptions
or customer-evidence status.

## The first purchase decision

An engineering lead is about to release a support agent that can update tickets
and request approvals. The agent says an action succeeded; a release test checks
the response format. The buyer still needs to know whether the right action
actually occurred, within the right tenant and authority, exactly as permitted.

AI Evaluation Lab's proposed first product is a bounded release evidence pack for
that decision. ProofGate is an existing demonstration of the Lab's verification
approach; adapting it to a buyer's support workflow is proposed work. This offer
does not assume the present repository is already a customer integration.

The first customer profile is a B2B software company or implementation team that:

- owns a working tool-using support or internal-approval agent;
- can provide a synthetic staging workflow and inspectable action receipts;
- has a named engineering owner, release date, and person who controls budget;
- changes its model, prompts, tools, or workflow often enough to rerun checks;
- can describe a recent relevant failure or a costly release-review process.

The engineering or platform lead is the likely champion. The head of engineering
or product is the proposed budget owner. Security and procurement may veto
access or a purchase. These roles must be identified for each prospect; a helpful
developer or an accelerator introduction alone is not a qualified buyer.

Exclude the first pilot if it requires live financial transfers, production
credentials, regulated personal data, unrestricted agent execution, or a general
safety certificate. A team needing only response-quality scoring is outside this
initial offer unless interviews reveal a concrete action-verification problem.

## What the buyer receives

One workflow, one frozen acceptance contract, a small qualified test set, a
comparison with the buyer's existing checks, and a reproducible evidence report.
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

The differentiation hypothesis is the combined delivery of explicit action
contracts, tests of the verifier itself, retained failures, and inspectable
outcome evidence. Each component can be reproduced by others. Any lasting
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

## Bottom-up market model: inputs still to validate

Count organizations, not individual developers, downloads, accelerator applicants,
or all businesses using AI. Count one purchasing organization once even if it has
several agents. The initial offer and capacity support a small beachhead; a broad
global market claim is unnecessary until the definition has been validated.

| Model | Formula | Evidence still needed |
| --- | --- | --- |
| Potential global annual spend for the defined workflow offer (TAM) | Verified eligible organizations worldwide × validated annual spend per organization | A reproducible organization list, eligibility screen, and price evidence; neither input is currently established |
| Reachable serviceable annual spend (SAM) | Eligible organizations in markets the Lab can actually serve × validated annual spend | Procurement, delivery, language, data-location and jurisdiction constraints; access to a prospect is not demand |
| Capacity-constrained first-year sales (SOM) | Pilots deliverable × pilot price + contracted recurring customer-months × monthly price | Founder capacity, signed scopes, actual conversions, and start dates |

Illustrative arithmetic only: 50 qualified reachable organizations at an assumed
$12,000 annual recurring spend would imply $600,000 in annual SAM. At 200
organizations the same formula gives $2.4 million. Neither organization count has
been verified; these are sensitivity examples, not a claimed Qatar or global
market size. Do not insert them as factual TAM/SAM values in an application.

The [financial model's](FINANCIAL_PLAN.md) illustrative base case uses nine
$5,000 pilots and 16 total recurring customer-months at $1,000, producing
$61,000 invoiced revenue. The 16
months are summed across start dates, not treated as sixteen months for each
converted customer. This is a modeled scenario, not a validated forecast,
booked pipeline, or funding request. At 60 hours per pilot plus eight per
recurring month, delivery requires 668 hours, before research, sales,
administration, integration overruns, and leave. Invoice value is not cash:
the financial model projects $52,000 collected in this scenario under its
one-month collection-lag assumption. Its month-by-month capacity, funding gates,
and downside case govern whether work can start; this annual total does not
establish feasible timing or funded runway.

To replace the market placeholders, build a dated list of 30 candidate
organizations with a public source for the relevant workflow, geography,
decision-maker role, eligibility reason, and duplicate checks. Keep personal
contact details and interview notes in a private workspace. Then report the
qualified subset and observed interview/conversion counts. Do not count uncontacted
organizations as a pipeline or display their logos as customers.

## Discovery that can disprove the idea

Target ten interviews with relevant engineering/release owners across at least
five organizations. This is a proposed research sample, not ten scheduled
meetings. Start with Qatar-serving teams for relevance, but record Qatar and other
markets separately rather than disguising international evidence as local demand.

Ask these questions before showing the proposed solution:

1. Describe the last agent release you approved. What actions could it perform?
2. What failed or took longest to verify? Show a redacted or synthetic example if
   you are permitted to share one.
3. Which checks caught the problem? Which evidence was missing? What happened next?
4. How many people and hours did review and repair require? Which costs are measured
   and which are estimates?
5. What do you already use for evaluation, tracing, CI, and manual approval?
6. Who could approve a pilot, from which budget, and on what procurement timescale?
7. What data or deployment restrictions would prevent a staging evaluation?
8. After seeing the exact pilot scope and $5,000 hypothesis: what would you remove,
   what would make it worth paying for, and what concrete next step could you take?

Record the date, role, workflow, observed problem, source of cost estimates,
current alternative, budget owner, purchase conditions, and disposition.
Separate direct statements from interpretation. Permission to quote an interview
does not imply permission to publish artifacts or name the organization.

Proposed discovery continuation gate: at least three distinct organizations
describe a recurring action-verification problem using a specific example, two
accept a detailed scoping discussion, and one names a budget owner and a plausible
paid-pilot procurement route. A pleasant call, mailing-list signup, unpaid
collaboration, or vague interest does not satisfy this gate. If the gate is
missed after ten relevant interviews, revise the workflow or buyer segment before
expanding the product. Report the failure honestly.

## Ninety-day execution and stop decisions

The clock begins when work starts; external access, funding, and human review may
change the schedule. Proposed owners are roles, not employees or committed hires.

| Period | Work and proposed owner | Reviewable output | Continue only if |
| --- | --- | --- | --- |
| Days 1–15 | Founder: buyer interviews, eligibility screen, three-minute evidence walkthrough | Dated discovery log and qualified opportunity summary; public summary without private data | The discovery gate above is met or one explicit segment revision is justified |
| Days 16–30 | Founder + buyer release owner: scope and baseline; independent reviewer identified | Written workflow contract, price/scope proposal, data boundary, named buyer owner and reviewer | A buyer authorizes the bounded pilot; costs and access are feasible |
| Days 31–60 | Founder + reviewer: run the frozen pilot and comparison | Case-level results, failures, unknowns, measured effort, customer review | Technical and operational gates in the pilot protocol are met; otherwise report and stop/re-scope |
| Days 61–90 | Buyer budget owner + founder: purchase/renewal decision and economics review | Signed paid scope or documented rejection; repeat-use decision; actual cost ledger | A paid customer or credible purchase process exists and the revised economics support delivery |

No signed pilot or buyer access means no claimed customer validation. A letter of
intent, if obtained, should say whether it is binding and identify its conditions;
it is neither revenue nor a completed pilot. Collecting payment is not authorized
by this plan. Contracts, prices, commitments, and outreach require their own
appropriate execution steps.

## How this strengthens the Qatar proposal

Qatar should be a place to conduct useful customer validation and build a credible
operation, rather than an address added to qualify for funding. The immediate
local contribution hypothesis is engineering support for teams releasing
tool-using agents and, only where buyers need it, Arabic–English workflow tests
reviewed by qualified people. No Arabic capability, local buyer, institutional
partner, resident founder, or local hire is claimed today.

The application becomes stronger with one permissioned buyer case, a baseline
comparison the buyer accepts, a paid scope or documented purchase process, and a
realistic delivery-cost ledger. None of these can be replaced by a larger market
number or additional synthetic benchmark runs alone.
