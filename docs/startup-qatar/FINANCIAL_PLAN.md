# Financial plan for diligence

Status: **illustrative assumptions for comparison, 30 October 2026**. This is not a selected investment ask, historical financial statement, vendor quotation, signed offer or forecast of customer demand. Founder accounts and programme terms still need reconciliation. All amounts are USD.

## The investment decision

The programme maximum is not the budget. A bottom-up, no-collection stress case gives an indicative **$100,000 12-month ceiling**: $85,550 operating cash cost plus a 15% unspent contingency of $12,832.50, rounded to the next $10,000. The costs include planned work even if customers fail to pay. The plan is incomplete until Qatar costs, statutory obligations and founder availability are quoted or confirmed.

The proposed internal release gates are $20,000 / $30,000 / $50,000. These are negotiation scenarios, not the programme's approved tranche structure. Begin with a small validation allocation; do not ask the jury to underwrite an unproven expansion plan simply because START advertises up to $1.1 million. The programme states that funding is tied to mutually agreed milestones.[1]

| Gate | Internal ceiling | What would justify progressing |
|---|---:|---|
| Months 1–3: validation | $20,000 | Written programme eligibility/terms, founder agreement on availability, scoped technical review and buyer interviews. Initial three-month scheduled cash cost is $10,200, before contingency; the remainder is unspent working-capital headroom, not a spending target. |
| Months 4–6: first delivery and establishment | $30,000 | One paid-pilot scope or budget-authorised LOI, buyer-approved acceptance criteria, independent evidence review, and written Qatar establishment/visa/cost answers. A non-binding LOI does not equal collected revenue. |
| Months 7–12: repeatability | Up to $50,000 | Customer-accepted pilot evidence and one paid continuation or second paying buyer; a costed local hiring plan; sufficient cash before commitments. |

Founder owns cost and scope reconciliation. A customer budget owner validates willingness to pay; an independent reviewer checks technical evidence. The investor approves any investment release. If a gate fails, stop discretionary spending, report the failure and re-scope. Do not continue automatically because a date arrives.

At every release, recalculate remaining funded work and reserve, then deduct cash actually on hand and confirmed credits against those exact costs. Reduce or cancel later tranches where collections or benefits make them unnecessary. Under the illustrative base path, drawing the entire ceiling would leave $66,450 at year-end; that is a clear reason to resize later releases, not permission to spend it.

## Pricing and delivery economics to validate

| Proposed offer | Price hypothesis | Direct economic cost | Contribution before overhead and tax |
|---|---:|---:|---:|
| One-workflow pilot | $5,000 | 60 delivery hours × $50 + $500 independent review + $250 compute = $3,750 | $1,250 / 25% |
| One workflow's monthly regression service | $1,000 | Up to 8 hours × $50 + $100 compute = $500 | $500 / 50% |

These prices have not been accepted by a customer. The pilot excludes substantial custom integrations, unlimited reruns and production support. Re-scope those separately. The $50/hour rate is an economic replacement-cost assumption; it is not a claim about wages or a second cash payment. A 25% pilot contribution may be too low after acquisition and overhead. Measure actual hours before selling repeat work. See [commercial plan](COMMERCIAL_PLAN.md) and [pilot protocol](PILOT_PROTOCOL.md).

The cash model pays a proposed founder draw of $2,000/month and, conditionally from month 7, an all-in engineer allowance of $3,500/month. It does **not** also charge hourly labor in cash. Neither amount is a Qatar salary quote or a personal commitment. Capacity assumes 160 founder hours/month, of which 80 remain for product, sales and administration, plus 120 funded engineer hours/month from month 7. Both scenarios fit those assumptions; that does not prove the founder can or will make this commitment.

## Cash assumptions and sensitivity

| Cash category | Base 12-month amount | Basis |
|---|---:|---|
| Founder draw | $24,000 | $2,000/month, pending founder decision |
| Engineer allowance | $21,000 | $3,500/month in months 7–12, conditional employment plan |
| Infrastructure | $4,800 | $400/month, unquoted envelope |
| Qatar workspace and administration | $7,200 | $800/month from month 4, unquoted envelope |
| Business development | $2,700 | $300/month from month 4 |
| Setup, legal and travel | $7,500 | One planning allowance in month 4; itemised quotes required |
| Independent security/reliability review | $10,000 | Staged reviews, separate from pilot-specific reviewer fees |
| Pilot and recurring external delivery costs | $8,350 | $750 × 9 pilots + $100 × 16 customer-months |
| **Total scheduled cash cost** | **$85,550** | Contingency is reserved separately |

| 12-month output | Base hypothesis | Downside hypothesis |
|---|---:|---:|
| Completed paid pilots assumed | 9 | 3 |
| Recurring customer-months assumed | 16 | 1 |
| Invoiced revenue assumed | $61,000 | $16,000 |
| Collection lag assumed | 1 month | 3 months |
| Cash collected assumed | $52,000 | $10,000 |
| Year-end receivables assumed | $9,000 | $6,000 |
| Scheduled cash cost | $85,550 | $79,550 |
| Peak additional cash requirement from a modelled zero opening balance | $33,550 | $69,550 |
| Cash remaining if all $100,000 conditional tranches were received | $66,450 | $30,450 |

Zero opening cash is a mathematical origin for the incremental plan, not the founder's bank balance. The first 90-day validation targets are 15 buyer interviews, three assisted staging installs and one signed paid scope or budget-authorized LOI. The base cash model records the first completed pilot invoice in month 4 and recurring service from month 6; a one-month collection lag means the first pilot cash arrives in month 5. Staging installations and signed scopes do not count as completed paid delivery. The commercial plan and attachments use this same schedule. The downside keeps fixed spending unchanged to expose the cost of continuing despite weak sales; actual milestone gates should stop that continuation. Neither scenario estimates acceptance probability. Delayed investment is a separate constraint: do not incur costs before available cash or a committed payment schedule covers them.

The model does not price taxes, withholding, insurance, visas, employee obligations or family relocation individually. Administrative and employment envelopes require qualified local quotations before any commitment. If a separate residency route requires a bank balance, it is additional liquidity, not an operating expense or a charge to hide inside contingency.

## Historical financials and funding boundaries

The public planning file deliberately stores historical product revenue, opening cash, received funding and liabilities as `null`. Before completing the financial attachment, the founder must supply dated records for those fields and identify the legal contracting entity. No established product revenue or awarded investment is claimed here. Personal freelance income is not automatically startup product revenue.

The existing [$10,000 public research milestone](../../FUNDING.md) remains unchanged. No pending grant is counted as cash. Maintain separate cost centres for public research, customer-confidential work and Qatar commercial development. If an award funds a shared task, record the allocation and remove that cost from the other request; the same engineer hours or compute invoice cannot be reimbursed twice. Keep private bank statements and grant correspondence out of this public repository.

## Reproduce and review

From the repository root, with Python 3.10+ and no network calls:

```bash
python programs/startup-qatar/financial_model.py
python programs/startup-qatar/financial_model.py --check
```

[Assumptions](../../programs/startup-qatar/financial-assumptions.json) → [calculator](../../programs/startup-qatar/financial_model.py) → [monthly output](../../programs/startup-qatar/financials.json). `--check` detects stale output. The assumptions hash identifies the exact inputs; it is not audit assurance. Change prices, volume, collection timing, availability and quoted local costs before using the model for a real decision. Review cash and contribution separately.

## Source

[1] [Startup Qatar Investment Program](https://startupqatar.qa/en/investment-program), accessed 30 October 2026. START maximum and milestone funding are published programme statements. Every numerical operating assumption in this document is the Lab's proposal for testing, not a programme entitlement or market quotation.
