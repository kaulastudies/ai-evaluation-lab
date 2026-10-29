# EO-001 follow-up: independent receipt audit

An external action can be deduplicated correctly while a workflow still trusts
the wrong receipt. This study runs the existing Forge Operator simulator at a
pinned commit, substitutes selected responses, and checks the resulting
authorization against separately captured provider state and controller records.

**Measured:** fulfillment authorization in a synthetic workflow. **Not measured:**
actual fulfillment, live-agent performance, process durability or production
payment safety. The controller is trusted; this does not authenticate a real
provider or contain a malicious candidate.

## Source and scope

- [Forge source at the evaluated commit](https://github.com/jgaethle10/forge-operator/blob/956a53e171fc8be9ad111cce714aaf1ec89c7006/integrations/neatroots/ambiguous-external-effect.mjs).
- [Existing upstream tests](https://github.com/jgaethle10/forge-operator/blob/956a53e171fc8be9ad111cce714aaf1ec89c7006/tests/ambiguous-external-effect.test.mjs).
- [EO-001 original Lab contract and simulator, PR #27](https://github.com/kaulastudies/ai-evaluation-lab/pull/27).
- [Independent external-observation intake, draft PR #29](https://github.com/kaulastudies/ai-evaluation-lab/pull/29).

This branch starts from Lab main `c8f4b4ed0af988ebe8ca9821c472642ab4c20f63`.
It adds a separate `EO-001-RECEIPT-AUDIT/0.1.0` protocol. The frozen EO-001 v1
contract treats imported observation/ledger contradictions as invalid evidence;
this experiment instead deliberately substitutes a response while its trusted
recorder retains the original. Those are different trust assumptions and must
not be silently scored as the same task. Neither PR #27 nor PR #29 is merged or
rewritten by this change. Existing AS/RARB results and the 52-attempt ledger are
unchanged.

No Forge implementation is vendored or relicensed. The local recorder and audit
are original Lab code. Reproduction downloads the pinned source to a temporary
directory, verifies its SHA-256 and executes that exact file. The workflow code
is unchanged; wrappers copy the provider response before applying a fault and
never edit its stored receipt. The provider and workflow share one process, so
this is logical separation of evidence, not an enforced security boundary.

## Observed results

The experiment executes **19 deterministic episodes**, plus **3 damaged-evidence
controls** derived from one episode. These are selected controls, not a random
sample or an estimated failure rate. All three ordinary recovery/control paths
remain represented.

| Returned response | Initial execution | Reconciliation | Same-key retry |
| --- | --- | --- | --- |
| Unchanged matching receipt | Authorized, verified by audit | Authorized, verified by audit | Authorized, verified by audit |
| Different order ID | Unsafe authorization | Unsafe authorization | Unsafe authorization |
| `settled: false` | Unsafe authorization | Safe unresolved block | Unsafe authorization |
| `settled: "true"` string | Unsafe authorization | Unsafe authorization | Unsafe authorization |
| Invented receipt ID | Unsafe authorization | Unsafe authorization | Unsafe authorization |
| Identical receipt bytes from a previous run | Unsafe authorization under the run-binding protocol | Same | Same |

An additional acknowledgement-loss plus lookup-outage case safely blocks.
Totals: **3 matching authorizations, 2 safe unresolved outcomes, 14 unsafe
authorizations, 3 invalid-evidence controls**. Every executed episode has exactly
one recorded synthetic provider effect. No actual fulfillment action is executed
by the upstream module, so every audit row says `fulfillment_observed: null` and
`transaction_completion: NOT_MEASURED`.

The two provider-success paths authorize without checking the returned settlement
flag. Reconciliation checks its truthiness, which accepts a string. All three
paths accept a wrong-order or invented-ID response in these controlled probes.
These are response-validation findings under an expanded fault model. The
unmodified fake provider supplies valid responses; this is not an observation
of an exploitable production service.

The cross-run case is distinct. A second instance of the same provider returns
an identical ordinal receipt for the same order. Its bytes and content digest
therefore cannot identify its run of origin. Our controller knows where it
obtained that receipt and records an origin label. That label is **trusted
experiment evidence**, not a cryptographic proof available from the original
receipt. Whether a replay should be disallowed across real workflow restarts
depends on the intended provider/order namespace; that must be agreed before
extending this protocol to a real adapter.

## Reproduce

Requirements: Python 3.10+; Node.js 22+ for fresh upstream execution. No package
installation, provider account, model API or real payment is involved.

From the repository root, run the offline checks:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python research/eo001_receipt_audit/audit.py --check
```

The offline check recomputes every verdict from the committed recordings, checks
the fixed attempt inventory, compares the expected outcomes, and checks source
digests and the Inspect subset view. It does not rerun the upstream workflow.

For fresh, source-exact execution and the PR #29 compatibility check:

```bash
python research/eo001_receipt_audit/fetch_sources.py /tmp/eo001-pinned
python research/eo001_receipt_audit/audit.py --check \
  --source-file /tmp/eo001-pinned/ambiguous-external-effect.mjs \
  --inspect-adapter /tmp/eo001-pinned/adoption.py
```

The downloader uses two fixed public repository/commit/file pins from
[`source_lock.json`](source_lock.json). It executes nothing. The audit refuses
different source bytes and compares fresh recordings with the committed ones.
Network failure or changed/unavailable upstream files fails the fresh execution
check; there is no silent fallback to stored success. CI runs both checks.

Intentional source or protocol changes require `--write` with `--source-file`,
then review of the recordings, outcomes and source digests together. Include
`--inspect-adapter` to refresh its compatibility result. CLI exit 0 means this
evaluation gate matched all expected controls, **including expected failures**;
it does not mean every workflow passed. Exit 2 means the gate could not complete
or a result differed.

## What is adopted from the listing work

[PR #29's adoption study](https://github.com/kaulastudies/ai-evaluation-lab/blob/dc04592b4059f6384fde11ccce269e0f2a3dd4eb/research/open_source_adoption/ADOPTION_PLAN.md)
already separates external observations from independent Lab verdicts. This
experiment applies its bounded JSON intake pattern and tests actual compatibility
with its exact pinned adapter, without copying that whole branch into this one.

[`evidence/inspect_view.json`](evidence/inspect_view.json) contains every report
row and three opaque scores: authorization safety, outcome, evidence status.
It includes the null safety scores on invalid-evidence controls. It is a JSON v2
**subset view for the Lab's importer**, not a complete Inspect EvalLog or evidence
of an Inspect SDK evaluation. The fixed `created` value is fixture metadata, not
a measured execution timestamp. There are 22 evaluation rows, not 22 agent runs.

The pinned importer preserved all 22 rows and all 66 score values. Its output
remains `UNVERIFIED_EXTERNAL`, `lab_verdict: null`, `promotion_allowed: false`.
Receiving our PASS/FAIL strings does not make it an independent verifier.
[`evidence/adoption_check.json`](evidence/adoption_check.json) records that check.
No marketplace code, private asset or proprietary task package was imported.
Temporal, sandbox orchestration and diagnosis frameworks in the adoption map
remain possible later work; they are not dependencies of this experiment.

## Review the evidence

- [`protocol.json`](protocol.json): attempt inventory, expected outcomes and scope.
- [`evidence/recording.json`](evidence/recording.json): original provider returns,
  delivered responses, controller origin labels, final provider state, and raw
  workflow evidence/journal. The journal is narration, not the independent oracle.
- [`evidence/report.json`](evidence/report.json): recomputed outcomes, reason codes,
  per-input hashes and source digests. Missing provider evidence is unscorable.
- [`collect.mjs`](collect.mjs) and [`audit.py`](audit.py): recorder and separate audit.
- [`NEXT_EXPERIMENT.md`](NEXT_EXPERIMENT.md): bounded proposal for joint review.

Local validation: 43 root tests (21 new), offline replay, fresh upstream replay
and the exact PR #29 intake check pass. The 25 adoption-branch tests and its
125-entry catalogue/14-source check also passed in a separate checkout. Existing
AS-001/AS-002, RARB Phase 12 and deterministic replay gates passed. GitHub Actions
is the remote verification record; see the pull request checks for its status.

## Trust limits

The pinned source, recorder, controller-origin labels and full synthetic capture
are trusted. A party controlling all those inputs can forge a consistent story.
Hashes bind reviewed bytes; they do not authenticate a provider, prove log
completeness or establish a trusted clock. This experiment does not implement
provider signatures or a process sandbox. Pending states, refunds, multi-tenant
orders, crashes, races and live-agent decisions remain outside the protocol.
This is preliminary independent Lab work, not a joint result, endorsement or
claim that Systemia's internal production workflows have failed.
