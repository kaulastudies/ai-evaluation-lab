# Independent Systemia contract mapping

This is the Lab's independent execution of Evercraft's candidate and native
recovery CLI on disposable synthetic state. It follows
[Evercraft issue #1705](https://github.com/jgaethle10/forge-operator/issues/1705)
and reviews [draft PR #1744](https://github.com/jgaethle10/forge-operator/pull/1744)
at commit `171a49b2a5cf81ff8922ebe2c69a182e91c1bd54`.
It does not connect a live Systemia worker, release a hold, or translate a Lab
receipt into native observer authority.

## Observed results

| Fault | Candidate behavior | Delivered evidence | Synthetic effects | Observed fulfillment |
| --- | --- | --- | --- | --- |
| None | Confirm after execute | Authenticated | 1 | Unknown |
| Acknowledgment loss | Lookup, then confirm | Authenticated | 1 | Unknown |
| Lookup outage | Finish unresolved | Unavailable | 1 | Unknown |
| Altered signed response | Finish unresolved | Signature rejected | 1 | Unknown |

All four behavior checks pass. The last row does **not** mean its delivered
evidence is valid. Capture coverage is checked separately against the signed
closing state, controller call inventory and separate SQLite read. This only
establishes coverage within the trusted local synthetic store.

The native lane executes `goal-cli.mjs recovery-hold` and `recovery-observe`
against copied synthetic state. Fourteen cases cover valid observations,
mission/goal/work/attempt/attempt-key/provider mismatches, expiration, changed
claims, missing observer configuration, foreign Lab envelopes and repeated
reconciliation. Every case retains blocked work, unknown effect state, disabled
automatic replay and blocked dependent work. Separate CLI calls cannot complete,
retry, restart the work or issue a goal completion receipt. Rejected mutations
leave persisted state unchanged. These are normal process invocations; no new
power-loss or crash-durability claim is made about Systemia's file store.

The existing upstream tests also run unchanged: 15 candidate tests and 9 native
provider-observation tests. Eight Lab replay tests reject damaged or promoted
records. Counts describe bounded controls, not estimated production reliability.

## New explicit counterexample: authentic but false

The Lab controller creates an empty effect oracle and makes zero provider calls.
A disposable observer key signs a native `completed` claim whose response hash
points to that empty oracle. Systemia accepts the configured observer's signature
and records an attestation. The Lab independently checks the signature, but the
completion claim contradicts the controller-owned synthetic oracle.

Systemia still reports effect unknown, keeps the hold and rejects retry and
completion. This is consistent with its documented contract, not an observed
authorization bypass. It makes the boundary measurable: authenticated observer,
false effect claim, safe quarantine, task unresolved. The verifier checks the
response hash's shape; it does not fetch that response or establish its truth.

The oracle is a deliberately controlled fixture, not an independently trusted
production provider. A dishonest host could fabricate both observation and
oracle. The evidence demonstrates behavior under this specified counterexample.

## Contract mapping

| Concern | Lab contract | Native Systemia contract | Evaluation rule |
| --- | --- | --- | --- |
| Identity | Durable operation, full request, idempotency key | Mission, goal, work, attempt, stable attempt key and provider chosen before execution | Preserve both namespaces; do not collapse a durable operation into an ephemeral run or substitute a new attempt |
| Trust | Configured synthetic issuer key and store | Configured observer key scoped to predeclared provider | A key valid in one protocol grants no authority in the other |
| Freshness | Current signed query challenge and method | Observation after hold, bounded expiry and clock checks | Check each native rule; a time window is not automatically a Lab challenge response |
| Signed statement | Local synthetic settlement plus fresh observation | Observer attests completed, not_found or unknown | Authentication and effect truth are separate dimensions |
| Successful Lab result | Synthetic authorization only | No native disposition or release authority | Never map VERIFIED_AUTHORIZATION to native complete/retry |
| Recovery result | Safe unresolved or authenticated synthetic confirmation | Recovery hold remains with unknown effect state | Report safety, evidence and completion separately |

The two lanes share a reviewed protocol comparison, not an automatic authority
bridge. The Lab-envelope negative control passes an actual recorded candidate
session envelope to the native CLI, which rejects its foreign schema. The other
native controls use separately created synthetic goals and observer statements;
they do not prove that native Systemia executed the Lab's provider operation.

## Reproduce

Requires Python 3.12+, Node 22+ and the existing isolated signing dependency.
No npm install, network provider, model credential or live mission state is used.

```bash
python -m pip install -r research/eo001_receipt_audit/durable/requirements.txt
python -m research.eo001_receipt_audit.systemia.evaluate --check
python -m unittest discover -s research/eo001_receipt_audit/systemia/tests -v
python -m research.eo001_receipt_audit.systemia.fetch_sources /tmp/eo-systemia-pinned
python -m research.eo001_receipt_audit.systemia.evaluate --run \
  --forge-source /tmp/eo-systemia-pinned --output /tmp/eo-systemia-evidence.json
```

`source_lock.json` pins the complete ten-file upstream execution/test import
closure by commit and SHA-256. The downloader only fetches and verifies source;
the evaluator verifies it again before execution. Upstream source is not vendored.
The committed `evidence.json` retains all four sessions, native state snapshots,
public signed observations, CLI responses and upstream test output. Private keys
remain transient. Lab implementation hashes bind the replay to the recorder.
Fresh keys, timestamps and process timing differ between runs; the assertions
are reproducible, not the artifact bytes. CI retains fresh public evidence too.

The runner uses reviewed subprocesses on a trusted host, not a hostile-code
sandbox. Environment filtering is not filesystem or network containment.
Static evidence replay checks consistency and signatures under retained public
keys; it cannot prove the honesty of the original recorder. No live model has
run, and no provider settlement, delivery or production readiness is established.

## Next agreement

The [coordination issue text](COORDINATION_ISSUE_DRAFT.md) is prepared for review,
not yet published as an issue. Confirm the identity mapping, evidence ownership
and acceptance rules before building a native disposition bridge. A later agent
experiment needs pinned model/runtime configuration, bounded resources, retained
raw proposed actions and guard decisions, and complete attempt records. Guarded
success alone must not be reported as evidence that the underlying model chose
safe actions. Evercraft's local Raven lane is prepared upstream; it was not run
here and does not supply model provenance for these deterministic results.
