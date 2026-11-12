# Play the authority lifecycle experiment

This browser interface runs the same Python `Receiver` implementation as the
native review. Python and SQLite execute through Pyodide 314.0.7 in browser
memory. It does not replay a saved success result or approximate the receiver in
JavaScript. Each step opens a separate read-only connection to inspect committed
effects, grant state, and the event chain.

Start with **Revoked queued action**, run it with commit-time enforcement, then
select the deliberately broken enqueue-only check and rerun. The broken
implementation commits a write after revocation and the fixed expectation fails.
Next try **Unrelated change / continuation**: the correct receiver preserves the
same queued authorization; the global-invalidation control wrongly denies it.

The eight scenarios cover queued revocation, parent revocation, continuation,
duplicate delivery, lost acknowledgement, a prior committed effect, rollback,
and lock contention. Each run can export JSON containing its exact source
hashes, intermediate snapshots, immutable queued payload, actual results,
expected results, and timestamp. Empty state and incomplete runs are not passes.

## Run locally

From `examples/authority-lifecycle`:

```sh
python3 -m http.server --bind 127.0.0.1 8767
```

Open `http://127.0.0.1:8767/web/`. The first run downloads the pinned runtime from
jsDelivr; later runs reuse it. The receiver source files are fetched from the
same deployment and checked against `sources.json` before execution. Hosting,
the CDN runtime, and the source manifest remain trust assumptions. These hashes
provide source consistency, not external attestation.

## Verify natively

From the repository root, with Python 3.11+:

```sh
python3 -m unittest discover -s examples/authority-lifecycle -p test_web_demo.py -v
python3 examples/authority-lifecycle/verify_sources.py
python3 examples/authority-lifecycle/run_review.py /tmp/authority-fresh-review
```

Choose a fresh output directory. The native engine tests exercise all eight
correct scenarios and the three broken controls, plus continuation identity,
rollback snapshots, prior committed effects, and reset isolation. The separate
native review runs the original tests and bounded eight-worker concurrency case.

The browser does not run concurrent workers or process-crash tests. Its lock
contention case uses two connections in the same runtime with a zero busy
timeout. Acknowledgement loss deliberately discards the return value; it is not
a network-fault injection. SQLite files live in temporary browser memory and
are cleared on reload. All identities and administrative calls are trusted
fixture inputs. No credentials, user documents, model API calls, analytics, or
real external writes are involved.

The original PR #30 durable provider separately tests signed receipt recovery,
process kills, and multiprocess retries. This authority fixture is an additive
experiment; it does not silently claim integration with that provider, Harmonic,
TIP, or Systemia.

Runtime documentation: https://pyodide.org/en/314.0.7/usage/quickstart.html
# Runtime verification

The same engine was also executed in Pyodide 314.0.7 under Node: Python 3.14.2,
SQLite 3.39.0. All eight correct scenarios met their contracts and all three
broken controls violated them. See `../review-2026-11-12/pyodide.log`.
This checks WebAssembly execution, not DOM behavior or hosted browser delivery.

To repeat from the parent directory, install the pinned runtime in a temporary
directory and pass its absolute package directory to the checker:

```sh
npm install --prefix /tmp/authority-runtime pyodide@314.0.7 --ignore-scripts
node verify_pyodide.cjs /tmp/authority-runtime/node_modules/pyodide
```
