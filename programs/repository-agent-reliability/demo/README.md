# RARB Demo Evidence

This directory contains a judge- and stakeholder-facing evidence brief generated from
`metrics/summary.json`.

The brief is deliberately descriptive. It highlights the strongest demonstrated RARB
behavior while keeping unproven claims visible, especially the fact that the current
evidence set does **not** yet contain a successful bounded repair conversion.

Generate it with:

```powershell
python .\programs\repository-agent-reliability\demo\build_evidence_brief.py `
  --out-json .\programs\repository-agent-reliability\demo\EVIDENCE_BRIEF.json `
  --out-md .\programs\repository-agent-reliability\demo\EVIDENCE_BRIEF.md
```

Validate it with:

```powershell
python .\programs\repository-agent-reliability\demo\demo_check.py
```

## One-command demo entrypoint

`run_demo.py` regenerates the metrics and evidence brief, runs the current runner
regressions, source-exact initial-attempt replay, source-exact repair replay, metrics
validation, and demo-evidence validation, then emits compact machine-readable and
human-readable status artifacts.

Run:

```powershell
python .\programs\repository-agent-reliability\demo\run_demo.py `
  --out-json .\programs\repository-agent-reliability\demo\DEMO_STATUS.json `
  --out-md .\programs\repository-agent-reliability\demo\DEMO_STATUS.md
```

A green run means the generated metrics/brief still match the committed evidence, the
current evaluator regressions pass, and historical initial and repair evidence remains
source-exact replayable without model inference.

This command does not run a live model and does not create new benchmark evidence.
