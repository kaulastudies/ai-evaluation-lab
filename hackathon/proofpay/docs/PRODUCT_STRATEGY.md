# ProofPay product strategy

8 November 2026 · strategy and implementation recommendations, not a claim that the roadmap is delivered

ProofPay should earn the right to compete by solving one expensive operational problem well: keeping a business-approved purchase, its shared allowance and its actual payment outcome connected when execution is interrupted. The first contest is for the engineering team's workflow and operating console. Becoming a payment processor would be a later, separate business decision requiring considerably more than a second API adapter.

A large company is an ambition, not the current evidence. There is no established customer demand, revenue, partnership, valuation or superiority over PayPal or Stripe.

## The present product and its proof

Purchase Desk implements a single-merchant, USD workflow with a server-owned catalogue, owner approval, atomic allowance reservations, durable create/capture identities and checks against the original provider order. It includes explicit renewal of eligible expired approvals without changing the purchase, order IDs or reservation. Pre-dispatch cancellation can withdraw an untouched request, release its unused reservation once and retain its history. Rehearsal and PayPal sandbox are separate modes.

At this strategy checkpoint, 92 local tests passed, including 17 renewal, 20 pre-dispatch cancellation and two AI-provenance cases. The tests use synthetic provider/model records and mocked HTTP, with local process race/restart tests. The hosted application separately demonstrated rehearsal budget refusal, simulated capture response loss and reconciliation. Genuine PayPal sandbox OAuth and provider-adapter create/GET calls passed; the probe order was awaiting buyer action. Genuine model inference and the full sandbox buyer-approval/capture flow remain unverified. The API-key provisioning attempt returned no usable key.

This is implemented payment-operation software with a partially verified PayPal sandbox connection. It is not yet a verified end-to-end AI purchasing product. A screenshot, a configured connection or a passing synthetic test cannot close that gap.

## Compare against the incumbents accurately

The following facts come only from current official PayPal and Stripe sources, checked on 8 November. They are product documentation, not an independent comparison of performance.

| Capability | What the incumbents already provide | Implication for ProofPay |
|---|---|---|
| Agent commerce acceptance | PayPal Agent Ready supports ACP through Braintree and UCP through Braintree or PayPal Orders v2. Stripe offers agent wallets, embedded commerce, service bookings and machine payments. [1][2] | “Agents can pay” is not a unique proposition. Ordinary Orders v2 usage does not establish ACP/UCP compatibility. |
| Scoped authority and user approval | Stripe Link lets a customer approve a spend request before returning a one-time credential. Stripe Shared Payment Tokens can restrict the seller, currency, maximum amount and expiry. [3][4] | Do not claim that approval, merchant limits or expiry are absent from today's payment products. |
| Retry protection | PayPal documents request idempotency with API-specific support and retention. Stripe also documents idempotency, with differing API v1/v2 semantics. [5][6] | Benchmark against correct provider idempotency. A missing-response story alone is insufficient differentiation. |
| Platform infrastructure | PayPal's platform offering covers seller onboarding, multiple methods, FX, payouts and disputes; live access requires approval. Stripe Connect covers account onboarding, verification, charges, balances and payouts. [7][8] | A purchasing console is not equivalent to a payment platform or processor. These capabilities require substantial product and operating work. |

PayPal and Stripe may expand further into this application layer. Their public pages cannot prove that they lack an equivalent workflow or recovery feature. A customer's existing integration may already be sufficient. Test the buyer's actual alternative rather than selecting a weak comparison.

## Initial customer and differentiated hypothesis

Target an engineering lead at a B2B services software company that already integrates PayPal and has a named release delayed by approval, shared-budget or reconciliation work. Start with one cooperating merchant and a fixed digital-service catalogue. The studio purchasing reviews is the user story; the software company pays to integrate and operate it. This avoids pretending that merchant API credentials create an arbitrary-seller shopping wallet.

The proposition to test is:

> Keep your business approval and shared allowance attached to the original payment operation, and give an operator an inspectable answer when the outcome is uncertain.

Its possible value is faster integration and shorter investigation, not a claim to replace the provider's authorization or fraud systems. The combination may be useful even when the individual components are familiar. Defensibility would have to develop through maintained adapters, real failure cases, predictable upgrades and distribution—not through a generic approval screen or the word “proof.”

Use three measurable pilot hypotheses:

| Hypothesis | Pilot measurement | Failure signal |
|---|---|---|
| The integration removes repeated engineering work | Record hours against the customer's scoped in-house approach and repeat with a second team. | Every installation needs a custom state machine, or effort is unchanged. |
| Operators can resolve the supported cases faster | Give comparable reviewers at least five documented fault cases. Target median investigation below ten minutes and at least 50% improvement over the baseline. | Reviewers still need an engineer and direct database access for ordinary cases. |
| Ongoing maintenance is worth paying for | Offer a paid continuation after a completed pilot and record renewals. | Teams only want a one-time code copy or free advice. |

These targets are proposed acceptance criteria, not observed benefits. Any incorrect confirmation, extra provider dispatch or reservation error blocks release of the affected workflow. Zero failures in a limited suite is not a general reliability percentage.

## Product structure and visual direction

Aim for the clarity of a mature financial console: stable navigation, searchable records, precise amounts, readable timestamps and a clear next action. Use ProofPay's own identity and visual system. Do not reproduce Stripe's branding, trademarked assets or distinctive page composition.

Organize information around the operator's questions:

| Area | Operator question | Content available now |
|---|---|---|
| Overview | What needs my attention? | Active workspace allowance, reserved and paid amounts, unresolved operations and their ages. |
| Purchases | What was requested, and what can I do? | Searchable operation list and a selected purchase with current status, owner-approval expiry and permitted action. |
| Evidence | Why does the application believe this result? | Approved fields, provider verification snapshot, timestamps, model/rehearsal source and export. |
| Connections | Which external services are configured? | PayPal and AI configuration presence, mode explanation and access to the supported setup flow. |

These may be sections of the existing desk rather than four new pages. Configuration presence must not appear as successful external verification. Label the $300 figure “Workspace allowance,” not bank balance. Keep the rehearsal/sandbox mode visible on every screen. Use actual state rather than fabricated revenue charts, risk scores, uptime or payment volume. In a narrow prototype, a useful empty state is stronger than an invented chart.

## Three frontend improvements supported by the current API

These are recommendations for implementation. Existing actions should be reused; none requires a new payment authority or a fictitious provider integration.

### 1. A needs-attention queue

Use `GET /api/state` to sort and filter operations by approval needed, expired approval, buyer action, verification needed and confirmed. Show the purchase amount, state age from the recorded timestamps, held allowance and a single next action. Support search by item, operation and provider order ID.

Group `CREATE_UNKNOWN` without a stored order separately: explain that manual investigation is required instead of presenting a reconciliation button that cannot work. A stored, uncertain capture can offer the existing `/reconcile` action. Preserve server errors and refresh from server state after every mutation; frontend grouping does not grant authority.

Acceptance: a reviewer identifies the unresolved $180 operation and its next valid action within 15 seconds, sees that its allowance remains held, and cannot mistake it for a failed or paid purchase. This is a usability target to test.

### 2. An approval decision panel

Show item, merchant, amount, currency, current allowance impact, approval version and expiry together. Separate application owner approval from PayPal buyer approval. For eligible expired `APPROVED` or `ORDER_READY` states, present explicit reapproval through `/api/operations/:id/renew-approval`. Explain that the existing reservation and order remain unchanged.

Use the existing approval/create/capture actions for their respective states. A browser clock may label an apparent expiry, but the server remains authoritative. On a stale-version conflict, refresh and show what changed; do not automatically resubmit approval or capture. Renewal must not be offered as a remedy for uncertain payment or an expired PayPal order.

Acceptance: the owner can state the exact merchant and amount being authorized and distinguish reapproval from another charge. A conflicting concurrent action displays an understandable state update rather than a false success.

### 3. An approved-versus-observed evidence view

Fetch `GET /api/operations/:id/evidence` on selection. Display approved purchase fields beside the stored `verificationRecords` snapshot: order/reference identifiers, merchant, amount, currency and final capture state. Label missing evidence as “Not yet verified.” Show a mismatch only when an actual stored result supports it; do not invent an expected provider response.

Add the observation timestamp, request IDs and approval digest under expandable technical detail. Parse AI provenance from the recorded proposal event when present, displaying provider origin, requested/returned model and response ID without raw responses or credentials. Keep a clear “Rehearsal sample/rule” label for simulated proposals. Export the existing receipt rather than constructing a new client-authored confirmation.

Acceptance: a reviewer can trace approval to the checked provider record without reading raw event JSON. Simulated receipts remain visibly simulated, absent model provenance is not filled with a guessed model, and loading/error states never imply confirmation.

## Delivered interface checkpoint

The six-view workspace and pre-dispatch cancellation are privately deployed. Desktop checks cover navigation, purchase/evidence search, confirmed/cancelled filters, record inspection and cancellation accounting after reload. The evidence comparison described above remains a proposed deeper inspection view; the current Evidence screen presents events and exported server receipts. Local 360px/390px CSS-viewport inspection now covers the actual component and stylesheet with synthetic data, with a 768px tablet spot check. It led to corrections for cramped cards, table overflow and navigation scroll. Touch-device behavior and hosted mobile authentication are still unverified. See [hosted workspace evidence](../evidence/hosted-workspace-review.json) and [responsive review](../evidence/responsive-review.json).

## Roadmap to provider-independent operations

| Stage | Deliverable | Gate before expansion |
|---|---|---|
| Finish the PayPal slice | Genuine model proposal, native sandbox buyer approval, normal capture, response-loss recovery, hosted renewal and reproducible judge access. | Evidence from the actual application path, with no claim based only on local fixtures. |
| Repeat one customer workflow | A documented integration contract, pilot deployment, bounded support and the three operator improvements above. | Two paying teams can use substantially shared code and demonstrate measured value. |
| Add provider-independent operation records | Separate business intent and authority from provider-specific references, states, lookup and retention rules. | A second paying workflow needs portability and the contract does not erase meaningful provider differences. |
| Implement a second provider | A real test-mode adapter, independent evidence mapping, common conformance tests and explicit provider selection before execution. | Both providers pass their own supported normal/failure cases; customers pay for the additional capability. |
| Expand financial actions | Add a requested refund or invoice workflow with its own authority and accounting rules. | A paying buyer, defined operating ownership and verified recovery behavior for that action. |

Provider independence means a business operation has a consistent application contract while each adapter retains its own semantics. It does not mean switching providers after an uncertain charge. An unresolved PayPal attempt must be resolved or investigated on PayPal; rerouting it to Stripe could create a second financial effect. No automatic fallback is proposed.

## If direct payment processing becomes the goal

Owning the workflow can become a valuable business without becoming a processor. A decision to compete directly in processing would require a separate plan for merchant onboarding and verification, provider/acquirer or banking relationships, authorization and settlement systems, reconciliation of actual funds, fraud and loss ownership, disputes, refunds, reserves, support and geographic availability. Applicable licenses, registrations and compliance obligations depend on the business role and jurisdictions; they must be assessed before entering that role.

PayPal's platform documentation makes the sandbox-to-live approval boundary explicit, and Stripe Connect treats account verification and fund movement as distinct capabilities. [7][8] Those are useful examples of the operational scope. Adding a second API adapter, relabelling the workspace allowance as a wallet or drawing a settlement chart does not deliver it.

Do not announce processor parity, custody, payment-network access, guaranteed settlement, regulatory approval or a fee advantage without the relevant contracts, infrastructure and evidence. The product can compete for a particular buyer's software budget while remaining a customer of payment providers.

## Ninety-day commercial milestones

The following are goals, not traction. They align with the pricing hypotheses in [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md).

| Period | Commercial and product result to seek | Stop or narrow if |
|---|---|---|
| Days 1–30 | Finish the genuine external flow. Conduct ten qualified conversations after outreach authorization, obtain three scoped problems and seek two paid four-week pilots at the proposed $2,500 price. Test the operator console with at least two people unfamiliar with the implementation. | Fewer than three concrete problems emerge, or no qualified team accepts a paid proposal. |
| Days 31–60 | Deliver the first two pilots, track engineering/support hours, compare investigation tasks and record all failures. Package shared components rather than accumulating unrelated custom features. | Pilots repeatedly exceed the assumed 20 delivery hours or show no measured benefit. |
| Days 61–90 | Seek at least two paid continuations at a tested recurring price. Add a second provider only if a paying customer needs it and the first integration is repeatable. | Customers value only a one-time handoff, support costs defeat the price, or an incumbent's existing setup already solves the problem adequately. |

A billion-dollar outcome cannot be justified by this checkpoint. The credible sequence is an observed problem, paid use, repeated delivery, retention and sustainable economics. Preserve that sequence while designing the architecture to support a larger business if the evidence warrants it.

## Primary sources

1. [PayPal Agent Ready overview](https://developer.paypal.com/agent-ready/overview/) — live page updated 13 October 2026, including the Orders v2 path omitted by some older search snippets.
2. [Stripe agentic commerce documentation](https://docs.stripe.com/agentic-commerce) — current integration categories; availability varies by integration.
3. [Stripe Link Agent Wallet](https://docs.stripe.com/agentic-commerce/agents/link-agent-wallet) — approved spend requests and one-time credentials.
4. [Stripe Shared Payment Tokens, agent integration](https://docs.stripe.com/agentic-commerce/concepts/shared-payment-tokens.md?agent-seller=agent) — seller scoping and usage limits.
5. [PayPal idempotency](https://developer.paypal.com/api/rest/reference/idempotency/) — support and retention are API-specific.
6. [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests) — API-version-specific retry behavior.
7. [PayPal Platforms overview](https://developer.paypal.com/platforms/overview) — updated 3 November 2026; platform capabilities and live-approval requirement.
8. [Stripe Connect](https://docs.stripe.com/connect) — account verification, onboarding, payments, balances and payouts.

All eight sources were read on 8 November 2026. Feature lists do not prove comparative quality or customer demand. Current project evidence remains separately scoped in the local test artifacts, master handoff and application receipts.
