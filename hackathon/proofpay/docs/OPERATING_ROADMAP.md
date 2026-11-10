# Operating roadmap

8 November 2026 · proposed operating model and investment gates

ProofPay's immediate job is to help a software team connect an approved purchase to a checked payment outcome, including interrupted execution. A large future business would need repeated customer value, dependable operations and distribution. A “trillion-dollar” ambition is not a valuation, forecast or milestone supported by this prototype.

The next credible result is a reproducible AI-to-PayPal sandbox workflow that a reviewer can inspect, followed by paid pilots that measure integration effort and investigation time. Keep the [commercial hypotheses](COMMERCIAL_PLAN.md), [judge readiness](JUDGE_READINESS.md), [architecture](ARCHITECTURE.md) and [provenance plan](PROVENANCE_ROADMAP.md) consistent with what the code and evidence establish.

## Department responsibilities

These are functions, not a claim that ProofPay employs a full team. Rama Chandra M remains accountable for project decisions. Specialist contributors or agents can prepare bounded work, but they do not become payment approvers, legal advisers, security certifiers or authorized external representatives by appearing in this table.

| Function | Work owned | Reviewable output and release gate |
|---|---|---|
| Product | One buyer profile, purchase workflow and supported failure cases. | Requirement-to-evidence map; stop adding features that delay the genuine sandbox flow. |
| Design and accessibility | Readable type, predictable navigation, clear status and usable forms at narrow widths. | Recorded desktop/phone-width checks, keyboard review and explicit untested-device limits. |
| Application engineering | Server catalogue, authorization, operation state machine and APIs. | Reviewed changes with tests for the invariants affected; no client-authored prices or confirmation. |
| Payments integration | PayPal contract, buyer approval, request identities and recovery rules. | Actual sandbox normal/failure evidence; unknown outcomes stay attached to the original provider. |
| Data and reliability | Migrations, transactional accounting, retention, backup and restoration. | Repeated race/restart tests now; a real restore drill and measured recovery objectives before a customer production commitment. |
| Security and privacy | Threat model, tenant boundaries, dependency exposure, secret handling and incident response. | Findings with severity, reachable path, fix and retest; unresolved release-blocking risks prevent the affected rollout. |
| Independent QA | Check claims against execution, including failure paths. | Reproducible report tied to a source revision; separate fixtures, hosted rehearsal and genuine external-service results. |
| Research and provenance | Receipt semantics, independent verification and possible TIP interoperability. | Versioned schemas, adversarial vectors and a demonstrable external contract before adding compatibility claims. |
| Developer experience | Setup, CI, API examples, contribution instructions and release notes. | A fresh reviewer can run the documented supported path without production secrets or undocumented assistance. |
| Commercial and partnerships | Discovery, scoped pilots, pricing and distribution hypotheses. | Named customer problem, agreed acceptance and measured delivery economics; no outreach or commitments without authorization. |
| Customer operations | Support ownership, unresolved-operation handling and escalation. | Runbooks with a responsible person, response expectations and a manual investigation route. |
| Governance and finance | Scope decisions, spend limits, licensing, claims and release approval. | Decision log and budget ledger; specialist review before production financial or regulated responsibilities. |

Each issue should name one accountable owner, the expected user behavior, acceptance evidence and a reviewer. A contributor may cover several functions; avoid having the same person silently implement and declare an independent security review complete.

## Delivery stages

| Stage | Deliverable | Gate to continue |
|---|---|---|
| 0 — Hackathon release candidate | Genuine model proposal; owner approval; PayPal sandbox buyer approval and capture; retained recovery evidence; readable UI; public licensed source; reproducible instructions and the required demo. | A reviewer can trace one genuine application run and distinguish it from rehearsal. All mandatory event requirements are checked against official rules. Final submission still requires Rama's separate decision. |
| 1 — One repeatable sandbox pilot | One customer workflow, a scoped integration branch, documented operating rules and independent fault review. | Customer and builder agree acceptance before work; no incorrect confirmation, extra dispatch or reservation error in the supported cases. |
| 2 — Two paid implementations | Substantially shared code, measured integration effort, support time and investigator outcomes. | Both pilots meet agreed cases; at least one measured customer benefit; paid continuation establishes demand beyond a free demonstration. |
| 3 — A supportable product | Tenant/account model, access roles, migrations, observability, incident playbooks and tested recovery procedures based on customer needs. | Independent security assessment for the intended deployment, successful restoration exercise, bounded support commitments and measured costs. |
| 4 — Additional action or provider | A requested refund/invoice workflow or second provider with its own authorization, accounting and evidence contract. | A paying workflow justifies it; adapter conformance preserves provider-specific semantics and never routes around an uncertain existing charge. |
| 5 — Ecosystem platform | Stable SDK/API contracts, compatible evidence tools and repeatable partner distribution. | Several independent integrations, safe version migrations, renewal/retention evidence and a distribution channel that works without founder-only delivery. |

The stages are conditional, not a calendar forecast. Production money movement is a separate release decision after the responsibilities, security, legal arrangements and operating controls for the actual business model have been reviewed. Adding another payment API does not by itself create a payment processor, bank, custody service or regulated financial platform.

## Hackathon priorities

The judge should be able to understand the problem, see the actual AI and PayPal roles, trigger the supported failure case, and inspect the resulting evidence without relying on a sales claim. A coherent working slice is stronger than a catalogue of planned departments or protocols.

| Priority | Work | Evidence required |
|---|---|---|
| P0 | Finish secure model configuration and the genuine PayPal application path. | Recorded model provenance and actual sandbox order/capture lookup through the application, with secrets excluded. |
| P0 | Demonstrate uncertainty and recovery. | The original operation remains reserved after a deliberately lost application response; lookup resolves it without another capture. Label whether the run used PayPal or rehearsal. |
| P0 | Give reviewers a reliable entry point. | Fresh-user setup/reviewer-access check, exact source revision, working instructions and honest configuration limits. |
| P0 | Reconcile submission assets. | Submitted on 8 November 2026: [public entry](https://devpost.com/software/proofpay-purchase-desk). Preserve description, public source, video and team-credit consistency. Three inline Story images are verified; native card-thumbnail/gallery uploads remain incomplete. |
| P1 | Close concrete QA/security findings and improve readability. | Fixed issue, relevant regression evidence and clear remaining limitations; no invented “100% secure” badge. |
| P2 | Maintain the bounded offline receipt verifier. | Export/profile compatibility, reproducibility and mutation tests. Keep unsigned consistency separate from future signature and registry claims. |
| Later | External TIP registration, another provider or enterprise departments. | Verified interoperability or customer need. Do not imply delivery from a roadmap diagram. |

## Economics and resource decisions

Use the existing pilot offer as an experiment: $2,500 for a bounded four-week sandbox workflow, with a planning allowance of 20 delivery hours. At an assumed internal cost of $75 per hour, delivery consumes $1,500 before infrastructure, sales and support. These are management assumptions from the [commercial plan](COMMERCIAL_PLAN.md), not observed demand, vendor prices or earned revenue. A 40-hour delivery would already exceed that pilot price before other costs.

Track builder hours, model/API usage, hosting, independent review and support separately. Estimate each stage with `hours × internal hourly cost + infrastructure + API usage + external review`; do not hide founder time as a zero-cost resource. Set a spending limit before a paid-service experiment and record its actual use. This roadmap itself authorizes no purchase, subscription, hiring or external commercial commitment.

Limit early discovery to ten qualified conversations and three concrete scoped proposals before expanding the build. Seek two paid commitments, then renewal after delivery. If customers only want a one-time code handoff, price integration services honestly. If their existing provider/orchestration stack already solves the problem, record that outcome rather than inflate a software market claim.

## Release and operating discipline

Keep one GitHub issue per material behavior change and one source-linked evidence record per release. Classify claims as **implemented**, **verified locally**, **observed on the hosted rehearsal**, **observed with an external sandbox**, or **planned**. A test count must state which category it establishes.

Before each release, review changed trust boundaries, affected database migrations, meaningful regression results, the rollback path and user-facing failure states. During pilots, review unresolved operations and support load with a named operator. Track discovery and delivery economics weekly; review whether the next stage is justified monthly. Do not promise an SLA, uptime percentage or response time before the capacity and measurement exist.

The operating measures are practical: supported-case correctness, time to reproduce an incident, time to investigate an uncertain payment, integration hours, restore results, support hours per customer, paid renewals and contribution margin. Report failures alongside successes. A small passing suite does not justify a universal reliability percentage, and a large roadmap does not establish company value.
