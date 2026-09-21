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

Phase 11B is now **COMPLETE AND PROMOTED**. All ten planned initial trials ran from
source commit `37ed3813521f7cdaccbb6cc3a3d682854be1edb1`: nine reached
`VERIFIED_PASS`, and one admitted candidate failed public validation and remained
`VERIFIED_FAIL`. There were no false-greens, so no repair was eligible. All ten attempts
passed independent source-exact replay. The 90.0% verified-pass estimate has a 95%
Wilson interval of 59.6%–98.2%; it describes this one local configuration only.

Preview the exact run plan without calling a model:

```powershell
python .\programs\repository-agent-reliability\runner\batch.py `
  --plan .\programs\repository-agent-reliability\experiments\phase-11b-ap001-closure-v1.json
```

The historical live batch is frozen. Do not rerun or overwrite it. The dry-run command
above remains available to inspect the committed plan without calling a model.

Execution refuses a dirty worktree because every attempt records `HEAD` as its evaluator
source commit. It also refuses to overwrite a non-empty staging directory and checks
that the observed provider and model match the preregistered configuration.

The audited attempts are promoted under `tasks/AP-001/evidence/live/`, with the batch
ledger, report, and promotion record under `experiments/results/`.

After a complete staged batch, generate counts and Wilson confidence intervals with:

```powershell
python .\programs\repository-agent-reliability\runner\batch_report.py `
  --plan .\programs\repository-agent-reliability\experiments\phase-11b-ap001-closure-v1.json `
  --batch-root .\runs\live\rarb\phase-11b-ap001-closure-v1 `
  --out-json .\runs\live\rarb\phase-11b-ap001-closure-v1\batch-summary.json `
  --out-md .\runs\live\rarb\phase-11b-ap001-closure-v1\batch-summary.md
```

## Phase 11C: Nebius/NVIDIA pilot

`phase-11c-nebius-nemotron-pilot-v1.json` preregisters the first Nebius-backed
repository-task run. It schedules one AP-001 initial attempt using
`nvidia/nemotron-3-super-120b-a12b`. Only a genuine public-test false-green may enter
the bounded repair loop, with at most two repair attempts. Every observed outcome is
retained.

The earlier token-factory smoke test proved connectivity only. The completed pilot has
now passed artifact review and source-exact replay and is promoted into committed AP-001
evidence. The initial candidate reached `VERIFIED_PASS` directly, so no bounded repair
was triggered. A single model configuration and one initial trial do not support
statistical, broad multi-model, or production-scale claims.

Preview the fixed run plan without calling Nebius:

```powershell
python .\programs\repository-agent-reliability\runner\batch.py `
  --plan .\programs\repository-agent-reliability\experiments\phase-11c-nebius-nemotron-pilot-v1.json
```

Run the pilot from a clean checkout while keeping the API key ephemeral:

```powershell
$secureKey = Read-Host "Enter Nebius API key" -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $env:NEBIUS_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    $env:NEBIUS_MODEL = "nvidia/nemotron-3-super-120b-a12b"
    $env:PYTHONPATH = "src"

    python .\programs\repository-agent-reliability\runner\batch.py `
      --plan .\programs\repository-agent-reliability\experiments\phase-11c-nebius-nemotron-pilot-v1.json `
      --configuration-id nebius-nemotron-3-super-120b-a12b `
      --execute
}
finally {
    Remove-Item Env:NEBIUS_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:NEBIUS_MODEL -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
}
```

Do not rerun or delete a completed staging directory. Audit the result in place before
any evidence promotion decision.

## Phase 12: cross-model AP-001 replication

`phase-12-cross-model-replication-v1.json` preregisters 30 new AP-001 initial
attempts: ten each for local Ollama `llama3:latest`, local Ollama
`qwen2.5-coder:7b`, and Nebius/NVIDIA
`nvidia/nemotron-3-super-120b-a12b`. The configurations use the same task version,
temperature, output protocol, verifier, repair budget, and evaluator source commit.

The three-configuration matrix must execute as one batch. The runner sets each
non-secret model environment variable from the plan and refuses a split
`--configuration-id` execution. The Nebius key remains an ephemeral execution-time
credential and is not required to inspect or validate the preregistration.

Phase 12 was preregistered before execution and is now promoted as committed evidence.
The 30 labels are new observations; the Phase 11B and Phase 11C attempts remain frozen
and were neither rerun nor rewritten.

Preview the complete matrix without calling a model:

```powershell
python .\programs\repository-agent-reliability\runner\batch.py `
  --plan .\programs\repository-agent-reliability\experiments\phase-12-cross-model-replication-v1.json
```

Validate the preregistration, configuration-specific reporting, and explicit Phase 12
promotion:

```powershell
python .\programs\repository-agent-reliability\runner\phase12a_plan_check.py
```

Before live execution, `qwen2.5-coder:7b` must be available in Ollama and the Nebius
API key must be supplied ephemerally. A completed matrix will support bounded AP-001
configuration-level estimates only. It will not establish general coding-agent or
production-scale performance.

## Phase 12 promotion

`phase-12-cross-model-replication-v1` completed its fixed 30-attempt matrix and the
audited artifacts are promoted under `experiments/results/phase-12-cross-model-replication-v1/`
and `tasks/AP-001/evidence/live/`. The promotion record binds the source archive,
batch artifacts, evaluation records, replay reports, and canonical evidence paths by
SHA-256.

The completed matrix is one-task evidence: three configurations, ten trials per
configuration. It records 29 `VERIFIED_PASS`, one preserved `VERIFIED_FAIL`, zero
false-greens, zero repairs, and 30 source-exact no-model replays. AP-001 Section 9
remains open.
