# Evidence ledger for Startup Qatar review

Reviewed 30 October 2026 against public repository baseline
[`794602108eba47c806543c01b7f8d2b7ba9345cc`](https://github.com/kaulastudies/ai-evaluation-lab/tree/794602108eba47c806543c01b7f8d2b7ba9345cc).
This is evidence for an early product hypothesis. It does not establish customer demand,
production safety, or an independent audit.

## Claims a reviewer can inspect

| Claim supported by the committed records | Exact scope and limitation | Source |
|---|---|---|
| Five synthetic repository-agent tasks have recorded passing reference controls, rejected known-bad controls, and 17 rejected configured critical mutations. | The mutations test selected failure modes. They do not establish an exhaustive verifier or adversarial sandbox. | [Qualification records](../../programs/repository-agent-reliability/tasks/) and the regenerated snapshot below |
| The aggregate contains 52 attempts: 49 initial and 3 repair attempts; 44 `VERIFIED_PASS`, 5 `VERIFIED_FAIL`, 3 `HOLD`. | These are stored results under historical task contracts, not 52 customers, deployments, or independent tasks. Failure and HOLD records remain included. | [Canonical aggregate](../../programs/repository-agent-reliability/metrics/summary.json) |
| Three of 46 attempts with an explicit success claim and passing public tests were rejected by the verifier. | This selected evidence set illustrates a claim–evidence gap; 3/46 is not an enterprise incident rate or an estimate of savings. The three include one repair attempt. Initial-only count: 2/44. | [Metric definitions](../../programs/repository-agent-reliability/metrics/README.md), snapshot's `false_green_attempts` |
| A repeated AP-001 experiment contains 30 initial attempts: 10 per configuration, 29 passes and 1 failure. | **These 30 are already included in the 52.** One task and three configurations cannot establish a general model ranking. No repair attempts or false greens occur in this batch. | [Frozen batch summary](../../programs/repository-agent-reliability/experiments/results/phase-12-cross-model-replication-v1/batch-summary.json) |
| All 30 repeated attempts have stored source-exact no-model replay records whose hashes agree with the promotion manifest. | Checking stored replay artifacts is distinct from rerunning all 30. Reproducibility is valuable even when the preserved outcome is failure. | [Promotion manifest](../../programs/repository-agent-reliability/experiments/results/phase-12-cross-model-replication-v1/promotion.json) |
| There are two bounded-repair episodes and three repair attempts; one episode converts to a pass. | This is too small for a repair success-rate prediction. The successful episode is AP-005; the original AP-001 Section 9 repair sequence remains unfulfilled. | [Metric report](../../programs/repository-agent-reliability/metrics/REPORT.md) |
| Provider and model metadata are present for 51/52 attempts. | The IBM Bob IDE attempt has no recorded underlying model/provider or token/cost telemetry. Its top-level record hash is valid, while the existing aggregate's nested-record hash field is null. Do not infer missing telemetry. | [IDE record](../../programs/repository-agent-reliability/tasks/AP-001/evidence/live/ap001-ibm-bob-phase13-001/evaluation.json) |

Cost per verified success is **unknown**: reported cost fields cover only 40/52 attempts,
and local-provider zero charges exclude hardware, energy and labor. Historical runtime,
verifier and schema differences must be considered before pooling results into a product claim.

## Reproduce the proposal's arithmetic and source identity

From the repository root, with Python 3.10 or later:

```bash
python programs/startup-qatar/evidence_snapshot.py --check
PYTHONPATH=src python programs/repository-agent-reliability/runner/phase12_evidence_check.py
PYTHONPATH=src python programs/repository-agent-reliability/demo/run_demo_check.py
```

The first command reads the source artifacts, independently derives the headline counts,
checks them against the published aggregate, verifies 49 canonical scored-record hashes,
and verifies the promoted Phase 12 file hashes. The three HOLD attempts have no scored
record hash. It compares its result to
[`evidence-snapshot.json`](../../programs/startup-qatar/evidence-snapshot.json), which records
SHA-256 identities for 265 input files. It makes no network call and executes no candidates.

`--write` deliberately refreshes that review snapshot. Review the changed sources, baseline
reference, arithmetic and limitations before using it; it is not a way to turn a failed
check into an approved claim. Hash agreement establishes consistency with recorded bytes,
not that an external party independently attested those bytes.

The latter two commands are existing repository gates. On this branch's preparation run,
both passed. The demo gate includes the configured 16 historical replay cases and 3 repair
replay cases, runner controls, metrics, and evidence-integrity checks. It does **not** rerun
all 52 attempts or perform fresh inference. The separate Phase 12 integrity check verifies
stored replay evidence for the 30-trial batch. Full Git history is needed for historical
source-exact execution (`git fetch --unshallow` if the checkout is shallow).

Additional temporary-copy corruption checks rejected: manifest/verdict disagreement,
scored-record tampering, inflated aggregate counts, inflated mutation totals, and a changed
Phase 12 candidate artifact. A pristine copy reproduced the snapshot exactly. These checks
exercise the proposal auditor, not the security of candidate execution.

## Security status and release boundary

[Security remediation PR #34](https://github.com/kaulastudies/ai-evaluation-lab/pull/34)
was **open and unmerged** when checked on 30 October 2026, at head
`b81aec5ae4e143fe06e15e2b65dad6a2a7966e35`. Its description reports fixes for 25 scan
findings and passing workflows, while explicitly retaining required security review and
a follow-up scan. This proposal branch starts from `main`; it does not inherit those
unmerged fixes. Passing historical replay gates does not close those findings.

Use reviewed synthetic examples for jury demonstration. Customer code, production
credentials and untrusted candidate execution need a separate security-reviewed deployment
boundary before a customer pilot. Keep private customer artifacts outside this public repo.

## Evidence still required for an investment decision

| Jury question | Current evidence status | What closes the gap |
|---|---|---|
| Will a named buyer pay? | No paying AI Evaluation Lab customer or signed Qatar pilot is established by this packet. | Documented buyer interviews, an agreed problem and budget, then a signed paid pilot and actual receipt. |
| Does this improve an existing release process? | The public task evidence and new workflow demo are technical demonstrations. | A scoped pilot with a frozen baseline, held-out cases, human adjudication, measured false alarms/missed violations, and reviewer time. |
| Can another team reproduce the result? | Public artifacts and self-run checks exist. | An unaffiliated reviewer running the packet in a clean environment and documenting disagreements. |
| Is it ready for confidential workloads? | Security remediation remains under review; no production assurance is claimed. | Review closure, fresh scan, threat model, secrets/access controls and evidence-retention checks in the intended deployment. |
| Is Qatar execution credible? | Qatar operations, local hires, incorporation and founder residence are proposed decisions. | Written programme terms, local cost quotations, a founder-approved operating plan, and a plausible customer route. |

Collaborations, open-source contributions, applications and proposed pilots are not counted
as commercial traction, funding, or organizational endorsements. Bilingual Arabic–English
coverage also requires a qualified reviewer and recorded evaluation; it is a proposed
extension rather than an achieved result. No applicant-volume or selection-odds claim is
supported by this evidence ledger.
