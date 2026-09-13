# Evaluation Operations v0.2

The Lab treats an evaluation result as an evidence-bearing candidate rather than a single score.

```text
Task Contract
    -> Environment
    -> Model / Agent Run
    -> Artifacts + Trajectory
    -> Independent Verifier
    -> Evaluation Record
    -> Review / Disagreement / Adjudication when needed
    -> Regression / Release Gate
```

## New candidate workflow

```text
CLAIMED
  -> STARTUP_GATE
  -> CONTRACT_FROZEN
  -> FIXTURES_READY
  -> REFERENCE_PASS
  -> VERIFIER_PASS
  -> NEGATIVE_CONTROLS
  -> CANDIDATE_RELEASE
  -> AUTOMATED_GATES
  -> REVIEW
  -> ACCEPTED
```

The acceptance contract is frozen before a candidate is judged. The reference implementation must pass. A no-op or known-bad candidate must fail.

## Rework workflow

```text
REWORK_RECEIVED
  -> PIN_BASE_CANDIDATE
  -> CAPTURE_FINDINGS
  -> CLASSIFY_EARLIEST_BLOCKER
  -> MINIMAL_CAUSAL_CHANGE
  -> FULL_GATE_REPLAY
  -> NEW_CANDIDATE_RELEASE
  -> REVIEW
  -> ACCEPTED
```

If fixing a blocker requires changing the acceptance contract or agent-visible semantics, create a new task version instead of silently changing the task.

## Gate roles

- **Contract Gate** — validate package structure, metadata, restrictions, and contract hash.
- **Reference Gate** — prove the task is solvable.
- **Negative Gate** — prove a known-bad/no-op state does not pass.
- **Verifier Gate** — judge observable outcomes independently.
- **Repro Gate** — replay deterministic invariants.
- **Security Gate** — reject secrets, restricted data, and unsafe network assumptions.
- **Review Gate** — add human/model review only for genuinely subjective evidence.
- **Release Gate** — block acceptance when a required gate fails.

## Cost ladder

1. Deterministic verification — no model call.
2. Existing local Ollama model — zero API cost.
3. Free/credited cloud providers — comparative/capability-gap runs.
4. Paid model/API usage — funded work or a clearly defined public milestone.
