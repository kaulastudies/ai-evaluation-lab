# Adoption sequence

The useful ideas fall into evaluation interoperability, evidence provenance, tool boundaries, durable execution, diagnosis and original repository tasks. Importing whole commercial applications would add dependencies and uncertain rights without answering a defined Lab research question.

## 1. External observations — implemented prototype

The read-only Inspect JSON adapter supports a future intake step alongside existing Evaluation Records. It retains multiple samples and scorers, incomplete execution and byte-level provenance. It cannot turn an external score into an AS/RARB verdict. This is the only implemented integration in the branch.

Before any runtime promotion: freeze an intake contract, validate real exported logs from the intended upstream versions, independently bind task and verifier identity, review publication rights, and run negative controls for scorer substitution, missing attempts and tampering. Keep the existing converter and records versioned separately.

Relevant supplied entries: 21, 30, 52, 69, 88–93. Public references: Inspect and Harbor. A shared file format does not make results from different tasks or configurations comparable.

## 2. Tool contracts and permission drift — proposed

Use the public MCP Python SDK as a protocol reference. Build original mock tools for removed operations, added required parameters, schema type changes, stale permissions, untrusted tool responses and denied writes. Store the tool schema and authorization policy digest with each proposed run.

The check should fail closed for unknown schema constructs and distinguish a contract mismatch from an agent failure. Begin offline with synthetic tool responses. Real Jira, Confluence, desktop and business-account connectors are outside this branch.

Relevant supplied entries: 5, 30, 49, 51, 70, 80, 96. Do not copy MCPSMITH or the advertised enterprise task pack.

## 3. Durability and independent outcomes — coordinate with EO-001

PR #27 already contains a separate synthetic acknowledgement-loss and retry study. Do not duplicate or merge it through this adoption branch. Temporal's public Python SDK is a reference for a later process-durability experiment; agent-sandbox is a separate orchestration reference, not a containment guarantee.

Extend only under a new reviewed protocol: process restarts between intent and receipt, simultaneous same-key attempts, incomplete evidence, replay after a crash and independently obtained external outcome records. Keep the verifier and provider ledger outside candidate-writable paths. A hash chain alone does not establish receipt authenticity or completeness. No runtime, cluster, worker, provider key or paid service is enabled here.

Relevant supplied entries: 2, 23, 32, 35, 36, 48, 63, 76, 102, 104, 116. Preserve the existing Evercraft/EO-001 coordination boundaries and do not imply a new partnership.

## 4. Failure diagnosis and controlled coding-agent experiments — proposed

AgentRx provides a public diagnosis framework; its LLM judge remains an auxiliary signal, not the Lab's independent verdict. Freebuff and Aider are possible candidate agents or edit-format references, not trusted evaluators.

First define held-out trajectory splits, annotation rules and a fixed evaluation matrix. Retain failed, cancelled and unresolved attempts. Measure diagnostic localization separately from outcome correctness. Any stopping policy needs calibration and drift tests on held-out data. Keep verifier source and future labels out of the candidate context. Check dataset rights independently of a repository's root code licence.

Relevant supplied entries: 11, 29, 40, 88, 90, 91, 93, 100, 108. A public agent implementation does not establish reproducibility of hosted model routing or permission to reuse sold development history.

## 5. Original bounded task candidates — proposed

| Area | Public reference | Candidate research question | Required independent check |
|---|---|---|---|
| Retrieval | Faiss | Does approximate retrieval miss relevant evidence or retain stale revisions? | Exact-search baseline, frozen synthetic vectors and source provenance. |
| Constraints | OR-Tools | Does a candidate schedule satisfy all declared constraints? | A separately authored feasibility checker, not only a solver's status. |
| Dependency changes | pip-audit | Does a dependency edit change known vulnerability exposure? | Fixed input/lock state and dated advisory evidence; no automatic fixes. |
| Storage | Valkey, Harbor format | Do duplicate requests, restarts and failed writes preserve declared state? | Disposable fixtures, an independent state model and crash/replay controls. |
| Rendering | OSPRay, Harbor format | Can an agent repair one specified rendering or numeric defect within a fixed budget? | Original task, deterministic oracle, pinned source and acceptable numeric tolerances. |
| Simulation | Gymnasium | Are reset, termination and truncation handled correctly? | Frozen seed/protocol, separate environment checks and no broad RL claims. |

These are new task ideas, not implemented benchmarks. OSPRay's licence does not grant Moury's 12-hour evaluation package. Valkey's licence does not grant the Ferrodis history or every Redis release. PlanCodeScan remains a separate user-owned asset; private code and marketplace rights need their own review before any public task extraction.

## Promotion and rollback

Keep this draft branch isolated. A later promotion should be one small PR per implemented capability, with pinned provenance, independent controls, documented limits, current tests and explicit integration points. Do not bulk-install the 14 projects. The source pins are research snapshots, not an approved dependency lockfile or known-secure release selection.

Rollback for the present work requires no production action: no default-branch code, deployed service, existing workflow or published evidence is changed. Retire the draft branch if the prototype is not useful. Main and open PRs #26/#27 remain independently reviewable.
