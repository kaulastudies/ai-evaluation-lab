# YC application research and differentiation

Primary sources reviewed 31 October 2026. Public examples illustrate communication, not an admissions formula. YC's private applications and internal selection reasoning are unavailable.

## What to learn from public YC material

| Source | Application lesson | How to apply it here |
| --- | --- | --- |
| [YC: How to Apply](https://www.ycombinator.com/howtoapply) | Explain the actual product and give specific evidence about the founders and insight | Lead with release checks for AI-generated code and the executable AP-005 failure, not a general AI-market introduction |
| [Dropbox's successful 2007 application](https://www.ycombinator.com/apply/dropbox) | A concrete user workflow, working software, named alternatives and candid remaining work make the proposal assessable | Describe exactly what the reviewer runs and who might pay. Dropbox's beta users and founder history are its evidence, not evidence transferable to this venture |
| [YC's successful founder-video examples](https://www.ycombinator.com/video) | A short founder explanation is separate from a product demonstration | Record an approximately one-minute founder-only introduction; use bullet prompts and natural speech. The existing product walkthrough does not replace it |

The Dropbox application describes a different product in a different market and period. Its acceptance does not establish that any particular feature, writing pattern or founder configuration causes acceptance. Our task is to make our own progress and uncertainties easy to inspect.

Suggested founder-video prompts, rather than a script: who you are and what you build; the engineering user; one patch that passed ordinary tests but failed the contract; what the demo does today; the next customer milestone. Speak only to your actual work and commitments.

## Competitive context

| Alternative and primary source | Existing capability | Our proposed narrow entry and what must be proved |
| --- | --- | --- |
| [Confident AI / DeepEval, YC company profile](https://www.ycombinator.com/companies/confident-ai) | Agent evaluations and production monitoring, including converting failure traces into evaluation cases | Focus on qualifying a coding-task verifier and retaining contract-level evidence. Demonstrate a useful gap in the buyer's current setup; do not claim failure-to-regression is unique |
| [Braintrust: CI/CD for AI](https://www.braintrust.dev/learn/ci-cd/v0) | Evaluation experiments and release thresholds | Deliver useful workflow-specific checks into the existing review process. CI gating alone is not differentiation |
| [Inspect](https://inspect.aisi.org.uk/) | Composable agent evaluations, scorers and sandbox support | Reduce customer work to qualify and maintain the task contract. A general evaluation runner is already available |
| [Mercor Research](https://www.mercor.com/research/) and [Archipelago](https://github.com/Mercor-Intelligence/archipelago) | Professional-work benchmarks and an agent evaluation harness | Begin with the engineering team's release decision and reusable verification artifacts. Do not describe data companies as merely labeling vendors or assume labs are the only possible buyers |
| Internal tests, mutation testing and manual review | The buyer can assemble and own its checks | Compare the same cases, reviewer time and maintenance cost. Stop if the internal alternative is adequate and cheaper |

Our working thesis is **qualify the checker before trusting its pass**. The demonstrable assets are explicit contracts, known-bad controls, retained failures and reproducible artifacts. None is a proven exclusive moat. Defensibility would have to develop through useful reusable packs, permitted failure cases, low installation cost and sustained customer use.

## Where ProofGate fits: guardrails, evaluations and human review

The founder supplied a graphic titled *Guardrails vs Evals vs Human-in-the-Loop*, attributed in the image to Raju Dandigam. It is a useful communication framework, not technical validation or evidence of a partnership. The image itself is not redistributed here.

| Function | Question it helps answer | Relationship to ProofGate |
| --- | --- | --- |
| Runtime guardrails | Should this input, output or action be allowed under a policy? | Complementary. ProofGate's coding-task demonstration does not implement a general prompt-injection defense |
| Evaluations | How did the system perform against specified cases and criteria? | This is the current product's closest category. ProofGate qualifies the task checker and retains evidence for the verdict |
| Human review | Should an accountable person approve, change or reject the proposed action? | A reviewer can use ProofGate's report. Automated approval routing into a human-review platform is a future integration, not a demonstrated feature |

[NVIDIA documents several guardrail types](https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/rail-types); [LangGraph's interrupt primitive](https://reference.langchain.com/python/langgraph/types/interrupt) supports pausing execution for external input. These functions overlap in real systems. Evaluations also run after deployment, release blocking requires an enforced gate, and human review needs adequate context and authority. No combination establishes universal safety.

The stronger positioning is: **We test whether the checks behind a coding-agent release decision reject known-bad code, and retain reproducible evidence for the reviewer.** This is more concrete than claiming an all-in-one agent safety platform.

A proposed integration sequence is to export the existing verdict and failed-gate evidence into one customer's CI review, retain human authority over merge/release, and make confirmed failures repeatable regression cases. Native LangGraph, NeMo, CrewAI or n8n integrations are not claimed. First measure whether the evidence changes a real review decision and reduces its cost.

## What makes this case assessable

The demo lets a reviewer test a concrete failure and its repair without credentials or a model bill. The ledger retains unfavorable results and separates missing information from zero. These are current product choices, not claims of superior accuracy to another vendor.

What remains weaker than an application with customer traction: no verified paid deployment is established by this repository, only five synthetic task families are covered, and setup cost is unproven. The best next improvement is a real buyer's accepted evidence and repeat use, not a larger headline market number.
