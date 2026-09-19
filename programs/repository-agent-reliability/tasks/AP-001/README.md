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
