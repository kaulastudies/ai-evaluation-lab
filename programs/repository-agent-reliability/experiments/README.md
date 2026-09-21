# RARB Experiments

This directory contains preregistered experiment plans. A plan fixes trial counts,
model configuration, repair budget, stopping rules, and claim boundaries before a live
batch begins.

Experiment plans are not evidence. Live outputs first go to the ignored
`runs/live/rarb/<experiment-id>/` staging directory. They become committed RARB evidence
only after artifact review, source-exact replay, and an explicit evidence commit.

## Phase 11B: AP-001 closure attempt

`phase-11b-ap001-closure-v1.json` schedules ten new AP-001 initial attempts with the
existing local Ollama configuration. Every initial trial runs even if an earlier trial
reaches the target sequence. A public-test false-green may receive at most two bounded
repair attempts, and repair stops after conversion.

This phase does not use Nebius credentials and does not claim multi-model evidence.
Frozen v0.1 attempts remain untouched.

Preview the exact run plan without calling a model:

```powershell
python .\programs\repository-agent-reliability\runner\batch.py `
  --plan .\programs\repository-agent-reliability\experiments\phase-11b-ap001-closure-v1.json
```

Live execution is deliberately explicit:

```powershell
$env:OLLAMA_MODEL = "llama3:latest"
python .\programs\repository-agent-reliability\runner\batch.py `
  --plan .\programs\repository-agent-reliability\experiments\phase-11b-ap001-closure-v1.json `
  --configuration-id ollama-llama3-latest `
  --execute
```

Execution refuses a dirty worktree because every attempt records `HEAD` as its evaluator
source commit. It also refuses to overwrite a non-empty staging directory and checks
that the observed provider and model match the preregistered configuration.

No staged result should be copied into `tasks/AP-001/evidence/live/` until every attempt
has a manifest, its source commit is available, and source-exact initial or repair replay
passes as applicable.

After a complete staged batch, generate counts and Wilson confidence intervals with:

```powershell
python .\programs\repository-agent-reliability\runner\batch_report.py `
  --plan .\programs\repository-agent-reliability\experiments\phase-11b-ap001-closure-v1.json `
  --batch-root .\runs\live\rarb\phase-11b-ap001-closure-v1 `
  --out-json .\runs\live\rarb\phase-11b-ap001-closure-v1\batch-summary.json `
  --out-md .\runs\live\rarb\phase-11b-ap001-closure-v1\batch-summary.md
```
