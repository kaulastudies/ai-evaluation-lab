# AI Evaluation Lab: release checks for coding agents

Pitch narrative aligned with the redesigned Startup Qatar attachments, 30 October 2026. The core story has 13 slides and two evidence/financial appendix slides. This is presentation source; exporting it does not resolve the factual submission gates. Commercial activity, customer installation and Qatar operations remain proposed.

## 1. Release checks for coding agents

AI Evaluation Lab helps engineering teams check whether an AI-generated change satisfies the agreed task contract. **ProofGate** is the existing coding-agent demonstration, built on retained repository-agent attempts. AI Evaluation Lab is the company/project identity; ProofQ and other research prototypes are separate portfolio work.

Rama Chandra Malayanur leads the work as a founder and independent engineer based in India. [Public demonstration](https://kaulastudies.github.io/ai-evaluation-lab/proofgate/) · [Repository](https://github.com/kaulastudies/ai-evaluation-lab).

## 2. Passing tests can still hide a broken task

In the recorded AP-005 example, a generated record-transformer change passed public tests while silently dropping inactive rows. The qualified verifier rejected it because the frozen task contract required preservation of every input row. A later recorded repair passed the bounded verifier.

This is a synthetic repository task and historical inference, not a production incident. It demonstrates the difference between passing a test and satisfying the intended contract. The commercial question is whether that distinction changes a buyer's release decision enough to justify the cost of additional checks.

## 3. Verification matters to developer trust

In the 2026 Stack Overflow trust question, 48.0% of 14,304 respondents selected trust conditional on easily verifying outputs; 6.6% selected trust extending to important work decisions. This self-selected survey is an industry signal to investigate, not evidence of Lab demand, TAM or willingness to pay. No cross-year comparison is made.

Source: [Stack Exchange Inc., Trust in AI tools, 2026 Developer Survey](https://survey.stackoverflow.co/2026/ai/data/ai-trust), response data under ODbL 1.0; checked 30 October 2026.

## 4. Make the release decision inspectable

1. **Define:** freeze a task contract and challenge its verifier with negative controls.
2. **Check:** inspect the candidate change and run bounded contract checks.
3. **Review:** retain PASS, FAIL and HOLD outcomes with artifacts and replay instructions.

The working demonstration is a coding-task workflow. Customer installation, reviewed execution isolation, reusable repository adapters and CI packaging are next product work. The public runner is not a production sandbox.

## 5. Fifty-two retained attempts across five tasks

The public RARB record contains **52 attempts: 44 VERIFIED_PASS, 5 VERIFIED_FAIL and 3 HOLD**. In that selected set, **3 of 46 attempts with an explicit success claim and passing public tests** were rejected by the verifier. The sample does not estimate an industry failure rate.

The 30-trial AP-001 experiment is included in 52; do not add it again. Seventeen configured critical mutations were rejected in retained verifier-qualification results. See [EVIDENCE_LEDGER.md](EVIDENCE_LEDGER.md) for denominators, provenance and limits. These are technical results, not customer traction.

## 6. One engineering team, one release decision

First buyer hypothesis: **the engineering lead at a SaaS/software company or coding-agent integrator** with a recurring agent-generated code workflow, authorized test artifacts and a budget owner.

The proposed pilot covers one repository task family and compares the added checks with the buyer's existing tests and review process. A four-week delivery scope is proposed once access, security and independent review are ready. Repeat use on a subsequent release, actual effort and willingness to pay determine whether to continue. No buyer, savings or demand has been validated by this package.

## 7. Win on useful evidence and delivery

Internal tests and CI already provide assertions, logs and code review. LangSmith documents datasets, custom code evaluation and regression testing; Promptfoo documents assertions, evaluation and CI integration.

The proposed reason to choose the Lab is the work required to design, qualify and review trustworthy checks for a specific release decision. The pilot must demonstrate incremental findings or lower review effort after including installation and maintenance cost. No unique-feature monopoly or comparative ROI is claimed.

Sources checked 30 October 2026: [LangSmith](https://docs.langchain.com/langsmith/evaluation-types), [Promptfoo](https://www.promptfoo.dev/docs/intro/).

## 8. Start with code; expand through repeat use

Coding-agent checks are the first commercial entry point. Support and approval actions are a later extension, illustrated by a **separate offline synthetic prototype**. Authenticated connectors and customer deployment for that extension are not implemented here. Commerce, procurement and administrative workflows would need their own domain rules and validation.

The long-term product hypothesis is reusable verification with less founder assistance per account. The market formula is qualified buying organizations multiplied by validated annual spend; neither input currently supports a measured TAM. See [PLATFORM_STRATEGY.md](PLATFORM_STRATEGY.md).

## 9. A paid pilot first, recurring release support next

| Offer hypothesis | Price | Direct economic cost | Contribution before overhead and tax |
| --- | ---: | ---: | ---: |
| One bounded pilot | $5,000 | 60 hours × $50 + $500 review + $250 compute = $3,750 | $1,250 / 25% |
| One recurring workflow service | $1,000/month | Eight hours × $50 + $100 compute = $500 | $500 / 50% |

No customer has accepted these prices in the evidence used for this pack. Current pricing describes a bounded service. Software scale requires reusable contracts and lower delivery/support effort per account; prospective team features and private deployment are unvalidated. See [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md).

## 10. Turn a public example into a repeat release check

| Period | Proposed target |
| --- | --- |
| Days 1–30 | 15 buyer interviews; identify three teams with the same recurring release problem |
| Days 31–60 | Three assisted staging installs; measure setup effort and compare buyer-authored cases |
| Days 61–90 | One signed paid scope or budget-authorized LOI; freeze acceptance rules and delivery cost |

These are targets, not completed work. The unchanged base financial scenario starts paid delivery in **month 4** and recurring service in **month 6**. A staging install or LOI is not invoiced revenue or collected cash. See [PILOT_PROTOCOL.md](PILOT_PROTOCOL.md).

## 11. Engineering evidence and execution capacity

Rama leads the Lab's implementation, experiment execution and evidence curation. ProofGate and the retained evaluation pipeline provide inspectable evidence of that work. His [Periskop Jest 30 contribution](https://github.com/backstage/community-plugins/pull/10964) was merged by Backstage Community Plugins on 22 September 2026. An accepted contribution is individual execution evidence, not endorsement of this venture.

The founder profile supplies relevant operating context. Independent review, customer delivery and funded local capacity remain needs to address. Mentor acknowledgments, collaborators and AI review workstreams are not employees or committed cofounders. Actual availability and Qatar presence remain founder decisions. See [FOUNDER_PROFILE.md](FOUNDER_PROFILE.md).

## 12. Build a Qatar validation and delivery base

The proposed first local engagement is a buyer-owned coding-agent workflow with a software team or integrator. Seek relevant introductions, develop evaluation engineering and independent-review capacity when funded demand supports it, and confirm establishment terms before commitments.

No Qatar customer, partner, local hire or relocation is committed. Arabic-English evaluation remains an expansion hypothesis requiring a real use case and a qualified reviewer. The [operating plan](QATAR_OPERATING_PLAN.md) separates proposed activity from written programme requirements. Fee waivers do not mean free operations.

Source: [Startup Qatar START](https://startupqatar.qa/en/investment-program), checked 30 October 2026.

## 13. Fund validation, then earn the next stage

The planning scenario begins with **$20,000** inside a conditional **$100,000 twelve-month ceiling**: validate with $20,000, deliver with a proposed $30,000 second stage, and consider up to $50,000 for repeatability. These amounts are not founder-approved investment terms or a funding offer.

Later releases depend on buyer evidence, accepted independent review, a quoted Qatar setup, and paid continuation or a second paying buyer. Recalculate and reduce later capital for collections and actual costs; stop when gates fail. The existing public $10,000 research request is separate, and shared costs must be allocated only once. See [FINANCIAL_PLAN.md](FINANCIAL_PLAN.md).

The requested next decision is technical and commercial diligence, with a proportionate funded validation stage if eligibility and terms fit. A broader investment recommendation depends on demand, repeatable delivery and compatible founder commitments.

## Appendix A. Evidence and security boundaries

Historical model attempts, source-exact replay, original synthetic controls, plans and customer outcomes are different evidence classes. The 12 support-workflow controls are separate from the 52 model attempts. Hashes bind retained bytes; they do not prove a real external effect. Security remediation PR #34 remains a separate open dependency as of this review. No production enforcement, general certification or independent human audit is claimed.

## Appendix B. Financial scenarios

| Twelve-month measure | Base hypothesis | Downside |
| --- | ---: | ---: |
| Pilots / recurring customer-months | 9 / 16 | 3 / 1 |
| Invoices / cash collected | $61,000 / $52,000 | $16,000 / $10,000 |
| Operating cash cost | $85,550 | $79,550 |
| Peak unfinanced cash need | $33,550 | $69,550 |

These are planning assumptions, not forecasts or historical accounts. Actual revenue, cash, funding and liabilities remain unreconciled. The [jury review](JURY_REVIEW.md) and [submission gates](SUBMISSION_GATES.md) retain the unresolved investment questions.
