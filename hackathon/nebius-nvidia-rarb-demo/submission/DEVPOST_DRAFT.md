# Devpost Submission Draft — RARB

## Project name

**RARB — Repository Agent Reliability Benchmark**

## Tagline

**Don't just verify the coding agent. Verify the evaluation before trusting its verdict.**

## Track

**Coding and Agentic Engineering**

## Short description

RARB is an evidence-first reliability layer for repository-level coding agents. It sends repository tasks to coding models, including NVIDIA Nemotron through Nebius Token Factory, but does not trust the model's own success claim or ordinary public tests as final proof. RARB qualifies the verifier first, evaluates the generated candidate against a frozen task contract, preserves PASS/FAIL/HOLD outcomes, supports bounded evidence-guided repair, and produces source-exact evidence that can be replayed without rerunning model inference.

## Inspiration

Coding agents are increasingly able to propose repository changes, run tests, and declare success. The difficult question is what happens after the agent says “done.”

A green public test can miss important edge cases. A verifier can itself be weak. A repair loop can quietly leak too much information. Failed runs can disappear from demos.

RARB was built around one rule:

> Don't just verify the agent. Verify the evaluation before trusting its verdict.

The goal is not to claim that a model is generally “safe” or “correct.” The goal is to produce inspectable evidence about specific repository tasks under explicit contracts.

## What it does

RARB evaluates coding agents as systems under test.

1. A repository task is frozen with explicit success criteria.
2. The task verifier is qualified using a known-good reference, known-bad controls, and critical mutations.
3. A coding model generates a candidate change.
4. RARB performs structural admission and trusted-boundary checks.
5. Public tests run, but they are treated as evidence rather than the final verdict.
6. The qualified verifier applies task-specific gates.
7. The attempt is recorded as `VERIFIED_PASS`, `VERIFIED_FAIL`, or `HOLD`.
8. When a public-test false-green is eligible for repair, the agent receives only bounded failed-gate evidence.
9. The stored candidate and evaluator source can be replayed without another model call.

The hackathon judge interface exposes three real committed evidence stories:

- a Nebius Token Factory / NVIDIA Nemotron `VERIFIED_PASS`;
- the single preserved Phase 12 `llama3:latest` `VERIFIED_FAIL`;
- an AP-005 public-test false-green that converted to `VERIFIED_PASS` after bounded repair.

## How we built it

The evaluation engine is written in Python. Provider calls are normalized behind a provider adapter. Nebius is integrated through the Token Factory OpenAI-compatible `/v1/chat/completions` endpoint, with credentials kept in environment variables and the model fixed by the experiment plan.

For the Nebius/NVIDIA runs, RARB used:

- Provider: **Nebius Token Factory**
- Model: **`nvidia/nemotron-3-super-120b-a12b`**
- Temperature: **0**
- Repository task: **AP-001 — stale asynchronous response regression**
- Output protocol: **strict-code-only-v2**

The verifier and evidence pipeline are separate from the model call. Attempts preserve the candidate, raw model response, evaluator result, stdout/stderr, manifest, and replay record.

The judge-facing interface is dependency-free HTML/CSS/JavaScript. It visualizes committed evidence and clearly distinguishes stored-evidence replay from fresh inference.

## Nebius + NVIDIA usage

RARB makes runtime calls to **Nebius Token Factory** through its OpenAI-compatible chat-completions API. NVIDIA **Nemotron 3 Super 120B A12B** generates repository-task candidates.

The first preregistered Nebius/NVIDIA AP-001 pilot produced a source-exact replayable `VERIFIED_PASS`.

Phase 12 then ran a fixed 30-attempt replication matrix on the same frozen AP-001 task:

- 10 × Ollama `llama3:latest`
- 10 × Ollama `qwen2.5-coder:7b`
- 10 × Nebius/NVIDIA `nvidia/nemotron-3-super-120b-a12b`

Observed Phase 12 outcomes:

- **29 / 30 `VERIFIED_PASS`**
- **1 / 30 preserved `VERIFIED_FAIL`**
- **0 false-greens**
- **0 repair attempts**
- **30 / 30 source-exact no-model replays verified**

For the ten Phase 12 Nemotron attempts, the observed median recorded model-generation latency was **4,869.5 ms**. This is a descriptive observation for that fixed experiment, not a provider-wide performance claim.

## Current committed evidence

Across the complete committed RARB evidence set:

- **51 live attempts**
- **43 `VERIFIED_PASS`**
- **5 `VERIFIED_FAIL`**
- **3 `HOLD`**
- **5 qualified repository tasks**
- **0 / 17 critical verifier mutations escaped**
- Claim–Evidence Gap: **5 / 48 = 10.4%**
- False-Green Rate: **3 / 46 = 6.5%**
- Repair Conversion: **1 / 2 = 50%**
- Median recorded generation latency among verified successes: **13.398 s**

These numbers describe only the committed RARB evidence set.

## A failure we deliberately preserved

The only Phase 12 failure was:

`phase-12-cross-model-replication-v1-ap-001-ollama-llama3-latest-i001`

The candidate was structurally admitted and the agent claimed success, but public validation failed and qualified gates `AP001-G03`, `AP001-G01`, and `AP001-G02` failed.

RARB stored the result as `VERIFIED_FAIL`. It was not converted, replaced, or discarded. Because it was not a public-test false-green, no repair was eligible.

## Bounded repair example

AP-005 demonstrates why public tests are not enough.

The initial candidate passed public tests but failed all four qualified edge-case gates. RARB froze the attempt as a false-green `VERIFIED_FAIL`, supplied only failed-gate IDs and bounded diagnostics to the repair attempt, and then applied the same qualified verifier.

The repair converted to `VERIFIED_PASS` and is source-exact replayable.

## Challenges we ran into

### Qualifying the evaluator

A benchmark is not trustworthy merely because its verifier returns a result. We added known-good, known-bad, and mutation controls so a task can be placed on `HOLD` when the evaluator is not qualified.

### Keeping evidence immutable

The project preserves failed, held, and successful attempts separately. Later protocol improvements do not rewrite earlier evidence.

### Replaying old evaluations correctly

A current checkout can differ from the evaluator source that produced an old record. RARB therefore supports source-exact no-model replay against the historical evaluator source.

### Repair without leaking the answer

Repairs receive bounded failed-gate evidence instead of verifier implementation details or a reference solution.

## Accomplishments

- Built a task-generic repository-agent evaluation engine.
- Qualified deterministic verifiers across five synthetic repository tasks.
- Preserved genuine public-test false-greens.
- Demonstrated one successful bounded repair conversion and one exhausted repair episode.
- Added source-exact no-model replay.
- Integrated Nebius Token Factory and NVIDIA Nemotron for repository-task execution.
- Completed a preregistered 30-attempt cross-configuration AP-001 replication batch.
- Added CI gates for deterministic evidence, replay, Phase 12 integrity, Python compilation, and diff hygiene.
- Built a judge-facing evidence explorer without modifying the frozen experiment evidence.

## What we learned

The strongest signal was not a model score. It was the gap between what an agent claimed, what ordinary tests observed, and what a qualified verifier could demonstrate.

We also found that reproducibility requires more than saving prompts and responses. Evaluator source, candidate bytes, manifests, trusted-boundary checks, and replay semantics all matter if a result is expected to survive later code changes.

## What's next

- Add more repository tasks and cross-task replication without overgeneralizing single-task results.
- Close the original AP-001 Section 9 sequence only if the required false-green → bounded repair → pass sequence occurs naturally.
- Improve judge-facing live execution while keeping API secrets server-side.
- Expand cost provenance and production-scale runtime measurements.
- Continue using Nebius/NVIDIA configurations under preregistered, verifier-qualified experiments.

## Built with

- Python
- Nebius Token Factory
- NVIDIA Nemotron 3 Super 120B A12B
- Git / GitHub
- GitHub Actions
- Ollama
- HTML / CSS / JavaScript

## Evidence boundary

RARB does **not** claim general coding-agent correctness, provider-wide superiority, production-scale reliability, or a general safety certification.

Phase 12 is exactly one repository task, three fixed configurations, and ten trials per configuration.

The original AP-001 Section 9 sequence remains open as written.
