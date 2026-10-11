# Verifying the Verifier: Reproducible Evidence for Repository-Level AI Evaluation

Rama Chandra M  
AI Evaluation Lab  
ORCID: https://orcid.org/0009-0008-0189-2166  
Prepared: 11 October 2026  
Status: Self-published technical report, version 1.0; not peer reviewed.

## Abstract

An AI-generated patch can pass public tests while violating the intended task contract. AI Evaluation Lab addresses this gap through frozen task definitions, qualified verifiers, preserved execution evidence, and source-exact replay. This article describes the Repository Agent Reliability Program (RARB) using its public repository documentation. The documented evidence set contains 51 live attempts across five qualified tasks: 43 VERIFIED_PASS, five VERIFIED_FAIL, and three HOLD outcomes. These counts describe a bounded engineering evaluation, not general coding-agent performance. Two repair examples illustrate why an evaluation should preserve both successful corrections and terminal failures. The practical contribution is a workflow that makes a verdict inspectable and reproducible rather than relying on a completion claim or a single test result.

## 1. The problem

A coding agent produces several different signals: a statement that work is complete, a patch, public-test results, and behavior under task-specific checks. Those signals answer different questions. A well-formed patch may be admitted to evaluation without being correct. Public tests may cover ordinary inputs while missing duplicate processing, stale asynchronous responses, or data-transformation boundaries.

RARB treats the agent as the system under test and checks the evaluation mechanism before trusting its verdict. Its public task set covers stale asynchronous responses, permission-boundary isolation, idempotency, API contract regression, and data-transformation edge cases [1, 2].

## 2. Evaluation method

The workflow begins with an explicit task contract. The verifier is qualified using reference implementations, known-bad controls, and configured critical mutations. The agent candidate is then evaluated against the frozen contract. Admission, public validation, verifier outcomes, and trusted-boundary checks remain separate observations.

The program distinguishes three recorded outcomes. VERIFIED_PASS indicates that the candidate satisfied the evaluation requirements. VERIFIED_FAIL preserves an observed failure. HOLD records an attempt for which a candidate verdict was not established, including outputs rejected before execution. A rejected response is therefore not silently counted as a successful or failed executed patch.

Evidence is retained so that the evaluation can be replayed against the recorded source state without repeating model inference. This separates reproduction of the verdict from generation of another candidate. Bounded repair also retains the initial failure and connects subsequent attempts to it rather than overwriting the original result [2].

## 3. Documented evidence

The public evidence brief reports 51 committed live attempts across five qualified tasks, with 43 VERIFIED_PASS, five VERIFIED_FAIL, and three HOLD outcomes. It also reports that none of 17 configured critical verifier mutations escaped detection [2]. Mutation coverage is limited to those configured controls; it does not establish that the verifier detects every possible defect.

The Phase 12 matrix is a distinct subset of the documented program. It comprises 30 initial AP-001 attempts: ten each for Ollama llama3:latest, Ollama qwen2.5-coder:7b, and Nebius/NVIDIA nvidia/nemotron-3-super-120b-a12b. The repository reports nine passes and one failure for the Llama configuration and ten passes for each other configuration. All 30 outcomes passed source-exact no-model replay. These results concern one task and fixed configurations, with no repair attempts in that matrix [1, 2]. They should not be added to the 51-attempt headline total as if they were an independent additional dataset.

## 4. Repair examples

AP-005 provides a documented false-green example. The initial candidate passed public tests, but the qualified verifier rejected all four edge-case gates. The attempt was preserved as VERIFIED_FAIL. A bounded repair received failed-gate identifiers and diagnostics, then passed public validation and the same four verifier gates. The resulting VERIFIED_PASS remained linked to its parent failure [2].

AP-003 provides a counterexample. Its initial candidate passed public tests but failed duplicate-processing checks. One repair response was rejected at admission; the final allowed repair passed public tests yet still failed the verifier. The program preserved the terminal failure after the repair budget was exhausted [2].

Together, these examples show the value of retaining the full sequence. Reporting only the last successful patch would hide the initial false-green. Reporting only successful repairs would hide the limits of the repair process.

## 5. Limitations and reproducibility

This article summarizes repository-reported evidence. No model runs or verifier tests were independently executed while preparing it. The headline attempt counts are not a balanced benchmark across models and tasks. The Phase 12 comparison uses a small single-task matrix, and model tags may require additional provenance to identify immutable model versions. The evidence does not establish provider-wide superiority, general model safety, or production-scale reliability. Complete economic execution cost is not available in the evidence brief [2].

Readers should inspect the task contracts, recorded attempts, verifier controls, and replay instructions in the repository before reusing a conclusion. Future evaluation should broaden task coverage while retaining fixed contracts, negative controls, attempt budgets, and failure records.

## References and source snapshot

[1] AI Evaluation Lab. README. https://github.com/kaulastudies/ai-evaluation-lab/blob/70da1933a9dd174109fcf012ef8e25703b979fd2/README.md

[2] AI Evaluation Lab. RARB Demo Evidence Brief. https://github.com/kaulastudies/ai-evaluation-lab/blob/70da1933a9dd174109fcf012ef8e25703b979fd2/programs/repository-agent-reliability/demo/EVIDENCE_BRIEF.md

Repository head observed during preparation: 70da1933a9dd174109fcf012ef8e25703b979fd2. Sources accessed on 11 October 2026. Numeric findings above are attributed to repository documentation, not newly measured results.
