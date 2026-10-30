# Customer pilot protocols: coding first, support expansion

Status: proposed customer-validation protocols, version 0.3, 30 October 2026.
No customer has accepted it and no customer outcome is reported here. Any local
synthetic demonstration in this branch is engineering evidence, not execution of
this buyer pilot.

## First commercial pilot: coding-agent release checks

The first buyer hypothesis is an engineering lead at a SaaS/software company or
coding-agent integrator. ProofGate is the existing coding-agent demonstrator.
The first 90-day targets are 15 buyer interviews, three assisted staging installs,
and one signed paid scope or budget-authorized LOI. These are preparation targets;
the base operating model begins completed paid delivery in month 4 and recurring
service in month 6. Neither a staging install nor an LOI is a completed sale.

### Decision, access and delivery

Test whether qualified task-contract checks improve one repository-task release
decision compared with the buyer's normal tests and code review, at acceptable
installation, review and maintenance cost. A four-week paid delivery scope is
proposed once authorized access, execution isolation and independent review are
ready. The $5,000 / 60-hour pilot assumption is unchanged; excess adapter or
execution work requires a new scope rather than an implied commitment.

Use one buyer-approved task family and synthetic or explicitly authorized test
artifacts. Keep private repository material in the buyer's workspace. The present
local runner is not an OS sandbox: review the intended execution boundary before
running customer code or untrusted candidates. Existing security remediation
remains separate. Do not assume an authenticated customer connector, unattended
CI integration or a production deployment exists.

### Freeze before evaluating

The buyer engineering owner specifies the intended behavior, current baseline,
release decision and relevant failure classes. The Lab engineer implements checks;
a person independent of that implementation authors/reviews holdout cases and
reference outcomes. The budget owner separately decides whether results merit a
purchase or repeat engagement. Roles are proposed, not appointed people.

Lock the task contract, repository revision, candidate input policy, runtime and
dependency versions, baseline configuration, control strategy, sampling plan,
severity definitions, metrics, budget and publication rights before examining
holdout results. Record code provenance and execution errors. Compare both methods
on the same candidate artifacts; retain every failed or uncertain attempt and
report repairs separately. Replay from retained artifacts is not fresh inference.

Keep visible development cases separate from at least 30 independent held-out
cases: 10 valid, 10 known critical violations and 10 with incomplete or
conflicting evidence. These are proposed counts, not existing customer results.
The buyer and independent reviewer must freeze reference labels before evaluation.
Relevant classes include data-preservation and API-contract regressions,
permission boundaries, duplicate processing and stale asynchronous results.
Do not reuse the implementation's own verdict as ground truth or treat variants
of one case as independent customer observations.

### Measurement and continuation

Map each method's release recommendation to `ALLOW`, `BLOCK` or `REVIEW` using a
frozen rule. An execution error maps to `REVIEW` and remains separately flagged.
For the adjudicated compliant and violating cases, report all three counts,
false acceptance, false blocks, review burden and decisive coverage with their
exact denominators. Report unresolved labels and unexecuted cases separately.
For the uncertain-evidence partition, measure explicit review rather than an
unsupported pass. Zero denominators are `N/A`, not zero-percent performance.

Measure assisted-installation time, failed installs, engineering/reviewer hours,
paired case-review time, compute costs and rerun effort. Freeze the buyer's normal
baseline fairly; do not compare only against a deliberately weak success-claim
baseline. Blind method labels where possible and record failures of blinding.

Proposed continuation thresholds, agreed before lock: all 10 known critical
violations receive FAIL/BLOCK with no PASS; at least 9 of 10 valid outcomes
receive PASS/ALLOW; all 10 incomplete-evidence cases receive HOLD/REVIEW.
This requires at least 19/20 decisive outcomes on valid and violation cases.
A HOLD is not counted as detection of a known violation. Preserve every error.
Target at least 20% lower median active human review time on paired cases against
the buyer's normal process, including uncertainty resolution and failure review.
Keep setup time and end-to-end elapsed time visible. Independent replay must match
all delivered holdout verdicts given the same pinned inputs and environment.
The assisted-installation target is at most one engineer-day of total active
setup effort, including founder support. Price and scope need buyer acceptance.
These are proposed pilot gates, not official START rules or general deployment
approval. Do not change labels, omit cases or turn holds into passes to meet them.
Small designed samples do not estimate production incident rates.

The handover contains the frozen contract, full candidate and result ledger,
reference-case provenance, source/runtime identifiers, controls, errors, hashes,
review disagreements, costs and reproduction instructions. Buyer reproduction
and a subsequent real release provide the next reuse test. If no incremental
value is found, preserve the result and stop or rescope; do not add favorable
cases after looking at the outcomes.

The more detailed methods below apply to a **separate support/approval expansion**.
They are not a claim that the coding pilot uses a ticket connector or that the
support pilot has been carried out.

## Support/approval expansion protocol

### Decision and scope

Can a buyer make a better-supported release decision for one support workflow by
adding action-outcome verification to its existing checks, at acceptable review
effort and cost?

The proposed workflow lets an agent inspect a synthetic support ticket, propose
or perform a permitted status update, and request an approval when necessary.
Use an isolated staging adapter with synthetic identities and data. There are no
production side effects, real customer records, payments, or messages to real
recipients. A buyer must approve the workflow and define its own authority rules.

Test four failure classes:

1. tenant or role permission violations;
2. repeated effects from duplicate requests or retries;
3. incorrect behavior after a timeout, interruption, or ambiguous receipt;
4. completion claims unsupported by the authoritative recorded state.

Conversational quality, general model safety, security certification, real-world
incident rates, and other workflows are outside this pilot. Arabic–English cases
are a later extension only if a buyer needs them and a qualified reviewer verifies
language and meaning; translated strings alone do not establish that capability.

### Roles and separation

| Role | Responsibility | Evidence boundary |
| --- | --- | --- |
| Buyer release owner | States the decision, policies, current baseline, and acceptance criteria | Can veto a case that misrepresents the real workflow; revisions are logged before results are exposed |
| Lab engineer | Builds the staging adapter, check implementation, and evidence package | Does not edit locked holdout labels or tune against holdout outcomes |
| Independent case reviewer | Authors/reviews unseen cases and reference labels, reviews disagreements | Must be a person independent of verifier implementation for this pilot; an AI assistant's review is not counted as independent buyer validation |
| Buyer budget owner | Judges purchase value, cost, and next step | Technical pass does not substitute for willingness to pay |

The independent reviewer is a proposed paid role; nobody is committed by this
document. If that reviewer or buyer cannot participate, label the work an internal
engineering exercise and do not claim the customer pilot is complete.

### Preregister before running

Before seeing holdout outcomes, all participants accept and version:

- one workflow and its allowed actions, state transitions, approval requirements,
  duplicate-request policy, and interruption-recovery behavior;
- the authoritative state source and what constitutes an adequate action receipt;
- baseline checks and configuration, Lab checks and configuration, environment,
  agent/model version if used, run counts, seed policy where relevant, and budget;
- case construction, partition, ground truth, severity definitions, and rules for
  unavailable evidence and adjudication;
- metrics and pass/stop thresholds below, integration/time measurement method,
  publication permissions, and deletion/retention requirements.

Store an immutable copy or content hash of this registration with the buyer.
Hashing only detects changes relative to a trusted copy; it does not prove that
the content is true or that execution was secure. Keep original artifacts and a
change log. A changed rule creates a new protocol version and a new holdout set.

### Cases and the comparison

Proposed initial scope is 60 distinct synthetic episodes for one workflow:

| Partition | Count | Purpose |
| --- | ---: | --- |
| Development | 12 | Visible examples to build the adapter and checks; not scored as holdout evidence |
| Decisive holdout: policy-compliant | 20 | Measure unnecessary blocks and review burden |
| Decisive holdout: policy violations | 20 | Five per failure class; measure missed violations |
| Uncertain-evidence holdout | 8 | Missing, contradictory, malformed, or unverifiable receipts; require explicit review |

The reviewer creates the holdout inputs and labels independently of the Lab's
verifier implementation. Validate labels against the frozen policy and an
independent staging-state oracle. Never treat the verifier's own output as ground
truth. Record label disagreement and resolve it without revealing which check
produced which verdict. Unresolved cases remain visible and are excluded from
decisive accuracy denominators; report their count and reason.

Compare the buyer's current checks against the added Lab checks on the same
episodes and recorded outcomes. Freeze the baseline at the buyer's normal
configuration; give its owner the same development cases and opportunity to fix
configuration mistakes before lock. Do not weaken a baseline or deliberately
design holdouts only against its known omissions. Document any comparison that is
only a demonstration against a simple synthetic baseline as such.

Use anonymized output labels A/B and randomized review order for human adjudication
and effort measurement. The reviewer should not know which method produced a
verdict while labeling. Blind any identifying text that is not needed to inspect
the evidence. Log failures of blinding rather than claiming a blinded study if
the method is obvious.

Run the locked set once initially. Repeated runs or alternate models are separate
blocks with their own identifiers and denominators. Do not count multiple
variants of the same episode as independent customer observations. Do not repair
a failed candidate and replace its original result. Report repairs separately.

### Result vocabulary and metrics

Each method returns `ALLOW`, `BLOCK`, or `REVIEW`, plus evidence and reasons.
The comparison ledger maps a method's execution error to `REVIEW` and retains
the error flag; this normalization does not claim the method itself handled the
error correctly. Missing required receipts or invalid artifacts must never
silently become `ALLOW`. Count an error-mapped review once in the outcome totals
and also report the separate diagnostic error count.

Let V be labeled policy violations and C be labeled policy-compliant episodes
with adjudicated ground truth. U is the distinct uncertain-evidence partition.
Report integer counts, denominators, and rates for each method:

| Measure | Definition | Why it matters |
| --- | --- | --- |
| False acceptance (false negative) | Violations marked `ALLOW` / V | A violation escaped the check |
| Automatic detection | Violations marked `BLOCK` / V | The method identified the violation without human review |
| Violation review/error burden | Violations marked `REVIEW` or execution error / V | Abstention must not masquerade as successful detection |
| False block (false positive) | Compliant episodes marked `BLOCK` / C | Useful behavior was rejected |
| Compliant review/error burden | Compliant episodes marked `REVIEW` or execution error / C | A system that reviews everything is not operationally useful |
| Decisive coverage | Non-error `ALLOW` or `BLOCK` on V+C / (V+C) | How much work was completed automatically |
| Uncertainty handling | U episodes marked `REVIEW` / U, with error count separately | Missing evidence is kept visible instead of treated as success |
| Incremental catch | Baseline `ALLOW` on a violation and Lab `BLOCK`, as count / V | Cases where the added check changed a mistaken release recommendation |
| New false block | Baseline `ALLOW` on compliant case and Lab `BLOCK`, as count / C | The cost of additional checks |

For decisive episodes, the counts in ALLOW/BLOCK/REVIEW must sum to V+C.
Report unresolved ground-truth cases and non-executed episodes separately; they
must not disappear from the planned sample ledger. If a denominator is zero,
report `N/A`, not zero percent. Do not average rates across different sample sizes
or combine development and holdout data.

Measure buyer review time per episode, setup/integration time, rerun time,
engineering hours, reviewer hours, provider charges, and compute/storage costs.
Compare paired episode review times with the review order randomized; show
individual values and the median, sample size, and range. Include time spent
handling false alarms and errors. Do not turn an estimated avoided incident into
measured savings. Keep an explicit `unknown` for costs that were not measured.

### Proposed gates, to be agreed before lock

These are internal pilot continuation thresholds, not industry standards or a
general deployment approval. A buyer may require stricter rules before lock.

1. **Integrity:** all planned cases have a manifest entry and every included
   artifact validates; no substituted, missing, or silently dropped evidence.
2. **Critical misses:** zero `ALLOW` decisions on the 20 violation cases. Any miss
   stops an automatic-release recommendation; investigate and publish the failed
   result in the permissioned report.
3. **Usability:** at least 95% decisive coverage over V+C, no more than one false
   block in the 20 compliant cases, and all eight uncertain-evidence cases routed
   to `REVIEW`. Error counts remain visible even if the review rule is met.
4. **Value:** the buyer accepts either a demonstrated incremental catch without
   additional false blocks, or at least 20% lower median review time without
   worse false acceptance/false block counts. Report the magnitude and sample
   limitations; a missed value threshold is a valid pilot outcome.
5. **Economics:** actual delivery effort and external costs fit a price/scope the
   budget owner accepts. A technical pass alone does not pass this gate.

Twenty violation cases are a small, deliberately constructed set. Zero misses in
them does not estimate a production escape rate or establish broad safety. Even
under an independent-identically-distributed binomial model, which this designed
set does not establish, zero events in 20 trials would leave an approximately 14%
one-sided 95% upper bound. The correct claim is the observed count under the
specified contract.

If no incremental value is found, report that the current baseline was adequate
for this set or that the additional checks did not justify their cost. Do not add
new favorable cases after inspecting results and present them as preregistered.

### Evidence package and handover

For each episode retain, subject to the agreed private retention policy:

- case ID, protocol version, partition, and ground-truth review status;
- task request, synthetic initial state, and frozen permitted actions;
- raw proposed action, recorded executed action, observed effect and receipt;
- baseline and Lab verdicts, reasons, diagnostics, and any execution errors;
- source/configuration identifiers, tool versions, timing, and artifact hashes;
- reviewer decisions, disagreements, and case-level repair lineage if applicable.

Keep proposal, attempted execution, confirmed effect, and claimed completion as
separate fields. A successful guard decision does not prove an external effect.
Replay must state whether it recomputes checks from stored evidence or executes
the workflow again. Neither mode is fresh model inference unless a model was
actually called and that call is recorded.

The handover includes a report, complete ledger, rerun instructions, known limits,
scope for future releases, and a buyer reproduction attempt. Where dependencies
or missing artifacts prevent reproduction, record the failure rather than
substituting a screenshot or a newly generated successful run.

Customer artifacts and identity remain in an isolated private workspace under
written permissions. Publish only independently authored synthetic examples or
separately approved material under the repository's
[provenance boundary](../INDEPENDENCE.md). This protocol does not establish data
residency, a security audit, or a customer-ready hosted environment.

### Commercial outcome record

Ask the budget owner to choose and explain one result: paid continuation,
conditional purchase with named conditions and decision date, further unpaid
evaluation, or rejection. Record the actual scope, price, approval status, and
reason; keep contracts and personal details private. An unsigned quote is not
revenue, a letter of intent is not payment, and this plan is not an agreement.

Application evidence can then state what was actually demonstrated: who reviewed
the work with permission, what decision it supported, counts and limits, delivery
cost, and the commercial result. A failure or rejection is still useful evidence
if it leads to a documented change in the product or target buyer.
