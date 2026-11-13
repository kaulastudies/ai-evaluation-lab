# Signed receipts, process recovery and concurrent retries

This Lab-side experiment uses a local reference provider, real subprocesses,
SQLite effect storage, Ed25519 receipts, a separate read-only state check and a
bounded workflow adapter. It is **not a Systemia execution result**. The original
source-exact Forge audit remains separate in the parent directory.

## Implemented evidence

| Requirement | Observed control | Boundary |
| --- | --- | --- |
| Authenticity | 15 public-key, signature, request and semantic controls | Configured synthetic issuer only |
| Freshness | Signed query challenge and method; stale challenge rejected | Query binding, not a trusted wall clock |
| Legitimate recovery | Same durable receipt accepted through a fresh lookup after process restart | Stable operation and idempotency key |
| Crash before commit | Worker killed after SQL changes; zero effects survive | Process kill, not machine power loss |
| Commit before lost acknowledgement | Worker killed after commit/before stdout; recovery and retry preserve one effect | The SQL row is the entire synthetic effect |
| Same-key concurrency | Three rounds of eight independent processes; one effect and eight events each | One host and database |
| Conflicting payload race | Eight workers, two amounts; four matches, four conflicts, one effect | Either payload can win the race |
| Evidence coverage | Signed closing manifest matches a separate SQL read and controller inventory | Trusted provider/host, quiescent capture |
| Workflow behavior | Bounded JSON adapter and nine scripted controls | No Systemia or live-model execution yet |

All **24 top-level scenarios** match their expected outcomes. The 15
authentication controls are nested in one scenario, and the nine workflow cases
are included in the 24. Expected failures remain failures; the gate passing does
not mean those workflows passed. There are 28 additional unit/boundary tests.

## Receipt identity across restarts

A receipt identifies a **durable operation**, not an ephemeral client run. It
binds issuer, store, operation, order, amount, currency, idempotency key, settlement
sequence and receipt ID. A separately signed observation binds it to a fresh
query challenge and method. An earlier committed receipt therefore remains
usable after restart, while an old response cannot answer a new query. This
refines the original study's cross-run rule: legitimate recovery must remain
valid when the underlying operation has not changed.

The provider creates and signs its own receipt. The evaluator verifies it with
a separately configured public key, then compares a signed closing manifest
with an independent read-only SQL snapshot and all recorded controller requests.
The agent's final claim is checked against responses it actually received;
later ledger knowledge cannot retroactively justify an unsupported success claim.

## Reproduce

From the repository root on Linux, with Python 3.10+:

```bash
python -m pip install -r research/eo001_receipt_audit/durable/requirements.txt
python -m unittest discover -s research/eo001_receipt_audit/durable/tests -v
python -m research.eo001_receipt_audit.durable.suite --check
python -m research.eo001_receipt_audit.durable.suite --run
```

`--check` replays the committed public evidence, signatures, coverage, source
digests and expected outcomes. `--run` creates disposable stores and new issuer
keys, executes real process kills and races, and checks the same invariants.
Random keys, signatures, challenges and worker order differ between fresh runs;
invariant reproducibility is the claim, not byte-identical execution. `--write`
explicitly replaces the reviewed artifact after a source change. CI performs
both replay and fresh execution.

CI also retains the fresh run's public evidence as `eo-durable-public-evidence`
for seven days. The committed artifact remains the durable review snapshot.

[`evidence.json`](evidence.json) retains actual SIGKILL return codes, observed
commit-boundary markers, empty acknowledgement output, signed responses, full
request inventories, concurrency barriers, database snapshots and decisions.
Four damaged-evidence controls are deliberately unscorable. Private keys are
generated in temporary directories and are never exported or committed.

## Connect an isolated workflow

The [adapter contract](adapter_contract.json) uses one JSON stdin request and one
JSON stdout response per decision. Each decision starts a fresh candidate
process and receives the accumulated observations. Persistent workflows need an
explicit adapter for their session lifecycle.

Allowed responses:

```json
{"action": "execute"}
```
```json
{"action": "lookup"}
```
```json
{"action": "finish", "payment_status": "confirmed", "fulfillment_authorized": true, "receipt_id": "synthetic-effect-1"}
```

Use `unknown`, `false` and `null` for unresolved outcomes. The host owns the fixed
request, provider dispatch and signing key. Extra tool arguments, altered
operation identity, malformed or excessive output, nonzero exit, timeout and
exhausted steps cannot produce a passing success claim. The candidate receives
the public key and signed responses; the evaluator independently verifies them.

A complete scripted smoke run with a real post-commit provider kill:

```bash
python - <<'PY'
import json, subprocess, sys
from pathlib import Path
script = str(Path('research/eo001_receipt_audit/durable/scripted_candidate.py').resolve())
subprocess.run([sys.executable, '-m', 'research.eo001_receipt_audit.durable.runner',
    '--command-json', json.dumps([sys.executable, script, 'cautious']),
    '--fault', 'ack_loss', '--output', '/tmp/eo-workflow-session.json'], check=True)
PY
```

Defaults are six decisions and five seconds each; maximum configuration is
twelve decisions and fifteen seconds each. Argv is JSON, never shell text.
Inherited environment variables are restricted to basic process settings;
provider credentials are not forwarded. A live adapter's credentials and
model/token budget need explicit configuration and review. CLI-launched commands
remain `external_unclassified`, with model execution `null`, until provenance is
supplied and reviewed. The committed fixtures are explicitly scripted.

## Trust and engineering limits

- The public key is an evaluator trust anchor, never accepted from the envelope
  being verified. The archived key is trusted through fixture review. A newly
  imported packet cannot establish trust by supplying its own key and signature.
- Provider processes, evaluator and key storage are trusted. Owner permissions
  and environment filtering do not create a hostile-code sandbox. A malicious
  same-UID process can access the store/key. Only reviewed workflow commands
  belong here until an enforced isolation boundary is added.
- Effects, stable receipts and events share one SQLite transaction using
  `BEGIN IMMEDIATE`, WAL and `synchronous=FULL`. The fresh observation follows
  commit. A real remote payment cannot be made atomic with a local database by
  adopting this code. Power loss and storage faults were not tested.
- The signed manifest protects the supplied snapshot against unnoticed changes
  under the configured key. Its agreement with the separate SQL read and known
  inventory checks this experiment's capture. It cannot prove absence of actions
  outside the store or defeat a dishonest issuer or compromised host.
- Provider and verifier share a wire codec. Negative controls test the boundary;
  they do not eliminate common implementation errors or replace external review.
- No multi-host consensus, key rotation scheme, multi-tenant policy, refunds,
  pending settlement, real payment or actual fulfillment is evaluated.
  `fulfillment_observed` remains null.
- No model-provider credentials were configured for this work. Live-agent
  behavior and Systemia integration remain open; no model-performance rate or
  production guarantee is inferred from the scripted controls.

Technical references: [Ed25519 APIs](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/),
[SQLite transactions](https://www.sqlite.org/lang_transaction.html), and
[WAL assumptions](https://www.sqlite.org/wal.html). The signing dependency is
isolated in `requirements.txt`; existing Lab dependencies and AS/RARB evidence
are unchanged.
