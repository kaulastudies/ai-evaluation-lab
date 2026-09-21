# AP-001 — Stale Asynchronous Response

This is an independently authored synthetic repository task.

## Failure class

Two requests are started for different resources. The newer resource completes first and
correctly updates state. The older request then completes and incorrectly overwrites the
newer state.

## Public-test design

Public tests confirm the ordinary happy path and basic resource switching. They are
deliberately insufficient to prove the stale-response invariant.

## Qualified acceptance gate

The critical verifier starts requests for resource A and resource B, resolves B first,
then A, and confirms that A cannot overwrite B.

## Demonstration target

1. agent patch appears plausible;
2. public tests pass;
3. agent claims success;
4. verifier rejects AP001-G02;
5. bounded evidence identifies a stale-write failure;
6. agent repairs without seeing verifier source/reference implementation;
7. verifier passes;
8. replay independently reproduces the final verdict.

## Current evidence boundary

Committed evidence includes the earlier local Ollama `VERIFIED_PASS`, a preregistered
fixed ten-trial local Ollama batch, and one preregistered Nebius/NVIDIA `VERIFIED_PASS`
using `nvidia/nemotron-3-super-120b-a12b`. The fixed batch produced nine direct passes
and one public-test failure, with zero false-greens and ten successful source-exact
replays.

None of these attempts demonstrates the full sequence above because none contains
public-test pass, qualified-verifier rejection, bounded repair, and subsequent verifier
pass within one AP-001 episode. The original Section 9 target therefore remains open.

## Phase 12 promoted replication evidence

Phase 12 adds 30 frozen AP-001 initial attempts under one evaluator source commit:
10 Ollama `llama3:latest`, 10 Ollama `qwen2.5-coder:7b`, and 10 Nebius/NVIDIA
`nvidia/nemotron-3-super-120b-a12b`. The observed distribution is 29
`VERIFIED_PASS` and 1 `VERIFIED_FAIL`; the failure is preserved exactly, with public
validation failure and AP001-G03, AP001-G01, and AP001-G02 verifier failures. All 30
attempts are source-exact replay verified.

No Phase 12 false-green occurred, so no repair was eligible. AP-001 Section 9 therefore
remains open. These observations are limited to AP-001 and the three fixed
configurations tested.
