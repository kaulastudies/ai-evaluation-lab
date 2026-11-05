# October 2026 security remediation

Scope: CodeRabbit scan `a5f2f7a2-5083-4d70-9793-3eecdb7b8d46` of
`11ad08b6984829ab70c756d6972643abedb89e69` (25 findings). This branch changes
candidate execution and evidence verification; it does not retroactively change
historical results or assert that a follow-up scan has passed.

## Execution boundary

Native AP-001 through AP-005 candidates run behind a JSON observation interface.
The controller owns public assertions, acceptance gates, event scheduling, and the
verdict. Candidate source is mounted read-only in a fresh Linux bubblewrap sandbox;
only the Python runtime, transport worker, private tmpfs, and candidate are visible.
The worker clears the inherited environment, has CPU/address-space/file limits,
and installs seccomp rules denying process creation, exec, networking, and tracing.
The supervisor bounds input, output, and wall time and kills the process group.
Missing isolation produces HOLD/error and never falls back to native imports.
The AST check remains an output-format check, not a security sandbox.

Current verifier version is 0.2.0. Qualification runs against the reference,
known-bad implementation, and every current mutation. Historical qualification
JSON remains archived at its original version. The route-policy task vendors the
same transport; a regression check requires byte-for-byte equality.

Linux with working unprivileged namespaces, bubblewrap, libseccomp2, and
`/usr/bin/python3` is required for native scoring and historical replay. Windows,
macOS, and restricted containers must use a suitable Linux runner. CI explicitly
requires a successful sandbox probe; positive integration tests cannot silently
skip there. Separate root-owned Harbor verifier containers use an empty chroot and permanently dropped uid/gid instead of nested user namespaces. The seccomp and resource limits remain mandatory; no candidate code loads before both boundaries succeed.

## Evidence boundary and compatibility

`runner/evidence-anchors.json` pins the complete reviewed historical artifact
inventory, and its digest is pinned in `evidence_trust.py`. Submitted packages
cannot redefine their own expected inventory or replace an artifact and its hash.
Response bytes are validated and frozen before replay. Record hashes are recomputed
from their bodies. Task identifiers and parent labels are constrained; evidence
files are opened without following links. Repair prompts use frozen candidate bytes.

Historical source-exact replay is restricted to the reviewed archived packages and
runs in an isolated, bounded environment. New packages need reviewed provenance before being admitted to the historical archive. Fresh repair parents are independently re-evaluated with the installed secure controller, and their complete nested record hash must match before candidate code or diagnostic text enters a provider prompt. Self-supplied hashes alone are not proof of origin. The immutable anchors are a trust decision, not an independent
reassessment of historical benchmark quality.

Legacy executable standalone bundles are no longer trusted just because their
own manifest matches. Use the reviewed checkout's AP-001 `runner/replay.py` with
`--bundle-dir PATH`; it uses the installed secure verifier. Version changes may
prevent an old exact-verifier comparison from matching, which is reported as a
failure, never a fabricated replay success.

The browser demo retains explicitly reviewed fixed candidate/verifier snapshots
for its disposable Pyodide worker. Native callers additionally check the bundle
against repository-owned sources. This demo is not an arbitrary native execution
endpoint. The AP-005 browser snapshot includes the exact-type mutation check.

The demo's GREEN gate now discovers the same records as aggregation and rechecks
every candidate with the current controller, including the previously omitted
IBM Bob and third Llama3 attempts. Old fixed replay case lists remain additional
historical checks, not the coverage authority.

## Findings and changes

Numbers follow the scan's finding order (one-based).

| Finding | Change |
|---|---|
| 1. High: generic candidate admission bypass | Mandatory OS isolation; AST checks do not confer trust |
| 2. High: AP-002 shared verifier process | Trusted controller and remote candidate object |
| 3. Medium: Qiskit nested definition amplification | Finite primitive basis; composites/custom gates denied; operation, memory, CPU, wall budgets |
| 4. Medium: agent replay task path traversal | Known task IDs, confined runtime, authenticated archive |
| 5. Medium: generic forged verifier verdict | Verdict computed by controller outside candidate process |
| 6. Medium: Phase 12 self-supplied integrity hashes | Complete independently pinned inventory and recomputed records |
| 7. Medium: changed model response executed before validation | Validate response hash and length, then execute frozen private bytes |
| 8. Medium: AP-001 admission bypass | Same mandatory isolated transport |
| 9. Medium: AP-001 replay false verdict | Installed trusted controller; standalone legacy execution refused |
| 10. Medium: inherited generation credentials | Explicit environment allowlist; no provider keys mounted |
| 11. Medium: AP-001 ignores public failure | Public failure prevents VERIFIED_PASS |
| 12. Medium: AP-001 mutable fetch scheduler | Scheduler and resolution order owned by controller |
| 13. Medium: AP-004/AP-005 shared process | Remote candidate objects and trusted assertions |
| 14. Low: AS-001 action amplification | Reject oversized provider tool batches before dispatch; total/argument budgets; incremental recorder |
| 15. Low: route reward from early exit | Candidate remote; only trusted test controller can finish assertions |
| 16. Low: incomplete demo replay coverage | Aggregate discovery drives complete current-verifier coverage |
| 17. Low: subprocess resource exhaustion | Streaming output limits, wall timeouts, kill process group |
| 18. Low: repair prompt symlink disclosure | No-follow reads, archive provenance, frozen bytes and identity check |
| 19. Low: repair replay parent traversal | Strict components and authenticated evidence |
| 20. Low: trusted nested record_hash text | Canonical body hashes checked before execution and comparison |
| 21. Low: AP-003 shared process | Remote candidate object and trusted assertions |
| 22. Low: AP-003 interleaved retries | Same and changed-payload retries after another event; new mutant |
| 23. Low: AP-004 nullable field leakage | Full status, field-set, type/value contract across all variants; new mutant |
| 24. Low: AP-005 bool/int input mutation | Recursive exact-type input equality; new mutant |
| 25. Low: local evidence path amplification | Bounded iterative traversal, key/depth/work limits, 4 MiB input limit |

## Validation

Local unit and SDK checks are recorded in the PR. The editing environment blocks
nested Linux namespace setup, so positive sandbox integration requires CI on the
configured Linux runner. A CodeRabbit rescan and human review are still required
before declaring the findings closed. No production merge/deployment is included.
