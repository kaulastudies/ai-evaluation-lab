# Authority lifecycle: review and reproduction

12 November 2026

The question is whether withdrawing authority changes what the receiving system actually commits, while an unrelated change leaves an already authorized action able to proceed. The current local fixture meets those case expectations. It does not establish the behavior of Harmonic, a live TIP deployment, or a distributed receiver.

## What existed and what was added

| Layer | What it demonstrates | Where coverage stops |
|---|---|---|
| Recovered 5 November baseline, unchanged | Direct permission decisions, unauthorized revocation rejection, grant-ID reuse rejection, agent/scope/expiry restrictions, receipt tampering detection | No queued action or persistent downstream write; an ALLOW receipt is not a committed effect |
| 7 November receiver extension, implementation unchanged | Commit-time authority checks, parent revocation, retries, duplicate delivery, and continuation after an unrelated change | One trusted local SQLite transaction domain; not integrated with the original TIP archive or Evercraft implementation |
| 12 November review additions | Fresh execution, generated databases, application-level acknowledgement loss, rollback injection, lock contention, committed-before-revocation boundary, and a bounded concurrent mixed queue | Additional tests of the same local receiver, not new production integration or independent external validation |

Source before this review: `e5f9d8616bbef0532776d73cca42584745a83f67`. The new test code is [run_review.py](run_review.py). The baseline, [receiver.py](receiver.py), [run.py](run.py), and both original evidence files are unchanged.

## Request-to-evidence mapping

All database names below refer to files generated in the output directory by a fresh `run_review.py` execution. The committed [review-2026-11-12/evidence.json](review-2026-11-12/evidence.json) records the original queried rows, events, and database hashes; the binary databases are regenerated rather than committed. Each original receiver case compares returned outcomes with committed rows read through a fresh read-only connection.

| Requirement | Sequence and checked outcome | Relevant code | Generated database |
|---|---|---|---|
| Withdraw approval after queueing | Queue action, revoke its grant, deliver twice; both deliveries denied, zero effects | `run.scenario('revocation')`; `Receiver.deliver` | `revocation.sqlite` |
| Retry after restart | Queue and revoke, cleanly reopen receiver, deliver twice; zero effects | `run.scenario('restart_retry')` | `restart_retry.sqlite` |
| Delegation cannot bypass parent revocation | Queue under child, revoke parent, retry twice; zero effects; widening and new child creation rejected | `run.scenario('delegation')`; `Receiver.allowed` | `delegation.sqlite` |
| Unrelated change preserves existing authorization | Queue A, revoke unrelated B, deliver the same A using its existing grant; one effect | `run.scenario('unrelated_change')` | `unrelated_change.sqlite` |
| Duplicate delivery does not duplicate effects | Deliver the same action twice; COMMITTED then ALREADY_COMMITTED; one effect | `run.scenario('duplicate_delivery')` | `duplicate_delivery.sqlite` |

The continuation case does not create a fresh authorization after the unrelated change.

## Fresh results

Executed on 12 November 2026 with Python 3.12.14 and SQLite 3.53.1 on Linux. The exact UTC timestamp, environment, source hashes, database hashes, events, and queried rows are recorded in [evidence.json](review-2026-11-12/evidence.json).

- Original baseline: **5/5 pass**, with individual test output in [baseline.log](review-2026-11-12/baseline.log).
- Original receiver scenarios: **5/5 pass**.
- Deliberately broken controls: **3/3 detected**. Enqueue-only authorization allows a revoked write; ignoring parent revocation permits a delegated write; global invalidation blocks the unaffected action. Their `passed: false` fields are expected.
- New receiver checks: **5/5 pass**, with individual results in [review-tests.log](review-2026-11-12/review-tests.log).

| New check | Observed outcome | Evidence database |
|---|---|---|
| Reply discarded after a successful commit; retry through a new connection | ALREADY_COMMITTED; exactly one effect | `test_acknowledgement_loss.sqlite` |
| Action commits before authority is revoked | Existing effect remains; later delivery is denied; no additional effect | `test_committed_before_revocation.sqlite` |
| Exception injected after effect insertion but before event recording | Transaction rolls back the effect and event; retry then commits exactly once | `test_effect_rolls_back_when_recording_fails.sqlite` |
| Delivery attempts while another connection holds the revocation write lock | SQLITE_BUSY with zero effects; retry after revocation commits is denied | `test_revocation_lock_blocks_delivery.sqlite` |
| 24 queued actions, two deliveries each, eight worker threads with separate connections | All 24 deliveries for the 12 revoked actions denied; all 12 unaffected actions commit once, with 12 duplicate acknowledgements | `test_concurrent_mixed_queue.sqlite` |

The concurrent case queues both groups before revocation and releases delivery after revocation commits. It establishes this bounded ordering, not all possible races or sustained-load performance. The lock-contention case separately checks a delivery attempt during an uncommitted revocation transaction. Reply loss is injected at the caller boundary; no real network failure is induced.

The rollback test's pre-retry snapshot is included in the JSON. Its generated final database contains the later successful retry, not an empty database. Similarly, the committed-before-revocation case intentionally retains its earlier write: revocation is not retroactive erasure.

## Reproduce and inspect

From this directory, with Python 3.11+:

```sh
python3 run_review.py reproduced-review
```

Use `python` on Windows. No credentials, external services, or package installs are required. Use a new output directory each time. The runner exits nonzero on a failed expectation, baseline failure, missed broken control, or new test failure. Do not use `-O`; the imported original runner rejects optimized mode because its existing verifier uses assertions.

To inspect committed rows without calling the receiver implementation:

```sh
python3 -c "import sqlite3; c=sqlite3.connect('file:reproduced-review/unrelated_change.sqlite?mode=ro',uri=True); print(c.execute('SELECT id, resource, value FROM effects ORDER BY id').fetchall()); c.close()"
```

Expected output: `[('action', 'document', 'changed')]`. Substitute `revocation.sqlite` for an expected empty list. Broken-control databases are also generated and intentionally contain outcomes that violate their case expectations.

`SHA256SUMS.json` binds the supplied code, documentation, logs, and JSON to this review. It is an unsigned local integrity manifest, not independent attestation. Reproduction should match semantic outcomes; concurrent event order, execution timestamps, and timing logs need not match byte for byte.

## Remaining limits

- Authority checks, revocation, and effects share one SQLite transaction domain. Remote services and distributed caches need a separate consistency design.
- Identities and administrative calls are trusted fixture inputs. This is not an authenticated public API or a multi-tenant security review.
- No live TIP/Harmonic integration, TIP consensus, remote receiver, network partition, process-crash recovery, revocation latency measurement, or external reproduction was performed.
- Hash-linked events are unsigned and locally rewritable by a database administrator. They do not establish external provenance or protect against coordinated rewriting or truncation.
- Expiry and identity tests in the original baseline do not imply those features are implemented in the receiver extension.

A useful next review question is whether the downstream system has a transaction or equivalent enforcement boundary that can bind the final authority check to the committed effect. These cases make that assumption explicit rather than treating an orchestrator's stop signal as proof that a downstream write was prevented.
  
