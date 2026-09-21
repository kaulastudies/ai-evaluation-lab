# Repository Agent Reliability Program

**AI Evaluation Lab**

> Verifier-qualified evaluation of autonomous software changes.

This program evaluates coding agents as systems under test. It does not assume that an
agent's own success claim, ordinary unit-test pass, or LLM self-critique is sufficient
evidence that a repository-level task was completed correctly.

The program requires two independent questions to be answered:

1. **Is the verifier qualified to judge this task?**
2. **Did the agent satisfy the frozen task contract under that qualified verifier?**

A result can be `VERIFIED_PASS`, `VERIFIED_FAIL`, or `HOLD`.

`HOLD` is mandatory when the available verifier evidence is not strong enough to justify
a pass/fail decision.

## Core research question

Does verifier-backed feedback improve repository-level coding-agent reliability while
keeping cost and latency within practical bounds?

## Primary metrics

- Claim–Evidence Gap
- False-Green Rate
- Repair Conversion
- Verifier Escape Rate
- Cost per Verified Success
- Median Time to Verified Success

## Evaluation flow

```text
Frozen Task Contract
        |
        v
Verifier Qualification
  | reference -> PASS
  | known-bad -> FAIL
  | mutations -> detected
        |
        v
QUALIFIED?
   | no -> HOLD
   | yes
        v
Coding Agent
        |
        v
Patch + Agent Claim
        |
        v
Qualified Verifier
   | FAIL -> bounded evidence -> repair loop
   | PASS -> Evaluation Record
        |
        v
Replayable Evidence Bundle
```

## Initial benchmark

- **AP-001** — stale asynchronous response regression
- **AP-002** — permission-boundary violation
- **AP-003** — idempotency / duplicate-processing failure
- **AP-004** — API contract regression
- **AP-005** — data-transformation edge case

Current implementation status:

- **AP-001** — verifier-qualified; live admission `HOLD`, a preregistered fixed
  ten-trial local Ollama batch, and a preregistered Nebius/NVIDIA `VERIFIED_PASS`.
  All ten Phase 11B outcomes and the Nebius pilot are source-exact replayable.
- **AP-002** — verifier-qualified; live `VERIFIED_PASS`; source-exact replay available.
- **AP-003** — verifier-qualified; live public-test false-green `VERIFIED_FAIL`;
  bounded repair attempted and exhausted without conversion; source-exact repair replay
  available.
- **AP-004** — verifier-qualified; strict-code-only-v1 admission `HOLD` followed by a
  separate strict-code-only-v2 `VERIFIED_PASS`; both are frozen and source-exact
  replayable. This two-run observation is not treated as causal evidence for the
  protocol change.
- **AP-005** — verifier-qualified; the first live candidate passed public tests but
  failed all four qualified edge-case gates, then a bounded repair using only failed
  gate IDs and diagnostics converted the parent `VERIFIED_FAIL` to `VERIFIED_PASS`.
  Both attempts are frozen and source-exact replayable.

Current committed live evidence snapshot: **21 live attempts** —
**14 `VERIFIED_PASS` / 4 `VERIFIED_FAIL` / 3 `HOLD`** — across all **5 qualified
benchmark tasks**, with **0 / 17** configured critical verifier mutations escaping
detection. Repair Conversion is now **1 / 2 episodes (50%)**.

A successful bounded repair conversion is now demonstrated on AP-005. The original
AP-001 success gate in `PROGRAM_SPEC.md` remains unsatisfied **as written**, because
that frozen milestone specifically requires the false-green -> repair -> pass sequence
within AP-001 itself.

## Phase 11B evidence expansion

The preregistered Phase 11B plan completed all ten AP-001 initial trials under one local
Ollama `llama3:latest` configuration without early stopping. Nine attempts reached
`VERIFIED_PASS`; one admitted candidate failed public validation and remained
`VERIFIED_FAIL`. No public-test false-green occurred, so no repair was eligible. All ten
outcomes passed independent source-exact no-model replay.

The observed verified-pass rate is 90.0% (9/10; 95% Wilson interval 59.6%–98.2%). The
false-green rate among public-test passes is 0.0% (0/9; 95% Wilson interval 0.0%–29.9%).
This is repeated evidence for one local configuration, not repeated multi-model or
cross-provider evidence, and it does not close the AP-001 Section 9 sequence.

## Phase 11C Nebius/NVIDIA pilot

The preregistered Phase 11C pilot executed AP-001 once through Nebius Token Factory
using `nvidia/nemotron-3-super-120b-a12b`. The candidate was admitted, passed public
validation and all three qualified verifier gates, preserved the trusted boundary, and
ended `VERIFIED_PASS`. Source-exact no-model replay reproduced the stored evaluation
record hash and verdict.

This single direct pass demonstrates provider-backed Nebius/NVIDIA repository-task
execution under RARB. It did not enter the repair loop, does not close the original
AP-001 Section 9 sequence, and does not establish statistically meaningful or
production-scale performance.

## Non-goals

- claiming general software correctness;
- replacing repository maintainers or human code review;
- grading correctness solely with another LLM;
- hiding failed or null runs;
- treating existing unit tests as sufficient evidence by default;
- allowing the agent to modify its trusted verifier surface.

## Nebius/NVIDIA integration

Nebius x NVIDIA is an execution environment for the public multi-provider phase of this
program. The committed Phase 11C pilot now demonstrates one AP-001 run through Nebius
Token Factory using `nvidia/nemotron-3-super-120b-a12b`.

Future Nebius/NVIDIA runs remain subject to the same frozen-task, qualified-verifier,
trusted-boundary, preregistration, and replay requirements. The one-run pilot is not a
claim of broad multi-model, statistical, or production-scale capability.

The hackathon implementation is intended to remain part of AI Evaluation Lab after the
competition as an open repository-agent evaluation capability.
