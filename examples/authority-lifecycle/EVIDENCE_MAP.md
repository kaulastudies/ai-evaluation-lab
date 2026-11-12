# Existing evidence map

12 November 2026 · [PR #30](https://github.com/kaulastudies/ai-evaluation-lab/pull/30) · Source: `54d9462fa176adc0b40a62fa68afdb4a30481d7c`

Documentation only: no new tests or results. “Standing-preserving” means an unrelated authority change leaves the **same already-authorized, queued action** able to proceed.

| Requested category | Existing coverage | Demonstrated outcome | Specific limitation |
| --- | --- | --- | --- |
| Standing-preserving changes | A1, A2 below | Unrelated revocation preserves A's existing authorization and queued payload. A commits once. The mixed queue preserves 12 unaffected actions and blocks 12 revoked actions across 48 deliveries. | Only unrelated grant revocation; not arbitrary policy changes. Eight local threads, one database; deliveries start after revocation commits. |
| Revocation before commitment | R1, R2 below | Revocation after enqueue prevents writes through retries, clean restart and child delegation. Lock contention produces no effect; retry after revocation is denied. An effect committed earlier remains. | Authority and writes share one SQLite transaction domain. No remote cache/propagation test; clean restart is not crash recovery. Revocation is not retroactive erasure. |
| Ambiguous outcomes | U1–U3 below | A lost reply can coexist with one committed effect. Process kills before versus after commit leave zero versus one effect despite identical empty responses. Safe uncertainty remains unresolved; later evidence cannot justify an earlier unsupported success claim. | Caller-side exception or local subprocess faults, not network partitions. Trusted local provider/recorder; scripted workflows; physical fulfillment remains unobserved. No composed cross-system revocation test. |

## Exact test references

- **A1:** [run.scenario('unrelated_change')](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/examples/authority-lifecycle/run.py#L18-L58).
- **A2:** [ReceiverReview.test_concurrent_mixed_queue](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/examples/authority-lifecycle/run_review.py#L133-L166).
- **R1:** [run.scenario('revocation'), ('restart_retry'), ('delegation')](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/examples/authority-lifecycle/run.py#L18-L58). Each checks two denied deliveries and zero committed rows through a fresh read-only connection.
- **R2:** [ReceiverReview.test_revocation_lock_blocks_delivery](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/examples/authority-lifecycle/run_review.py#L113-L131), paired with [test_committed_before_revocation](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/examples/authority-lifecycle/run_review.py#L81-L89).
- **U1:** [ReceiverReview.test_acknowledgement_loss](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/examples/authority-lifecycle/run_review.py#L61-L79). The caller discards the committed reply; a fresh connection returns `ALREADY_COMMITTED` with one effect.
- **U2:** [DurableEvidenceTests.test_process_kill_is_before_response_and_respects_commit_boundary](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/research/eo001_receipt_audit/durable/tests/test_durable.py#L56-L61) checks recorded `kill_before_commit` and `kill_after_commit_recover` cases. [Generator](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/research/eo001_receipt_audit/durable/suite.py#L105-L126); [actual SIGKILL mechanism](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/research/eo001_receipt_audit/durable/harness.py#L69-L84).
- **U3:** [DurableEvidenceTests.test_safe_uncertainty_does_not_imply_payment_failure and test_later_manifest_cannot_justify_an_unobserved_success_claim](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/research/eo001_receipt_audit/durable/tests/test_durable.py#L83-L95). `candidate_safe_unknown` is `PASS / SAFE_UNRESOLVED`; `candidate_overclaim` is `FAIL / UNSUPPORTED_SUCCESS_CLAIM`. Both have one evaluator-observed effect. These unit tests replay recorded sessions; they do not themselves inject fresh failures.

## Evidence and reproduction

[Receiver evidence](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/examples/authority-lifecycle/review-2026-11-12/evidence.json): `original_receiver_scenarios`, `known_bad_controls`, `additional_checks`; queried rows, events and database hashes. [Durable evidence](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/research/eo001_receipt_audit/durable/evidence.json): `cases[]`, keyed by the IDs above.

[Negative controls](https://github.com/kaulastudies/ai-evaluation-lab/blob/54d9462fa176adc0b40a62fa68afdb4a30481d7c/examples/authority-lifecycle/run.py#L60-L70): `global_invalidation` blocks the unaffected action; `queue_only` allows a revoked write; `ignore_parent` allows the delegated write. Each must violate the same fixed expectations.

From the repository root at the pinned revision:

```sh
python3 examples/authority-lifecycle/run_review.py /tmp/authority-map-review
python3 -m pip install -r research/eo001_receipt_audit/durable/requirements.txt
python3 -m unittest discover -s research/eo001_receipt_audit/durable/tests -v
python3 -m research.eo001_receipt_audit.durable.suite --check
# Optional fresh local execution, including real process kills:
python3 -m research.eo001_receipt_audit.durable.suite --run
```

Use a new receiver output directory. Durable fresh execution requires Linux. `--check` replays recorded evidence; `--run` executes fresh cases. This map claims no new execution. Prior CI: [receiver](https://github.com/kaulastudies/ai-evaluation-lab/actions/runs/43238363267), [receipt audit](https://github.com/kaulastudies/ai-evaluation-lab/actions/runs/43238363024).

## Remaining evaluation gap

The fixtures are complementary, not a composed end-to-end proof. They do not demonstrate revocation across an independent authorization service and receiver with stale authority, uncertain dispatch and independently established final effects in one experiment.

The next scoping step is to identify an existing receiver interface, its final authority decision point and its outcome-observation mechanism. Reuse these controls after agreeing that contract; no additional test construction is proposed here.
