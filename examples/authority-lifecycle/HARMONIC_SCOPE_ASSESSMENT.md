# Harmonic public scenario: initial scope assessment

12 November 2026 · AI Evaluation Lab · Public-material review and reproduction only

**Finding:** the supplied public material supports independent reproduction of the NDA example's dispatch control and local HTTP consequences. It also supports inspection and checksum verification of V114's preserved receiver-boundary evidence. It does not permit an independent rerun of V114 or verification of the sovereign production runtime.

Reviewed source: [`zlomke76-del/harmonic-public` at `3ce2c49139f65a87e4a5339c7e90560078922be4`][source]. This assessment selects the public scenario identified for review and follows the earlier [scope proposal](SCENARIO_SCOPE.md). No implementation or tests were added to Harmonic. No private access, live model, external disclosure or production endpoint was used. The original Lab evidence and Harmonic's frozen records remain unchanged.

## What was independently reproduced

Fresh execution of the existing commands produced the following results. [REPRODUCTION.json](harmonic-public-review/REPRODUCTION.json) retains commands, environment, complete stdout/stderr, exit codes and reviewed-file SHA-256 values. The source checkout remained clean. These are fresh local results, separate from the repository's historical evidence.

| Existing material | Result in this review | What the result supports |
| --- | --- | --- |
| `node --test api/evaluate.test.js examples/raw-vs-governed/guard.test.js` | 26 passed, 0 failed | Ten reference-evaluator regressions and sixteen adapter checks. Adapter tests use supplied responses; they are not all HTTP integration trials. |
| `node examples/raw-vs-governed/run.js` | Exit 0; raw unjustified releases **1**, governed revoked releases **0**, unchanged-authority justified releases **1** | The actual public evaluator and fictional sink communicate over loopback HTTP. Assertions inspect the sink's in-memory ledger, not merely a printed decision. |
| `sha256sum -c SHA256SUMS.txt` in the V114 directory | Four listed files matched | Published README, freeze, result and test bytes match the supplied manifest. This verifies integrity against that manifest, not the truth of the historical run. |
| Frozen V114 execution command | **NOT RUN / unavailable from public implementation** | The preserved test imports private `api/secure-execution`; no substitute was implemented and no historical result was relabeled as independently reproduced. |

Reproduce from the pinned checkout with Node 20+; this review's exact Node version is in the record. No dependency installation is required:

```bash
git clone https://github.com/zlomke76-del/harmonic-public.git
cd harmonic-public
git checkout --detach 3ce2c49139f65a87e4a5339c7e90560078922be4
node --test api/evaluate.test.js examples/raw-vs-governed/guard.test.js
node examples/raw-vs-governed/run.js
cd evidence/examinations/v114-execution-boundary
sha256sum -c SHA256SUMS.txt
```

The proposal is deterministic replay. This run does not measure an LLM failure rate. Receipt IDs, timestamps and hashes vary between fresh executions; the asserted consequence counts are the comparison criteria.

## Where enforcement actually occurs

| Surface | Decision and consequence boundary | Demonstrated limit |
| --- | --- | --- |
| [Public API contract][contract] | Describes governance determinations separately from downstream execution. Its example explicitly marks downstream execution unenforced and execution not performed by Harmonic. | A contract declaration is not deployment evidence. Public reference `stable / allow` and `blocked / deny` are not silently remapped to production `PERMITTED` or `REFUSED`. |
| [Reference evaluator][evaluator] | Computes a disposition from represented authority and evidence, including represented revocation. | It does not independently authenticate the registry or discover an unreported state change. |
| [Teaching adapter][guard] | Requires refresh and verification callbacks; evaluates, checks admission, refreshes again, and reevaluates a changed packet before invoking `execute`. | This is the dispatch gate. Callback presence does not prove authentic current authority. The reference helper checks request/operation hashes and expiry; it is not signature verification. |
| [Demo receiving endpoint][sink] | `POST /release` validates the fictional payload and appends a ledger entry, including the current authority revision and `justified` flag. | It **does not reject revoked authority or require a receipt**. Raw execution reaches it after revocation. The governed path prevents its own dispatch; the receiver does not enforce that gate against another caller. The ledger append is a local synthetic effect, not a durable document release. |
| [V114 preserved executor][v114test] | Calls `verifyExecutorRequest` with a receipt, trusted public key, expected service and execution payload; increments the synthetic effect counter only after verification succeeds. | This describes receiver-side gating within the constituted test boundary. The verifier implementation is private, and the consequence is an in-process counter behind an injected `fetchImpl`, not an independently operated payment receiver. |

In the runnable example, T0 active authority produces the proposal; revision 2 represents revocation; raw dispatch creates an unjustified ledger entry; governed evaluation blocks dispatch. A separate active-authority trial creates one justified entry. The two HTTP routes, registry variable and ledger share one process and trust domain. Network syntax alone does not make these independent systems.

## Mapping the three review questions

| Question | Exact available evidence | Scope conclusion |
| --- | --- | --- |
| Does authorized work continue? | [`run.js` control, lines 101–115][control]; existing test `explicit reference allow executes once after revalidation and binding verification` | Unchanged active authority permits execution. This is an independent positive-control trial. It is not the stronger experiment in which an unrelated change occurs while the same queued authorization survives. The Lab's separate A1/A2 cases remain relevant controls, not Harmonic results. |
| Does revocation prevent commitment? | [`run.js`, lines 82–100][revocation]; existing test `effect-time revalidation change forces a second evaluation and blocks changed authority` | Represented revocation prevents this adapter's dispatch. The latter unit test uses a simulated evaluator. Neither establishes atomic revocation/commit ordering at an independent receiver. |
| Are ambiguous outcomes represented honestly? | [Adapter return and catch, lines 82–84][catch]; V114's seven preserved cases | These materials do not demonstrate lost-response reconciliation. If an executor commits and then throws, the catch returns `executed: false`; that value alone cannot establish no effect. This is a source-level scope observation, not a newly executed failure case or a finding about the private runtime. |

The [V114 result][v114result] records one successful positive effect and six blocked unauthorized paths: receiptless bypass, attacker-signed permit, payload tamper, expired permit, governance refusal and absent governance evidence. Its fixture supplies governance dispositions and evidence identifiers, and disables the persistence requirement. It does not exercise a live governance decision or database persistence round trip. An expired receipt test is not proof of single-use handling for a still-valid receipt. These qualifications agree with the [archive's own boundary statement][v114readme].

## Production relevance and the next bounded decision

The public example is sufficient for this initial assessment; no additional implementation or private access is needed. Reuse its proposal, packet construction, positive control, dispatch checks and observable sink counts. Reuse V114's frozen criteria as an inspectable specification, retaining its historical status. The Lab's [A/R/U evidence map](EVIDENCE_MAP.md) supplies comparison methods for continuation, commit ordering and uncertainty; it does not establish Harmonic compatibility or integration.

For any later production-facing evaluation, the unresolved boundary is the point between the last authority observation and the receiver's irreversible or durable effect. Current public evidence does not establish:

- atomic or otherwise contractually ordered revocation versus commit, including change after the final refresh;
- immutable action binding across every callback and effect-capable route, authenticated authority, or production receipt verification;
- duplicate/retry/delegation behavior, single-use permits, crash recovery or reconciliation of an accepted request with a lost response;
- independent operational evidence, deployment-wide route coverage, tenant isolation, load limits or service-level performance.

These are limits on what this review can conclude, not assertions that production lacks those controls. The [public/sovereign boundary][boundary] explicitly separates the implementations.

**Proposed next step:** review this boundary map together and decide whether a further examination should concern public adapter dispatch or a separately specified receiver-enforced consequence. Agree the exact authority/commit semantics and available outcome observation before designing anything further. The present result is a reproduced public integration example plus a bounded archival assessment, not production certification.

[source]: https://github.com/zlomke76-del/harmonic-public/tree/3ce2c49139f65a87e4a5339c7e90560078922be4
[contract]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/docs.html#L39-L66
[evaluator]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/api/evaluate.js
[guard]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/guard.js#L13-L84
[sink]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/run.js#L51-L68
[control]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/run.js#L101-L115
[revocation]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/run.js#L82-L100
[catch]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/examples/raw-vs-governed/guard.js#L82-L84
[v114test]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/evidence/examinations/v114-execution-boundary/V114_TEST.js#L94-L116
[v114result]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/evidence/examinations/v114-execution-boundary/V114_RESULT.json
[v114readme]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/evidence/examinations/v114-execution-boundary/README.md
[boundary]: https://github.com/zlomke76-del/harmonic-public/blob/3ce2c49139f65a87e4a5339c7e90560078922be4/V4_PUBLIC_BOUNDARY.md
