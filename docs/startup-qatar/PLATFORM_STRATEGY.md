# Product expansion and market launch decision

30 October 2026. This document extends the Startup Qatar proposal with a product strategy. It does not represent new integrations, industry deployments, customers or measured market size.

## Decision

Build toward a shared verification product for teams releasing tool-using AI agents. Start with coding-agent release checks for an engineering lead at a SaaS/software company or coding-agent integrator. Use that first buyer workflow to learn which parts can be installed and reused without founder involvement. Treat support/approval checks as a separate offline expansion prototype. Apply to Startup Qatar once the factual submission gates are resolved, while customer validation continues. Completing several industry products is not a prerequisite for the published PoC/MVP route.[1]

The current repository provides technical proof and an offline workflow example. It does not yet provide self-service customer onboarding, authenticated connectors, paid subscriptions or a demonstrated repeat-use business. Those are material product gaps. A broader pitch alone does not close them.

## What the market evidence supports

McKinsey's August 2026 survey reports that 40% of respondents from large organizations were scaling agents, compared with 22% from smaller organizations. It also reports that 32% had forgone at least one software purchase because their organization could build the functionality internally with coding agents.[2] This supports investigating a growing need while recognizing a serious build-versus-buy alternative. It does not measure the Lab's addressable market.

LangChain's June 2026 survey of more than 1,300 professionals reports 57% with agents in production, 32% naming quality as a leading barrier and approximately 52% running offline evaluations.[3] These are findings from a vendor's respondent sample, not population estimates or evidence that these respondents would buy this product.

LangSmith already documents custom code evaluation and regression tests, while Promptfoo documents evaluation, red teaming and CI use.[4][5] The Lab must demonstrate a useful improvement over those tools or the buyer's own checks, including integration and maintenance effort.

## One product across sectors

The common unit is a workflow release decision. For each workflow, the proposed product records what the agent claimed, which action it attempted, the authority it had, the observed effect and what can be verified. Industry-specific checks must describe the actual business rules and trustworthy evidence source.

| Layer | Reusable responsibility | Current position |
| --- | --- | --- |
| Evidence format | Preserve claims, actions, outcomes, provenance and uncertainty | Existing RARB records and a separate synthetic workflow schema; a stable cross-workflow API remains proposed |
| Verification engine | Evaluate frozen rules and return a reasoned decision | RARB verifiers and one support-ticket closure implementation exist; general-purpose adapters remain proposed |
| Workflow packs | Version rules, controls, reference outcomes and replay instructions | Repository-agent tasks and a synthetic support example exist; industry packs need design and validation |
| Connectors | Obtain authorized events and bind receipts to the actual system | Authenticated customer connectors are not implemented by this branch |
| Team product | Compare releases, review unresolved cases and retain evidence with access controls | Customer-ready collaboration, identity, retention and billing remain proposed |

The existing workflow verifier is deliberately limited to `close_ticket` and synthetic bundles. Renaming its fixtures as healthcare, finance or retail would not establish support for those sectors. A real connector must establish receipt authenticity, completeness and effect identity. An application trace alone may not prove that a remote action occurred.

## Expansion order

| Priority | Buyer/workflow | Reusable checks | Additional evidence required |
| --- | --- | --- | --- |
| First | Engineering leads at SaaS/software companies or coding-agent integrators | Repository task contracts, qualified verifiers, retained failures and replay | Buyer-approved task family, reviewed execution isolation, assisted installation, independent cases and accepted price |
| Next | Support and internal-approval agents | Permission, approval, duplicate effect, unsupported completion, unresolved evidence | Authenticated staging connector, authoritative receipts, buyer-owned contract and independent cases; current example is offline only |
| Next | E-commerce operations: order changes, returns or refund approvals in staging | The same authorization and effect checks | Domain rules, correct transaction/state evidence and a buyer willing to reuse the product |
| Next | Logistics and procurement: shipment or purchase-order updates | Authorization, allowed state changes, replay and duplicate detection | Cross-system event mapping and reviewers who understand the workflow |
| Later | Financial operations: invoice approvals and reconciliation | Separation of duties and evidence of allowed changes | Qualified domain review, security and contractual controls; no autonomous real-money release in the first offer |
| Later | Healthcare administration: appointment and administrative-record workflows | Access boundaries and authorized state changes | Healthcare-specific review and data controls; clinical decisions are outside the proposed initial product |

Software/repository-agent evidence is the first commercial entry point. Support/approval workflows and other sectors are later expansion hypotheses. A new sector proceeds only when at least two independent teams need the same pack, its connector can be reused, a qualified reviewer accepts the rules and someone accepts a paid scope. These are proposed internal expansion gates, not observed demand.

## What a multi-billion-dollar claim would require

Annual addressable spend equals the number of eligible buying organizations multiplied by a validated annual budget for this product category. Count each organization once across sectors. Exclude teams without relevant agents, budget, observable outcomes or a feasible procurement route.

For scale intuition only, 50,000 eligible organizations at $40,000 annually would imply $2 billion of annual addressable spend. Neither input is verified. This arithmetic is not our TAM, expected revenue or valuation. The hypothetical enterprise budget is also not the current $5,000 pilot or $1,000 monthly service price.

The immediate research task is a sourced organization-level list, qualified buyer interviews and observed price acceptance. Use those to estimate reachable spend first. Do not add the whole AI, cybersecurity, healthcare and financial-services markets together. The proposal can explain a large expansion opportunity while keeping the numerical market claim open.

## A product that can spread

The paid pilot buys learning and implementation. Growth beyond founder capacity requires the second buyer to install a useful part of the product with less assistance. Track support hours per activated organization and reject a scaling claim if they grow roughly one-for-one with customers.

The proposed adoption path is:

1. A developer runs a local diagnostic against synthetic or authorized staging evidence without creating an account or sending private traces to the Lab.
2. The report identifies an inspectable mismatch or explicitly states that the available evidence is insufficient. It must never manufacture an issue to encourage purchase.
3. The developer adds the same check to the next release and shares a redacted result with a teammate.
4. A team buys collaboration, recurring workflow maintenance or private deployment because repeated use creates value.

Start with coding-pilot installation documentation, reviewed execution isolation, a packaged CLI and one buyer-informed repository adapter. Add an opt-in CI integration that can annotate a release using the repository owner's permissions. A report should export locally by default. Public links or badges require explicit publication permission and should describe the exact check, never certify broad safety.

Publish worked failure cases with reproduction instructions, then distribute through the developer and integration communities that use the selected adapter. Obtain permission for customer examples. No promotion or outreach has been sent through this strategy update.

Free local verification can reduce adoption friction. Possible paid products include team review/history, managed recurring checks and private deployment/support. These capabilities and prices require validation. Keep optional fresh-model testing separately metered with user budgets; do not make free adoption depend on unlimited provider spend. Existing pilot/service pricing remains an experiment, not a SaaS price list.

## First 90 days and later beta acceptance criteria

The first 90-day targets are 15 buyer interviews, three assisted staging installs and one signed paid scope or budget-authorized LOI. They precede a scaled beta; they are not completed milestones or a sales forecast. The unchanged base model starts paid delivery in month 4 and recurring service in month 6.

After initial paid validation, a separate proposed beta could measure a cohort of 20 qualified organizations, with eligibility and observation dates recorded. This later experiment is not an additional first-90-day obligation. Its thresholds below are learning targets, not forecasts or achieved milestones:

| Question | Proposed acceptance evidence |
| --- | --- |
| Can a team start without the founder? | At least 10 of 20 complete installation and a check on their own authorized staging evidence; record abandoned attempts and assistance time |
| Is initial value accessible? | Median time to an interpretable first result under 30 minutes among successful activations, alongside completion rate and the slowest attempts |
| Does the product get used again? | At least 5 of 20 rerun it for a subsequent real release within the observation window; report actual release opportunities and right-censored cases |
| Does it improve a decision? | A buyer accepts incremental detection or reduced review effort against its normal baseline under the existing pilot protocol |
| Will someone pay? | At least two organizations accept a paid scope or product offer; keep signatures, invoicing and collected cash distinct |
| Can it scale economically? | Record per-account infrastructure, provider, support and onboarding costs; show a credible positive contribution at the tested price |

Use an initial 30-day observation window after onboarding the cohort. Organizations without a subsequent release opportunity remain in the full-cohort count and are separately identified; they are not silently dropped. Small samples justify another experiment, not a claim of product-market fit. GitHub stars, visitors and demo clicks do not substitute for activation, repeat use or payment.

If installation fails, simplify the adapter. If teams activate but do not return, investigate whether checks affect a recurring decision. If they return but refuse payment, revise the buyer or paid value. More sector pages will not answer those questions.

## Release readiness and a possible traffic spike

An offline developer preview can be distributed before a hosted customer service is ready, with explicit experimental scope and trustworthy installation instructions. A hosted launch needs tested authentication, tenant separation, receipt provenance, secret handling, deletion/retention, error recovery and applicable security closure. PR #34 remains a separate security dependency as of this review.

If hosted evaluation is introduced, bound concurrency and job duration, queue work, enforce per-organization quotas and cost limits, and stop paid model calls at the configured cap. Test retries, duplicate jobs, exhausted quotas and partial failures against a stated workload. Start with a documented capacity limit and expand after measurement. No load testing, burst capacity, incident coverage or hosted production readiness is established by this document.

A usage surge cannot be promised. The useful goal is a product that customers can adopt, revisit and recommend without unsustainable costs or founder assistance. Distribution experiments and retention evidence should determine whether to widen the launch.

## Application timing

Proceed toward the START application in parallel with a focused beta. The published route explicitly accepts PoC/MVP applicants.[1] Waiting for five sectors or a surge is unnecessary. Submitting before the founder can answer legal identity, finances, Qatar presence, hiring and time commitment accurately is also unnecessary. Resolve those [submission gates](SUBMISSION_GATES.md), export the required attachments and describe current capabilities and future expansion separately.

The investment story is a reusable verification product with a specific first customer problem, early technical evidence and a measurable path to repeat use. The committee should see how capital removes an adoption or delivery bottleneck. It should not be asked to treat an unverified TAM or several proposed sector packs as traction.

## Sources reviewed 30 October 2026

1. [Startup Qatar Investment Program](https://startupqatar.qa/en/investment-program).
2. [McKinsey, The state of AI in 2026](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai), published 25 August 2026.
3. [LangChain, State of Agent Engineering](https://www.langchain.com/state-of-agent-engineering), dated 12 June 2026.
4. [LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types).
5. [Promptfoo introduction](https://www.promptfoo.dev/docs/intro/).

Sector prioritization, architecture, price hypotheses and beta thresholds are the Lab's proposed strategy, not conclusions asserted by those sources.
