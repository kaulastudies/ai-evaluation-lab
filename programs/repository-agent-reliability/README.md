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

- **AP-001** — verifier-qualified; live admission `HOLD` and later
  `VERIFIED_PASS`; source-exact replay available.
- **AP-002** — verifier-qualified; live `VERIFIED_PASS`; source-exact replay available.
- **AP-003** — verifier-qualified; live public-test false-green `VERIFIED_FAIL`;
  bounded repair attempted and exhausted without conversion; source-exact repair replay
  available.
- **AP-004** — verifier-qualified; strict-code-only-v1 admission `HOLD` followed by a
  separate strict-code-only-v2 `VERIFIED_PASS`; both are frozen and source-exact
  replayable. This two-run observation is not treated as causal evidence for the
  protocol change.
- **AP-005** — verifier-qualified; first live candidate was admitted and passed public
  tests but failed all four qualified edge-case gates, producing a genuine
  `VERIFIED_FAIL` false-green; source-exact replay available.

Current committed live evidence snapshot: **9 live attempts** —
**3 `VERIFIED_PASS` / 3 `VERIFIED_FAIL` / 3 `HOLD`** — across all **5 qualified
benchmark tasks**, with **0 / 17** configured critical verifier mutations escaping
detection.

The original AP-001 success gate in `PROGRAM_SPEC.md` remains unsatisfied as written;
successful bounded repair conversion is still an explicit evidence gap.

## Non-goals

- claiming general software correctness;
- replacing repository maintainers or human code review;
- grading correctness solely with another LLM;
- hiding failed or null runs;
- treating existing unit tests as sufficient evidence by default;
- allowing the agent to modify its trusted verifier surface.

## Planned hackathon integration

Nebius x NVIDIA is the intended execution environment for the public multi-model phase
of this program. The current committed RARB evidence uses local Ollama execution; it
does **not** yet demonstrate Nebius/NVIDIA production-runtime evidence.

When Nebius access is available, NVIDIA models served through the supported Nebius
runtime will be evaluated under the same frozen-task, qualified-verifier, trusted-
boundary, and replay requirements. Any such runs must be recorded as new evidence rather
than retroactively attributed to the current local evidence set.

The hackathon implementation is intended to remain part of AI Evaluation Lab after the
competition as an open repository-agent evaluation capability.
