# RARB Demo Evidence

This directory contains a judge- and stakeholder-facing evidence brief generated from
`metrics/summary.json`.

The brief is deliberately descriptive. It highlights the strongest demonstrated RARB
behavior while keeping unproven claims visible. The current evidence set contains one
successful bounded repair conversion on AP-005; it does **not** satisfy the original
AP-001-specific Section 9 sequence or establish statistically meaningful multi-model
performance. It now also records one preregistered, source-exact replayable
Nebius/NVIDIA AP-001 `VERIFIED_PASS`; that single pilot does not establish
production-scale performance.

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
