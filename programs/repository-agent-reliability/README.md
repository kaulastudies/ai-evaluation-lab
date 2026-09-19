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

Only AP-001 is frozen in this initial scaffold.

## Non-goals

- claiming general software correctness;
- replacing repository maintainers or human code review;
- grading correctness solely with another LLM;
- hiding failed or null runs;
- treating existing unit tests as sufficient evidence by default;
- allowing the agent to modify its trusted verifier surface.

## Hackathon integration

The Nebius x NVIDIA hackathon is used as an execution environment for the first public
multi-model implementation of this program. NVIDIA Nemotron models accessed through
Nebius Token Factory are evaluated under frozen repository-level tasks.

The hackathon implementation remains part of AI Evaluation Lab after the competition as
an open repository-agent evaluation capability.
