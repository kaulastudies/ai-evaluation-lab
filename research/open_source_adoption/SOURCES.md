# Public sources and adoption boundaries

Reviewed 2026-10-29. These 14 public repositories were checked directly for repository identity, a pinned commit, root licence and introductory documentation. This is not a complete dependency, dataset, security or runtime audit. Public alternatives are not asserted to be the marketplace products. No third-party implementation, marketplace code or vendor task pack is copied into this branch.

The original adapter is informed by the Inspect log interface. It does not install Inspect or execute an agent. Only that offline adapter is implemented; every other entry below is a research proposal. The Lab's original Apache-2.0 licence continues to apply to newly authored code and documentation. Any future reuse must retain upstream notices and check file-level exceptions.

## inspect

- Repository: [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai)
- Reviewed commit: `2f78dcb29eb02830b4536050f61fd1a0f7665523`
- Root licence: [MIT](https://github.com/UKGovernmentBEIS/inspect_ai/blob/2f78dcb29eb02830b4536050f61fd1a0f7665523/LICENSE); Git blob `72fc87742ef8a944fab4f28fe6231696c62f2fa4`.
- [Pinned introductory documentation](https://github.com/UKGovernmentBEIS/inspect_ai/blob/2f78dcb29eb02830b4536050f61fd1a0f7665523/README.md).
- Use: Implemented: read bounded JSON v2 exports into unverified external observations.
- Next gate: Require a separate task/version binding and independently verified evidence before any future promotion.

## freebuff

- Repository: [CodebuffAI/freebuff](https://github.com/CodebuffAI/freebuff)
- Reviewed commit: `e78f379dcb10475f52164b143e6af73fbaace5c1`
- Root licence: [Apache-2.0](https://github.com/CodebuffAI/freebuff/blob/e78f379dcb10475f52164b143e6af73fbaace5c1/LICENSE); Git blob `446a604f1bd40e5d75149f9300fe294400d11f3f`.
- [Pinned introductory documentation](https://github.com/CodebuffAI/freebuff/blob/e78f379dcb10475f52164b143e6af73fbaace5c1/README.md).
- Use: Candidate agent for shadow repository experiments; not a Lab dependency.
- Next gate: Pin agent, model routing, tool permissions and costs; freeze tasks and verify patches independently. The public repo does not license a private marketplace snapshot.

## harbor

- Repository: [harbor-framework/harbor](https://github.com/harbor-framework/harbor)
- Reviewed commit: `509b119db0d97b141dcd9c80f4f7ab861c47c2d6`
- Root licence: [Apache-2.0](https://github.com/harbor-framework/harbor/blob/509b119db0d97b141dcd9c80f4f7ab861c47c2d6/LICENSE); Git blob `261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64`.
- [Pinned introductory documentation](https://github.com/harbor-framework/harbor/blob/509b119db0d97b141dcd9c80f4f7ab861c47c2d6/README.md).
- Use: Existing Lab ecosystem; use its public task/environment format for future original tasks.
- Next gate: Keep reference solutions and trusted verifiers outside candidate control; check each task/dataset licence separately.

## agent-sandbox

- Repository: [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)
- Reviewed commit: `b1277676f8bf0e82ea299928997ecf5d696a92f1`
- Root licence: [Apache-2.0](https://github.com/kubernetes-sigs/agent-sandbox/blob/b1277676f8bf0e82ea299928997ecf5d696a92f1/LICENSE); Git blob `8dada3edaf50dbc082c9a125058f25def75e625a`.
- [Pinned introductory documentation](https://github.com/kubernetes-sigs/agent-sandbox/blob/b1277676f8bf0e82ea299928997ecf5d696a92f1/README.md).
- Use: Optional future sandbox lifecycle evaluation.
- Next gate: Requires a dedicated cluster/runtime isolation review; orchestrating a pod is not proof of hostile-code containment.

## agentrx

- Repository: [microsoft/AgentRx](https://github.com/microsoft/AgentRx)
- Reviewed commit: `7a18c79708e7671be15124460f4f7296107c2a55`
- Root licence: [MIT](https://github.com/microsoft/AgentRx/blob/7a18c79708e7671be15124460f4f7296107c2a55/LICENSE.txt); Git blob `9e841e7a26e4eb057b24511e7b92d42b257a80e5`.
- [Pinned introductory documentation](https://github.com/microsoft/AgentRx/blob/7a18c79708e7671be15124460f4f7296107c2a55/README.md).
- Use: Failure-step diagnosis as an auxiliary research signal.
- Next gate: LLM-based diagnosis is not the ground-truth verifier; hold out trajectories and independently review labels and dataset rights.

## ospray

- Repository: [RenderKit/ospray](https://github.com/RenderKit/ospray)
- Reviewed commit: `1fc364776c5cbbf8b1100dbf321cc3d40da41311`
- Root licence: [Apache-2.0](https://github.com/RenderKit/ospray/blob/1fc364776c5cbbf8b1100dbf321cc3d40da41311/LICENSE.txt); Git blob `68c771a099958211169377d766a7389422f5573d`.
- [Pinned introductory documentation](https://github.com/RenderKit/ospray/blob/1fc364776c5cbbf8b1100dbf321cc3d40da41311/README.md).
- Use: Optional C++ repository workload for a new original task.
- Next gate: Build a deterministic oracle and fixed resource budget; the renderer licence does not grant the listed OSPRay Eval benchmark.

## mcp-python

- Repository: [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- Reviewed commit: `d7845c073a2b9ba5ab2817ecf93d3e45ef24cd14`
- Root licence: [MIT](https://github.com/modelcontextprotocol/python-sdk/blob/d7845c073a2b9ba5ab2817ecf93d3e45ef24cd14/LICENSE); Git blob `3d48435454b105021b4f777c11b6b07d8d2ffea3`.
- [Pinned introductory documentation](https://github.com/modelcontextprotocol/python-sdk/blob/d7845c073a2b9ba5ab2817ecf93d3e45ef24cd14/README.md).
- Use: Reference for tool-schema and permission-boundary interoperability.
- Next gate: Add independently authored mock tools and contract-drift controls before any network connector.

## temporal-python

- Repository: [temporalio/sdk-python](https://github.com/temporalio/sdk-python)
- Reviewed commit: `2a7d321cbe538c38f7c9a45fcc4c6c44733ecf85`
- Root licence: [MIT](https://github.com/temporalio/sdk-python/blob/2a7d321cbe538c38f7c9a45fcc4c6c44733ecf85/LICENSE); Git blob `c7f1b9e7e809f4134614fdd5bd1b00c5e3a8df87`.
- [Pinned introductory documentation](https://github.com/temporalio/sdk-python/blob/2a7d321cbe538c38f7c9a45fcc4c6c44733ecf85/README.md).
- Use: Reference for durable execution, retries and replay.
- Next gate: First test crash recovery and concurrency against a synthetic external ledger, aligned with EO-001; SDK licence is not a hosted-service authorization.

## faiss

- Repository: [facebookresearch/faiss](https://github.com/facebookresearch/faiss)
- Reviewed commit: `a6505c5c5d76eaf86f9196669564ee766a9a1b69`
- Root licence: [MIT](https://github.com/facebookresearch/faiss/blob/a6505c5c5d76eaf86f9196669564ee766a9a1b69/LICENSE); Git blob `b96dcb0480a0b0be0727976e5202a1e7b23edc3f`.
- [Pinned introductory documentation](https://github.com/facebookresearch/faiss/blob/a6505c5c5d76eaf86f9196669564ee766a9a1b69/README.md).
- Use: Reference for exact-versus-approximate retrieval experiments.
- Next gate: Use licensed or synthetic vectors, test recall and stale-source provenance; defer installation until a bounded protocol exists.

## or-tools

- Repository: [google/or-tools](https://github.com/google/or-tools)
- Reviewed commit: `100f66e6242ab8bf8d32feb8f3bf086db66ae2b5`
- Root licence: [Apache-2.0](https://github.com/google/or-tools/blob/100f66e6242ab8bf8d32feb8f3bf086db66ae2b5/LICENSE); Git blob `d645695673349e3947e8e5ae42332d0ac3164cd7`.
- [Pinned introductory documentation](https://github.com/google/or-tools/blob/100f66e6242ab8bf8d32feb8f3bf086db66ae2b5/README.md).
- Use: Reference for synthetic scheduling and feasibility tasks.
- Next gate: Keep independent feasibility checks and deterministic problem instances; review bundled solver/dependency terms separately.

## pip-audit

- Repository: [pypa/pip-audit](https://github.com/pypa/pip-audit)
- Reviewed commit: `1483f5bce0490807e88007c444337e8715c118c5`
- Root licence: [Apache-2.0](https://github.com/pypa/pip-audit/blob/1483f5bce0490807e88007c444337e8715c118c5/LICENSE); Git blob `f433b1a53f5b830a205fd2df78e2b34974656c7b`.
- [Pinned introductory documentation](https://github.com/pypa/pip-audit/blob/1483f5bce0490807e88007c444337e8715c118c5/README.md).
- Use: Optional dependency-vulnerability evidence collection.
- Next gate: Pin inputs and review output; no automatic dependency updates or environment changes. A clean report is not a security guarantee.

## valkey

- Repository: [valkey-io/valkey](https://github.com/valkey-io/valkey)
- Reviewed commit: `ffbd8481a90ca0786d1d1b63c55df695be6d08e0`
- Root licence: [BSD-3-Clause](https://github.com/valkey-io/valkey/blob/ffbd8481a90ca0786d1d1b63c55df695be6d08e0/COPYING); Git blob `a2782ea7ba8784d1116974c91df9706499eda3d7`.
- [Pinned introductory documentation](https://github.com/valkey-io/valkey/blob/ffbd8481a90ca0786d1d1b63c55df695be6d08e0/README.md).
- Use: Separately licensed key-value reference for storage tasks.
- Next gate: Use a disposable local instance and independent persistence oracle; do not conflate with Redis versions or sold reconstruction history.

## aider

- Repository: [Aider-AI/aider](https://github.com/Aider-AI/aider)
- Reviewed commit: `5dc9490bb35f9729ef2c95d00a19ccd30c26339c`
- Root licence: [Apache-2.0](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/LICENSE.txt); Git blob `d645695673349e3947e8e5ae42332d0ac3164cd7`.
- [Pinned introductory documentation](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/README.md).
- Use: Candidate for fixed-task edit-format and repair experiments.
- Next gate: Keep identical tasks/models/budgets and compare independently verified patches; no runtime installation in this branch.

## gymnasium

- Repository: [Farama-Foundation/Gymnasium](https://github.com/Farama-Foundation/Gymnasium)
- Reviewed commit: `d4ef1b64d0198985d42cb75ce8f8bad41cb9bb4c`
- Root licence: [MIT](https://github.com/Farama-Foundation/Gymnasium/blob/d4ef1b64d0198985d42cb75ce8f8bad41cb9bb4c/LICENSE); Git blob `ac10bf443756cdc02724943ac09021092ce9e737`.
- [Pinned introductory documentation](https://github.com/Farama-Foundation/Gymnasium/blob/d4ef1b64d0198985d42cb75ce8f8bad41cb9bb4c/README.md).
- Use: Reference for future environment reset/step/termination semantics.
- Next gate: Preregister a specific RL question and seed protocol; environments and third-party assets require individual review.

## Inspect interface evidence

The adapter reads the version, status, eval identity, sample ID/epoch, named scores, error/limit/invalidation indicators and declared sample counts described in [EvalLog/EvalSample source](https://github.com/UKGovernmentBEIS/inspect_ai/blob/2f78dcb29eb02830b4536050f61fd1a0f7665523/src/inspect_ai/log/_log.py). It intentionally does not implement the full schema, binary `.eval` format, score reductions, aggregate metrics or transcript reconstruction. Unknown top-level fields may be ignored; unknown versions are rejected.

A pinned [upstream JSON fixture](https://github.com/UKGovernmentBEIS/inspect_ai/blob/2f78dcb29eb02830b4536050f61fd1a0f7665523/tests/log/test_eval_log/log_formats.json) was used for a local compatibility smoke test. It remains upstream and is not vendored. Its test result is not a new Lab model attempt.
