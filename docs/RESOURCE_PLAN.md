# Low-Cost Resource Plan

| Layer | Default |
|---|---|
| Repository / CI | GitHub public repository + standard CI |
| Local inference | Existing Ollama installation |
| Terminal task runtime | Harbor + Docker |
| Model/agent experimentation | Inspect |
| Control-plane state | Git + JSON first |
| Queryable local state | SQLite only when needed |
| Public evidence | Small versioned records and summaries |

## Scaling rules

1. Run one local agent task at a time until RAM/CPU/GPU use is measured.
2. Prefer deterministic gates before any model judge.
3. Reuse Docker layers and cached fixtures.
4. Use an already-installed Ollama model before downloading another large model.
5. Use free/credited cloud providers for comparisons and capability gaps.
6. Buy paid model calls only for funded work or a defined public milestone.
7. Add hosted observability only when collaboration needs justify it.
8. Add cloud sandboxes only when isolation or throughput requires them.
