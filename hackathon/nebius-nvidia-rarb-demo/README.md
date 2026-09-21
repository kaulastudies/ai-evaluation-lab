# RARB — Nebius × NVIDIA Hackathon Demo

Judge-facing demo for the **Repository Agent Reliability Benchmark (RARB)** in the Nebius × NVIDIA Global AI Hackathon, Coding & Agentic Engineering track.

## What this demo shows

The interface presents three real evidence patterns already committed to AI Evaluation Lab:

1. a Phase 12 Nebius Token Factory / NVIDIA Nemotron `VERIFIED_PASS`;
2. the single preserved Phase 12 `llama3:latest` `VERIFIED_FAIL`;
3. the AP-005 public-test false-green followed by a successful bounded repair conversion.

The **Replay stored evidence** control is intentionally a visualization of committed evidence. It does not pretend to trigger fresh model inference.

## Run locally

No build step or dependency installation is required.

```bash
cd hackathon/nebius-nvidia-rarb-demo
python -m http.server 8080
```

Open `http://localhost:8080`.

## Deploy on Vercel

Import the public repository and set the Vercel project **Root Directory** to:

```text
hackathon/nebius-nvidia-rarb-demo
```

This is a dependency-free static site.

## Submission package

- [Devpost draft](submission/DEVPOST_DRAFT.md)
- [Demo video script](submission/VIDEO_SCRIPT.md)
- [Judge testing instructions](submission/JUDGE_TESTING.md)
- [Significant hackathon-period updates](submission/SIGNIFICANT_UPDATES.md)
- [Nebius / NVIDIA feedback draft](submission/NEBIUS_NVIDIA_FEEDBACK.md)

## Live Nebius runtime

The underlying RARB project makes runtime calls to Nebius Token Factory through the
OpenAI-compatible chat-completions endpoint. A minimal authenticated connectivity check is
available at `scripts/nebius_token_factory_smoke.py`; repository-task Nebius/NVIDIA evidence
is preserved under the canonical RARB evidence paths below. API keys remain server/local
environment variables and are never embedded in the browser demo.

## Canonical evidence

The demo does not rewrite the frozen evidence. Canonical artifacts remain under:

- `programs/repository-agent-reliability/demo/EVIDENCE_BRIEF.md`
- `programs/repository-agent-reliability/metrics/REPORT.md`
- `programs/repository-agent-reliability/experiments/results/phase-12-cross-model-replication-v1/`
- `programs/repository-agent-reliability/tasks/AP-001/evidence/live/*phase12*/`
- `programs/repository-agent-reliability/tasks/AP-005/evidence/live/`

## Evidence boundary

Phase 12 is one task, three fixed configurations, and ten trials per configuration. It does not establish general coding-agent performance, provider-wide superiority, or production-scale reliability. The original AP-001 Section 9 sequence remains open as written.
