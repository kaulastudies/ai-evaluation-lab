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
