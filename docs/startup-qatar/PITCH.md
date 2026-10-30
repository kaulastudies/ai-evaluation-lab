# AI Evaluation Lab: verifiable release checks for AI agents

Pitch narrative for Startup Qatar START. Prepared 30 October 2026. These sections are presentation source, not an exported pitch-deck attachment. All proposed commercial and Qatar activity requires validation.

## 1. The product

AI Evaluation Lab helps an engineering team determine whether a tool-using agent completed a defined workflow within its permissions. The release evidence records the task contract, the agent's claim, the observed outcome and the verification result. Missing evidence remains visible.

The first proposed commercial workflow is support-ticket closure that requires approval. The buyer is the engineering owner responsible for releasing that automation. The existing ProofGate demonstration shows the Lab's verification approach on repository-agent tasks.

## 2. The problem we can demonstrate

A passing public test or an agent's success message can disagree with the underlying task contract. In the Lab's retained repository-agent evidence, 3 of 46 attempts with an explicit success claim and passing public tests were rejected by the qualified verifier.

This is a result from a small, selected synthetic task set. It does not estimate failure prevalence in deployed enterprise agents. The commercial question is whether checking these disagreements reduces a buyer's release risk or review effort enough to justify a paid engagement.

Source: [evidence ledger](EVIDENCE_LEDGER.md) and its reproducible snapshot.

## 3. What the buyer receives

A proposed pilot produces a frozen contract for one workflow, a control and held-out test set, a machine-readable report and reproducible regression instructions. Each result preserves the distinction between the agent's claim, a requested action and evidence of the resulting effect.

The buyer can inspect why a case passed, failed or remained unresolved. The pilot measures missed violations and false alarms alongside review time. It does not promise a generally safe agent or automatic compliance certification.

## 4. What works today

The public repository contains five RARB tasks and 52 retained attempts: 44 verified passes, 5 verified failures and 3 holds. The 30-trial AP-001 repeated experiment is included in those 52 attempts. Seventeen configured critical verifier mutations were rejected in the retained qualification results.

ProofGate exposes existing evidence for inspection and replay. This branch adds a separate offline support-workflow demonstration. That demonstration contains synthetic records and makes no fresh-model or customer-deployment claim.

These results support technical diligence. Independent human evaluation and commercial validation remain open.

## 5. First customer and route to revenue

Start with a small engineering team releasing an agent that changes support records and can provide authorized test data and observable action receipts. The proposed purchase is a fixed-scope evaluation sprint for one workflow.

The pricing hypothesis is US$5,000 for the first pilot, followed by an optional US$1,000 monthly regression service with a limited workload. These prices have not been accepted by a buyer. The [commercial plan](COMMERCIAL_PLAN.md) specifies the discovery questions, cost assumptions and conditions for changing or stopping this offer.

## 6. Alternatives and differentiation

LangSmith already supports code evaluators and regression testing. Promptfoo already supports model/application evaluation, assertions and CI integration. A buyer may also write ordinary tests and inspect logs without buying a new product.

The proposed reason to choose the Lab is the engineering and evidence package for one difficult workflow: qualified checks, explicit unknowns, reproducible failure artifacts and a measurable reduction in release review effort. The pilot must demonstrate incremental value against the buyer's current tools. A generic evaluation dashboard alone would provide insufficient differentiation.

Sources checked 30 October 2026: [LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types), [Promptfoo introduction](https://www.promptfoo.dev/docs/intro/).

## 7. Why Qatar

Startup Qatar's START route supports PoC/MVP companies planning Qatar operations and includes AI/ML and B2B SaaS among its priority sectors. This makes it a relevant funding and market-entry route for the proposal.

The proposed local contribution is workflow-verification capability that a Qatar engineering team can operate and audit. Arabic-English workflow tests could add value after a qualified language reviewer and a local design partner agree on a real use case. Neither a reviewer nor a partner is secured by this proposal.

The [operating plan](QATAR_OPERATING_PLAN.md) makes incorporation, local hiring, deployment location and founder presence conditional on written terms and founder decisions. Fee waivers do not establish a zero-cost launch.

Source: [official investment program](https://startupqatar.qa/en/investment-program), checked 30 October 2026.

## 8. The next 90 days

The next milestone is an agreed workflow and a paying or budget-authorized pilot, followed by a comparison against the buyer's existing release process. Discovery must establish a named budget owner, permission to use the evidence and the operational cost of current failure/review.

Engineering work then freezes the acceptance rules before evaluation and retains failures. Independent case authorship and blinded review reduce the risk of testing only what the verifier already handles. The [pilot protocol](PILOT_PROTOCOL.md) defines what counts as success and when to stop.

## 9. Capital tied to evidence

The [financial model](FINANCIAL_PLAN.md) explores an indicative US$100,000 funding ceiling for a conditional 12-month plan, beginning with a proposed US$20,000 validation stage. This is a planning scenario, not a founder-approved funding request, valuation, term sheet or promise of program funding.

Later spending depends on customer evidence and written operating costs. The model separates cash collections from invoicing, founder draw from economic labor cost, and projected revenue from historical actuals. Any funded public research overlap must reduce the corresponding commercial funding need.

## 10. Founder and execution capacity

Rama Chandra Malayanur leads AI Evaluation Lab. The public repository provides inspectable implementation, retained experiment artifacts and verification code. The strongest founder evidence is the work itself.

The business remains founder-dependent. The first plan must fit real founder availability and leave room for customer discovery, support and review. Proposed specialist reviewers and local hires must remain unfilled roles until agreed and funded. See the [public founder profile](FOUNDER_PROFILE.md).

## 11. Risks that determine the investment decision

Customer demand is unproven. Existing tools may already solve enough of the problem. Evidence from a few synthetic workflows may not transfer to customer systems. Receipts supplied by an untrusted system cannot establish real-world truth merely because their hashes match. Security remediation in PR #34 remains open and unmerged as of this review.

The proposal addresses these risks with a narrow pilot, explicit trust assumptions, a comparison baseline and staged spending. No document substitutes for customer evidence or an independent security review.

## 12. The decision requested

Advance the project to technical and commercial diligence, with a defined first-pilot milestone and a proportionate first funding stage if terms and eligibility fit. A broader investment decision should follow evidence of buyer demand, viable delivery cost and an agreed Qatar operating commitment.

The [jury review](JURY_REVIEW.md) records the objections that still need answers. The [submission gates](SUBMISSION_GATES.md) identify unresolved facts before this narrative becomes an application.
