# ProofPay business pilot plan

Updated 8 November 2026. This is a proposed sandbox pilot, not a launched payment service or an offer that has been sold. There are no verified customers, revenue, partnerships or willingness-to-pay results. [QA](QA_REPORT.md) separates the current business increment from earlier deployment evidence.

## Product and first customer

ProofPay is an approval and payment-evidence desk for owner-led service businesses: small agencies, consultancies and studios that need to approve outside work, keep an allowance visible and investigate an uncertain payment. It sits around a payment provider. It does not replace PayPal or Stripe, hold customer money, provide a bank balance or offer arbitrary merchant purchasing.

The first pilot should involve one business owner, one department or cost-centre label and one controlled service catalogue. The present catalogue is synthetic and sandbox-only. Test whether this workflow solves a real approval or investigation problem before adding more providers, currencies or enterprise features. A business name is reporting metadata, not verified legal identity; a department label creates no additional user, role or separate budget.

## What the owner can do

| Capability | Current behavior | Pilot value to test |
|---|---|---|
| Business settings | Save business name, department label and a default USD allowance for future workspaces. Stale profile versions cannot overwrite a newer save. | The owner can set up the desk without editing code. |
| Saved workspace context | New workspaces retain the business name, department, profile version and allowance used at creation. Later settings do not rewrite them. | Earlier decisions remain understandable after defaults change. |
| Workspace history | Lists only the owner's saved workspaces. Selection is blocked while the active workspace has a reserved or uncertain purchase. | Review earlier work without hiding an unresolved operation. |
| Purchase decisions | Approve, renew eligible approval, cancel before dispatch and inspect the recorded outcome. | Replace a fragmented approval/investigation process with one inspectable operation. |
| CSV and evidence | Export all loaded purchases in the active workspace, with business snapshot, mode, source and status; inspect versioned evidence separately. | Produce a usable review handoff. CSV is not an invoice, accounting certification or signed provider receipt. |

The unconfigured starting allowance is $300. Saved defaults can range from $1 to $1,000,000 USD, but each workspace has its own fixed test allowance. These are not deposits, account-wide limits or a combined business balance. Rehearsal uses deterministic samples; the manual PayPal diagnostic uses no AI. Actual model-led purchasing remains a separate verification gate.

## First onboarding session

1. Complete authorized owner configuration, then use the protected Vercel deployment and the dedicated ProofPay owner key. Business settings do not create login accounts.
2. Open **Business settings**. Enter the business name, **Department or cost centre**, and **Default workspace allowance**. Use $300 for the existing competing-request demonstration. Select **Save business settings**.
3. Start a rehearsal. Check its saved identity and allowance, approve a request, and inspect reserved/available amounts. Show a blocked competing approval without treating the allowance as real money.
4. Change the default settings, then verify that the earlier workspace and its approvals retain their original values. A new workspace uses the new defaults.
5. Open **Workspace history**. Resolve a held purchase before selecting another workspace. **Reset simulated workspace** is a separate rehearsal action; it retains earlier records and does not resolve a real payment.
6. In **Purchases**, choose **Export CSV**. Reopen the downloaded file and compare its row count and values with all loaded active-workspace purchases, including statuses hidden by the current screen filter. Inspect a versioned receipt separately.

Keep the first session in rehearsal. Use a separate PayPal sandbox buyer for the provider diagnostic after server credentials are configured. Perform a bounded AI call only under the reviewed free-credit policy; never use personal OpenAI credits or reset a consumed grant to stage a demo.

## Resources and sign-ins actually needed

| Resource / access | Current position | Owner action when needed |
|---|---|---|
| GitHub | Repository, review and CI already exist. | Maintainer access for source/release work; the business operator does not need a new GitHub account just to use the desk. |
| Vercel | Existing project; [business production release](../evidence/business-portal-release-2026-11-08.json) READY. Setup-pending shell checked at three widths. | Maintain appropriate deployment access. Application sign-in is a separate owner-key step; a business label or Devpost team membership does not grant it. |
| Neon/PostgreSQL | Existing connected database; eight real checks and business migration/repeat succeeded. | Maintainer owns subsequent migration and release checks. The business operator does not need a separate database login. |
| ProofPay owner key | Server-side credential setup remains blocked/pending. | Complete the authorized private setup for the owner hash/session secret, then sign in. Do not publish or share the owner key as a multi-user workaround. |
| PayPal sandbox | Existing integration and historical diagnostic evidence. Current Vercel credentials/flow still need verification. | Configure the test merchant on the server; sign in separately as the sandbox buyer for native approval. A normal PayPal-account login alone does not perform this setup. |
| Vercel AI Gateway | Free-credit route and eligible model identified; one expiring attempt configured. No actual inference recorded. | Recheck the current grant/balance/expiry before an authorized attempt. No personal OpenAI key or paid top-up is needed or permitted for this test. |
| Postman | Optional [collection](../postman/README.md) prepared and checked offline. | Import only for developer API inspection; it is not required for normal owner use or runtime AI. |

No additional sponsor signup is needed to test the present workflow. Astropods remains an unactivated alternative, not a dependency. A custom domain, a second payment processor and extra analytics tools can wait for a demonstrated need. See [RESOURCE_PLAN.md](RESOURCE_PLAN.md) for dated account/offer details; an old credit snapshot is not a current balance guarantee.

## Four-week pilot and acceptance

Week 1: agree one workflow, record its current approval/investigation process and complete setup. Week 2: have the owner perform the profile, allowance, history and report tasks. Week 3: run the agreed sandbox normal/uncertain-outcome cases and retain failures. Week 4: compare the results and decide whether to continue. No outreach or customer contact is authorized or sent by this plan.

Accept the pilot only when the owner can reproduce the agreed tasks, older workspace values remain unchanged, another owner's records are inaccessible, history switching respects held purchases, and exported data matches the selected workspace. A confirmed payment must have the required provider evidence. A screenshot, configuration flag or success toast alone does not pass those checks.

Measure time to approve a request, time to identify an unresolved payment, time to reconstruct a purchase from its evidence, operator assistance required and delivery/support hours. Record a baseline and the actual results; do not invent savings. Pause or narrow the pilot if the buyer needs production funds, arbitrary sellers, multiple approvers or accounting integration before these features exist.

## Pricing hypotheses, not published prices

| Proposed offer | Bounded scope | Question to validate |
|---|---|---|
| $2,500 assisted pilot | Four weeks, one sandbox workflow and up to 20 delivery hours; setup, walkthrough, agreed fault cases and written findings. | Will a qualified business pay for this defined outcome rather than free exploration? |
| $499/month continuation | One maintained workflow, agreed checks and bounded support, offered only after the pilot demonstrates recurring work. | Is there ongoing value and sustainable support cost after the owner can inspect the code? |

These retain the earlier integration-pricing hypotheses; they are not a bill, checkout, customer commitment or revenue forecast. No customer has been charged. Payment-provider charges and any future inference costs require separate agreed terms. Do not charge extra merely for checking an uncertain operation again.

Continue after the first pilot only if a buyer identifies a concrete problem, uses the workflow and accepts a scoped continuation. Otherwise reduce the scope or stop. Multi-user approval roles, production payment readiness, more merchants and provider expansion follow demonstrated demand and their own implementation/security work. Company valuation and processor parity are not evidence of product progress.
