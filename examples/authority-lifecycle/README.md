# Authority changes and the receiving system's outcome

Original review package: 7 November 2026. Fresh reproduction and additional checks: 12 November 2026. This extends the recovered 5 November offline revocation demo. It is a local test fixture, not a test of Harmonic or a live TIP deployment.

**Start with [REVIEW.md](REVIEW.md)** for the request-to-evidence mapping, current results, and limits. The original baseline and `evidence.json` remain unchanged. New results and test logs are in [review-2026-11-12/](review-2026-11-12/). A fresh native run retains 13 inspectable SQLite databases alongside its JSON evidence.

**Interactive demo:** [browser experiment and launch instructions](web/README.md).
It executes the unchanged receiver in Python/SQLite, lets the reviewer step
through eight scenarios and compare three deliberately broken controls, and
exports the actual run's evidence. This is an additive authority experiment in
[PR #30](https://github.com/kaulastudies/ai-evaluation-lab/pull/30); it does not
change or claim integration with that PR's existing signed receipt provider.

For the full current review, use Python 3.11+ and run from this directory:

```sh
python3 run_review.py reproduced-review
```

On Windows use `python run_review.py reproduced-review`. The destination must not already exist. This reruns the original baseline, five receiver scenarios, three known-bad controls, and five new checks. The new checks cover lost acknowledgement, an already committed effect, rollback on recording failure, write-lock contention, and a bounded concurrent mixed queue. No credentials or package installs are needed.

## Reproduce the original 7 November package

Python 3.10+; standard library only; no credentials, services, or installs.

From this directory:

```sh
python3 run.py
```

On Windows use `python run.py`. The runner executes the original five tests, runs five receiver scenarios in temporary SQLite databases, checks three deliberately broken controls, and writes `evidence.json`. It exits nonzero on a failed expectation. Do not use Python's `-O` flag. An optional output path preserves the supplied evidence: `python3 run.py reproduced.json`.

## Existing results versus this extension

The unchanged original code, tests, README and evidence are under `baseline/`. Recovered archive SHA-256: `fdcfa36bf74c8114d1c58ae66de11440966962a87af71cc355c85efeb8ea7c2a`.

The baseline checks direct permission decisions, rejected revocation by the wrong issuer, reuse of a revoked grant ID, identity/scope/expiry restrictions, and receipt tampering. Its five tests pass again. It does not have a queue, receiving-system mutation, child delegation chain, or continuation-after-unrelated-change case. Its ALLOW receipt is not proof of a committed write. Its caller-supplied time is also not suitable for enforcing production revocation.

New files `receiver.py` and `run.py` add queueing, commit-time checks, persistent effects, delegation ancestry, and independent reads of committed state. The extension reuses the baseline's canonical hash function; it does not claim to integrate the missing original `tip-agent-receipts.zip` or the Evercraft patch. The fetched lab repository at `72344eae045edddbb011f1b4d4915edf40850308` contained no matching receipt implementation to integrate. A title search did not recover the original TIP archive.

## Cases and observed results

| Case | Sequence | Committed receiver rows |
|---|---|---:|
| Revocation | Authorize and queue; revoke; deliver twice | 0 |
| Restart and retry | Authorize and queue; revoke; reopen receiver; deliver twice | 0 |
| Delegation | Create child and queue under child; revoke parent; deliver twice | 0 |
| Continuation | Authorize and queue A; revoke unrelated grant B; deliver A | 1 |
| Duplicate delivery | Authorize and queue; deliver twice | 1 |

The delegation case also rejects widening to another resource and creating a new child after revocation. The continuation test uses the same action and grant established before the unrelated change; it does not issue a fresh approval.

## Evidence boundary

`Receiver.deliver` uses `BEGIN IMMEDIATE` to read current authority, check all ancestors, insert the receiving system's effect, and record the outcome within one SQLite transaction. Revocation uses the same database transaction boundary. If revocation commits first, subsequent delivery cannot commit; this is not retroactive cancellation of an action already committed.

The runner closes the receiver and opens a fresh read-only database connection. It compares actual `effects` rows and returned delivery outcomes with explicit expectations, then exports all event records. Event hashes are checked using the baseline helper. A unique action ID prevents duplicate committed rows. Retries use an immutable queued payload. The database is temporary; the JSON contains its queried rows and events, not retained database files.

Three known-bad controls must fail the same case expectations: checking authority only at enqueue; ignoring parent revocation; invalidating every action after any grant changes. Their `passed: false` values in the evidence are expected and demonstrate detection. They are not failures of the correct implementation.

## What this does not establish

- No Harmonic integration, remote receiver, TIP consensus, or external independent reproduction.
- Identities and administrative operations are trusted fixture inputs, not authenticated APIs.
- No network partitions, distributed caches, sustained-load benchmark, injected process crashes, or multi-tenant security tests. The 12 November additions include one bounded 8-worker, 48-delivery case; this is not a stress or latency benchmark. Restart is a clean close/reopen, not crash recovery.
- SQLite provides a single local transaction domain. A separate remote authority service needs its own commit-time consistency design.
- Hash-linked events are unsigned local integrity checks, not externally anchored proof. A database administrator can rewrite them; truncation and coordinated rewriting are not detected.
- The baseline's expiry and identity tests do not imply those features are implemented in the new receiver. The new receiver models a fixed write action and exact resource scope.

This package supports a narrow claim: in this reproducible local receiving system, the tested authority changes govern committed writes, and an unrelated revocation preserves the queued authorized action.
  
