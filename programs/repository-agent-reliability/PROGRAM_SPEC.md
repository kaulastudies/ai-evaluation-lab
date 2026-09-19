# RARB v0.1 — Frozen Engineering Specification

Status: **DRAFT FOR IMPLEMENTATION**

## 1. Product statement

AI Evaluation Lab's Repository Agent Reliability Program (RARB) evaluates autonomous
software changes using verifier-qualified task contracts and replayable evidence.

The coding agent is the **system under test**, not the source of truth.

## 2. Required verdicts

Every run MUST terminate in exactly one of:

- `VERIFIED_PASS`
- `VERIFIED_FAIL`
- `HOLD`

`HOLD` MUST be used when verifier qualification is insufficient, trusted evidence is
missing, or the environment cannot reproduce the required checks.

## 3. Trusted boundary

The coding agent MUST NOT be allowed to modify:

- frozen task contract;
- verifier source;
- verifier qualification controls;
- hidden acceptance fixtures;
- canonical evaluation-record generator;
- hash-generation logic.

Any attempted write to the trusted boundary MUST be recorded as a constraint violation.

## 4. Verifier qualification

Before scoring an agent on a task, the verifier MUST demonstrate:

1. reference solution passes;
2. known-bad solution fails for the intended reason;
3. configured mutation set is exercised;
4. mutation-detection rate is recorded;
5. verifier version and task version are frozen.

Initial qualification policy for AP-001:

- reference control: must pass;
- known-bad control: must fail;
- required mutations: all critical mutations must fail;
- any critical mutation escape => `HOLD`.

## 5. Agent attempt protocol

For each attempt capture:

- starting commit;
- model/provider/configuration;
- prompt/task version;
- tool calls;
- changed files;
- commands executed;
- agent success claim;
- public test result;
- verifier result;
- verifier evidence;
- latency;
- token usage;
- cost when available.

The agent's success claim has no effect on the final verdict.

## 6. Repair protocol

On `VERIFIED_FAIL`, the repair agent may receive:

- failed gate identifiers;
- bounded diagnostic evidence;
- relevant stdout/stderr;
- allowed file paths.

It MUST NOT receive the hidden verifier implementation or a reference solution.

## 7. Replay

A completed run MUST retain enough information to re-run verification against the same
artifact without re-running model inference.

Replay must validate:

- task version;
- starting/final artifact identity;
- verifier version;
- relevant hashes;
- verifier result.

## 8. Required metrics

For a batch of repeated trials compute:

- Claim–Evidence Gap
- False-Green Rate
- Repair Conversion
- Verifier Escape Rate
- Cost per Verified Success

## 9. AP-001 success gate

The first implementation milestone is complete only when one fully reproducible AP-001
run demonstrates:

1. agent receives frozen task;
2. agent creates a plausible patch;
3. public tests pass;
4. qualified verifier rejects the patch;
5. bounded failure evidence is returned;
6. agent repairs the patch;
7. verifier passes;
8. evaluation record is emitted;
9. replay reproduces the verifier verdict without model inference.

No dashboard work should begin before this loop runs reliably.

## 10. Non-normative implementation status amendment — 2026-09-19

Sections 1–9 above remain the original frozen RARB v0.1 engineering specification.
This amendment records observed implementation status without redefining the original
success gate.

Current committed evidence demonstrates:

- AP-001 verifier qualification, an admission `HOLD`, a later `VERIFIED_PASS`, and
  source-exact replay;
- AP-002 verifier qualification, a live `VERIFIED_PASS`, and source-exact replay;
- AP-003 verifier qualification, a genuine public-test false-green
  `VERIFIED_FAIL`, bounded repair attempts, source-exact repair replay, and terminal
  failure after the configured repair budget;
- AP-004 verifier qualification, a frozen strict-code-only-v1 admission `HOLD`, and
  a separate strict-code-only-v2 `VERIFIED_PASS`, both replayable from their recorded
  source commits;
- AP-005 verifier qualification, an initial public-test false-green
  `VERIFIED_FAIL`, and a bounded repair that received only failed gate IDs and
  diagnostics before converting the parent failure to a source-exact replayable
  `VERIFIED_PASS`.

As of this amendment, the committed live evidence set contains 10 attempts:
4 `VERIFIED_PASS`, 3 `VERIFIED_FAIL`, and 3 `HOLD`. All five benchmark tasks are
verifier-qualified, with 0 of 17 configured critical verifier mutations escaping
detection. Across two bounded-repair episodes, one converted to `VERIFIED_PASS`
(Repair Conversion = 50%).

The general successful bounded-repair-conversion evidence gap is therefore closed by
AP-005.

The original AP-001 milestone in Section 9 is **still not satisfied as written**.
No single AP-001 run demonstrates public-test false-green -> bounded repair -> verifier
pass. AP-005 now demonstrates that general sequence on a different frozen task, while
AP-003 remains a documented non-converting repair episode.

Therefore the remaining evidence gaps are:

- the original AP-001-specific Section 9 sequence as written;
- repeated multi-model/statistically meaningful evidence;
- Nebius/NVIDIA production-runtime evidence.

Demo and dashboard-style artifacts added during implementation are evidence indexes and
presentation surfaces. Their existence must not be interpreted as satisfying or
retroactively changing the original Section 9 ordering requirement.

The AP-004 v1 `HOLD` and v2 `VERIFIED_PASS` are separate observed attempts. This evidence
does not by itself establish that the protocol change caused the different outcome.
