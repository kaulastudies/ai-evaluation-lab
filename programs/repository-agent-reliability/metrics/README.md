# RARB Metrics

`aggregate.py` computes an evidence-backed snapshot from committed live model attempts
under `tasks/AP-*/evidence/live/` and verifier-qualification records.

The current metric definitions are intentionally explicit:

- **Claim–Evidence Gap** — among attempts with an explicit stored agent-success claim,
  the share that did not end `VERIFIED_PASS`.
- **False-Green Rate** — among explicit success claims whose public tests passed, the
  share rejected by the qualified verifier.
- **Initial False-Green Rate** — the same measure restricted to non-repair attempts.
- **Repair Conversion** — share of bounded-repair episodes with at least one
  `VERIFIED_PASS` repair.
- **Verifier Escape Rate** — critical verifier-qualification mutations that escaped
  detection divided by critical mutations exercised.
- **Cost per Verified Success** — reported provider cost divided by `VERIFIED_PASS`
  count only when every attempt has a reported cost.
- **Median Time to Verified Success** — median model-generation latency among
  `VERIFIED_PASS` attempts.

Missing fields are never fabricated. Attempts without an explicit stored success-claim
field remain visible in the ledger but are excluded from Claim–Evidence Gap.

These are descriptive metrics over the committed evidence set. They are not claims about
general model performance.
