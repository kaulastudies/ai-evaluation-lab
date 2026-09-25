# Phase 13 — IBM Bob agent pilot v1

Status: **PREREGISTERED DESIGN — NOT EXECUTED**

Baseline evaluator commit: `899998eb8806e426b5af44c064764c1c887ea92b`

## Objective

Evaluate IBM Bob as a repository coding agent under the existing RARB AP-001 task
without exposing the trusted verifier surface to the agent.

This pilot is intentionally narrow. It is designed to answer whether one fixed IBM Bob
configuration can produce an admissible AP-001 candidate that passes the already-qualified
verifier. It does not create evidence until the run is executed, audited, source-exactly
replayed, and explicitly promoted.

## System under test

- Agent: IBM Bob IDE
- Access tier: team-provided IBM Bob workspace
- Version: record the exact installed version at execution time; use IBM Bob v2.0.2 or later
- Mode: Agent
- Workspace: isolated AP-001 candidate workspace only
- MCP: disabled
- Outside-workspace file access: not permitted
- Extra user hints after the frozen task prompt: not permitted

The full `ai-evaluation-lab` repository MUST NOT be opened as Bob's benchmark workspace.
RARB verifier code, verifier diagnostics, evidence bundles, prior candidate outputs, and
other trusted evaluation material must remain outside Bob's readable workspace.

## Frozen task

- Task ID: `AP-001`
- Task version: `0.1.0`
- Initial attempts: exactly 1
- Repair attempts in this pilot: 0
- Early stopping: not applicable
- Outcome preservation: required

A repair experiment, if justified by the observed pilot outcome, requires a separate
preregistration. The pilot must not be converted into an interactive repair session after
seeing verifier results.

## Interaction protocol

1. Start from the baseline evaluator commit above.
2. Materialize only the AP-001 candidate-facing workspace and public task surface.
3. Confirm that the trusted verifier and prior evidence are not readable from that workspace.
4. Open only that isolated workspace in IBM Bob.
5. Start a fresh Bob task in Agent mode.
6. Do not run `/init` for this pilot.
7. Submit the frozen AP-001 task prompt once.
8. Approve only read/edit/execute actions that stay within the isolated workspace and are
   necessary for the task.
9. Do not provide additional implementation hints, corrective guidance, verifier gate
   information, prior RARB outcomes, or hidden-test details.
10. End the agent interaction when Bob reports completion or clearly stops making progress.
11. Freeze the resulting candidate state before running the qualified verifier.

## Evaluation flow

```text
Frozen AP-001 task
        |
        v
Isolated candidate workspace
        |
        v
IBM Bob initial attempt
        |
        v
Frozen candidate + agent completion claim
        |
        v
Public validation
        |
        v
Qualified AP-001 verifier (outside Bob workspace)
        |
        v
VERIFIED_PASS / VERIFIED_FAIL / HOLD
        |
        v
Source-exact no-model replay
```

## Evidence to capture

At execution time record, without adding secrets:

- exact Bob IDE version;
- operating system and relevant workspace configuration;
- permission configuration used for the run;
- frozen task/prompt identifier and hash where available;
- evaluator source commit;
- candidate patch or candidate source snapshot;
- Bob's terminal completion claim or task summary when exportable without violating terms;
- public-test result;
- qualified-verifier gate results;
- final RARB verdict;
- source-exact replay result;
- generation/interaction timing only when measured reproducibly;
- cost or Bobcoin usage only when directly observable; otherwise report unknown.

Do not infer missing token, cost, model, or internal-provider metadata.

## Trusted-boundary requirements

The run is invalid for RARB promotion if Bob can read any of the following before candidate
freeze:

- AP-001 qualified-verifier implementation;
- hidden verifier tests or expected gate outputs;
- prior AP-001 candidate solutions or evidence bundles;
- post-run verifier diagnostics;
- private contractor, customer, or task-platform material;
- credentials or unrelated secrets.

A `.bobignore` file may be used as an additional control, but workspace isolation remains
the primary boundary. Ignore rules are not treated as a system-level sandbox.

## Analysis plan

Primary unit: one initial attempt.

Report the observed outcome exactly. Do not estimate a population-level success rate from
this single pilot. If the attempt is admitted, report whether public validation and the
qualified verifier pass or fail. If admission or evidence quality is insufficient, record
`HOLD` rather than forcing a pass/fail result.

No comparison to Ollama, Nebius/NVIDIA, or other RARB configurations is authorized from
this one pilot beyond a descriptive statement that the systems were evaluated under RARB.
No superiority ranking is permitted.

## Claim boundary

This preregistration is not evidence that IBM Bob is reliable, safe, superior, or suitable
for production use.

A completed single AP-001 run can establish only that one recorded IBM Bob configuration
produced one observed outcome under this frozen RARB task and qualified verifier.

No IBM sponsorship, endorsement, partnership, certification, or validation of AI Evaluation
Lab is implied by use of IBM Bob or access supplied for a hackathon/team workspace.

## Publication boundary

Only Rama-controlled public/synthetic RARB material may be used.

Do not introduce Handshake, Boson, Insight, customer, employer, private benchmark, or other
restricted artifacts into the Bob workspace or public evidence package.
