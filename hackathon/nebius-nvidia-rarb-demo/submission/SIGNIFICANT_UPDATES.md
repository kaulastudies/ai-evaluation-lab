# Significant Updates During the Hackathon Submission Period

AI Evaluation Lab existed before the Nebius × NVIDIA Global AI Hackathon submission period. The submitted RARB capability, however, was built and significantly expanded during the submission period.

The public Git history provides the audit trail.

## What was added during the submission period

### September 19, 2026 — RARB execution and verification foundation

RARB gained:

- a task-generic repository-agent execution engine;
- generic source-exact no-model replay;
- a bounded repair protocol;
- evidence-backed reliability metrics;
- a generated evidence brief and one-command demo entrypoint;
- verifier-qualified synthetic repository tasks, including preserved failures and false-greens.

Representative commits include:

- `377c22c4cf18730510042d6f0efaa9a8d341dc16` — task-generic RARB execution engine
- `038d90eafd4b3bc89fa36de35f8c512c6a32c2b6` — generic no-model replay
- `2adb68051c219798ae9ac71087b1fd67ae7d2a1c` — bounded repair protocol
- `bf65c92d9cab365800fcbdab77542d1c2417b65c` — evidence-backed RARB metrics
- `abf50641285b0c32b2c627b1303da666d879b186` — one-command RARB demo entrypoint

### September 21, 2026 — Nebius/NVIDIA integration and replicated evidence

RARB then added:

- a preregistered Nebius/NVIDIA AP-001 pilot;
- runtime repository-task execution through Nebius Token Factory using `nvidia/nemotron-3-super-120b-a12b`;
- preserved source-exact Nebius evidence;
- a preregistered fixed 30-attempt cross-configuration replication plan;
- ten Nebius/NVIDIA Nemotron attempts inside that fixed matrix;
- promotion of all 30 Phase 12 attempts into canonical evidence paths;
- Phase 12 evidence-integrity CI checks;
- compilation and authored-diff hygiene gates;
- a judge-facing hackathon evidence explorer.

Representative commits include:

- `348b3aedf8ce1296645d97db8f4fe31d47878bdd` — preregister Nebius Nemotron RARB pilot
- `37ed3813521f7cdaccbb6cc3a3d682854be1edb1` — merge source-exact Nebius AP-001 pilot
- `90893b5b0b6f6110b36548fe8d14f1938c578483` — preregister cross-model replication
- `4e9e7eafd195068a25f0cb20f8617773d5f9b3c9` — merge Phase 12 evidence promotion
- `09cd1ca6f703f5451772107039cb97f18f982e68` — merge the Nebius/NVIDIA hackathon judge interface

## Submission-period result

The project being submitted is therefore not a cosmetic rebrand of the pre-existing AI Evaluation Lab repository.

During the hackathon period, the repository gained the RARB repository-agent reliability system, verifier qualification, bounded repair, source-exact replay, evidence metrics, Nebius Token Factory / NVIDIA Nemotron execution, a fixed cross-configuration replication experiment, integrity gates, and the judge-facing product experience.

The underlying AI Evaluation Lab repository predates the competition; these RARB capabilities and the hackathon integration are the significant submission-period updates.
