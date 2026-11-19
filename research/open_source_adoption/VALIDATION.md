# Validation and limits

Validated locally on 2026-10-29 against Lab baseline `c8f4b4ed0af988ebe8ca9821c472642ab4c20f63`.

| Check | Result |
|---|---|
| `python -m unittest discover -s research/open_source_adoption/tests -v` | 25 tests passed. |
| `PYTHONPATH=src python -m unittest discover -s tests -v` | 22 existing Lab tests passed. |
| `python ops/gates/validate_as001.py` | Passed; frozen AS-001 contract SHA-256 remains `379d5a5301c9a234e019c4c6ea2eb0cc25b48ce1e3050ad0cb3251ee55e51b2c`. |
| `python ops/gates/validate_as001_live_evidence.py` | Passed on published Ollama evidence; no live provider called. |
| `python ops/gates/validate_as001_groq_evidence.py` | Passed on published Groq evidence; no live provider called. |
| `python ops/gates/validate_as002.py` | Passed; frozen AS-002 contract and controls unchanged. |
| `PYTHONPATH=src python programs/repository-agent-reliability/runner/phase12_evidence_check.py` | All integrity checks passed. |
| `PYTHONPATH=src python programs/repository-agent-reliability/demo/run_demo_check.py` | Deterministic/source-exact replay gate passed. |
| `python -m compileall -q research/open_source_adoption programs/repository-agent-reliability` | Passed. |
| `python research/open_source_adoption/adoption.py catalogue-check` | All 125 supplied entries covered; 14 pinned public references; no marketplace code imported. |
| `python research/open_source_adoption/adoption.py isolation-check` | No local tracked or untracked nonignored changes outside `research/open_source_adoption/`. |
| Pinned upstream Inspect JSON fixture | One sample and its categorical `I` score preserved; no Lab verdict produced. See [UPSTREAM_SMOKE.json](UPSTREAM_SMOKE.json). |

The adapter tests cover multiple scorers, aggregate-score fallback refusal, failed and cancelled execution, missing attempts, invalidation, limits, early stopping, typed sample identities and epochs, duplicate keys, ambiguous numeric values, input bounds, digest mismatch, output determinism, omitted raw text, read-only CLI behavior, catalogue completeness, source pins and protected-path detection.

An initial test exposed that relying on the interpreter's recursion limit did not impose a predictable JSON-depth bound. The parser now checks nesting before decoding objects, and a control verifies that brackets and escaped quotes inside strings do not affect that bound. The final test result above includes that correction.

## What these results do not establish

- No model-performance, general safety, marketplace verification or production-readiness result is created.
- No new paid inference, training, hosted service, cluster, MCP connector, email or other external action was run.
- The Inspect test is a static-format compatibility smoke test. The full Inspect SDK, binary `.eval` format, aggregate metrics and transcript semantics were not exercised by the new adapter.
- The 14 upstream projects were reviewed as references, not installed or end-to-end tested. Root licences do not settle every dependency, dataset, private snapshot or hosted-service term.
- The existing Lab converter, records and contracts remain unchanged. New output is quarantined as `UNVERIFIED_EXTERNAL` and cannot be promoted by this prototype.
- Existing GitHub Actions are not edited to discover the new subtree tests. Those 25 tests are reported as local validation; existing PR CI runs its unchanged workflow.

The base-tree identities are recorded in [baseline.json](baseline.json). The PR must remain a draft with additions confined to this directory; no merge or deployment is part of this work.
