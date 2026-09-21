# Nebius / NVIDIA Feedback Draft

## What worked well

### OpenAI-compatible Token Factory API

RARB already used a provider abstraction, so the Token Factory OpenAI-compatible chat-completions surface was straightforward to integrate. The Nebius adapter uses:

`https://api.tokenfactory.nebius.com/v1/chat/completions`

with the API key and model ID supplied through environment variables. This let the evaluator keep the same frozen repository-task protocol while changing the model/provider configuration.

### Clear model identity

Using the explicit model ID `nvidia/nemotron-3-super-120b-a12b` was useful for experiment provenance. RARB stores provider, model, token counts when returned, latency, raw response, candidate, and evaluator artifacts so a run is traceable later.

### Practical inference latency for this bounded experiment

Across the ten preregistered Phase 12 Nemotron AP-001 attempts, the observed median recorded model-generation latency was **4,869.5 ms**. That is only a descriptive measurement for this specific prompt, model, account, and experiment; it is not a general performance benchmark.

## What could improve

### Request-level provenance metadata

Evaluation systems benefit from stronger machine-readable provenance. It would be useful if each inference response exposed a stable request ID plus model revision/deployment revision metadata that can be stored directly in an evidence record.

### Machine-readable request cost

RARB records token usage but currently leaves Nebius request cost as unknown. A response field or API that exposes the exact billed cost for an individual inference request would make cost-per-verified-success metrics more reproducible.

### Evaluation-oriented examples

More official examples for deterministic evaluation workloads would help: fixed-temperature runs, repeated trials, provenance capture, batch evaluation, and safe replay patterns.

### Sandbox documentation for coding-agent evaluation

For coding-agent use cases, a concise end-to-end example that combines Nemotron inference with an isolated repository sandbox, test execution, artifact export, and cleanup would reduce setup friction for evaluation and benchmark builders.

## NVIDIA Nemotron feedback

Nemotron 3 Super 120B A12B produced valid repository-task candidates for all ten Phase 12 Nebius attempts under the fixed AP-001 protocol, and each attempt passed the qualified verifier in that bounded matrix.

The most useful property for RARB was not a conversational feature; it was the ability to place the model inside a deterministic evaluation protocol with a fixed model ID, temperature, prompt construction, and preserved raw response.

For future evaluation work, model/version provenance and stable structured-output controls would make repository-agent benchmarking even easier to reproduce.
