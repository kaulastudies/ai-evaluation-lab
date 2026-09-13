# Local Evaluation Evidence

This directory contains compact public Evaluation Records generated from successful local runs.

Raw Inspect `.eval` logs and Harbor job directories are intentionally not committed. They can contain bulky runner detail and machine-local paths. The public records retain:

- runner/model/task identity;
- deterministic score/reward;
- source-artifact SHA-256;
- repository commit SHA;
- task contract hash where applicable;
- canonical Evaluation Record hash.

Current evidence:

- `inspect-llama3-baseline.json` — local Ollama `llama3:latest` through Inspect AI.
- `harbor-oracle-route-policy.json` — local Harbor oracle/reference execution of `route-policy-repair`.
- `summary.json` — compact index of the accepted records.
