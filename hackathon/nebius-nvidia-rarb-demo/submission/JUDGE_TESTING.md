# Judge Testing Instructions

## Fastest path

1. Open the public hosted demo URL supplied in Devpost.
2. In **Judge Mode**, switch among:
   - Nebius / Nemotron pass
   - Preserved Phase 12 failure
   - False-green → repair
3. Click **Replay stored evidence** to visualize the preserved replay sequence.
4. Use **Open canonical evidence** to inspect the corresponding committed artifacts.

The browser interface intentionally visualizes committed evidence. It does not send a secret API key from the browser or represent a UI animation as fresh model inference.

## Run the judge interface locally

From the repository root:

```bash
cd hackathon/nebius-nvidia-rarb-demo
python -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

No JavaScript package install or build step is required.

## Run the RARB evidence demo

From the repository root:

```bash
python programs/repository-agent-reliability/demo/run_demo.py
```

The command regenerates/checks RARB evidence artifacts and runs the deterministic/replay validation suite. A successful run finishes GREEN.

## Verify Phase 12 evidence integrity directly

```bash
python programs/repository-agent-reliability/runner/phase12_evidence_check.py
```

This checks the promoted Phase 12 evidence, fixed configuration matrix, hashes, preserved failure, replay state, claim boundaries, and credential-marker scan.

## Optional live Nebius connectivity check

A live provider check requires your own Nebius Token Factory API key.

Set:

```text
NEBIUS_API_KEY=<your key>
NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b
```

Then run:

```bash
PYTHONPATH=src python scripts/nebius_token_factory_smoke.py
```

The script makes a runtime Token Factory call and reports provider, model, latency, token usage, returned response, and connectivity status.

Do not commit API keys.

## Canonical hackathon evidence

### Nebius/NVIDIA pilot

```text
programs/repository-agent-reliability/experiments/results/phase-11c-nebius-nemotron-pilot-v1/
programs/repository-agent-reliability/tasks/AP-001/evidence/live/ap001-nebius-nemotron-001/
```

### Phase 12 replication

```text
programs/repository-agent-reliability/experiments/results/phase-12-cross-model-replication-v1/
programs/repository-agent-reliability/tasks/AP-001/evidence/live/*phase12*/
```

### False-green and successful bounded repair

```text
programs/repository-agent-reliability/tasks/AP-005/evidence/live/ap005-ollama-llama3-001/
programs/repository-agent-reliability/tasks/AP-005/evidence/live/ap005-ollama-llama3-002-repair/
```

## Expected evidence snapshot

- 51 attempts
- 43 VERIFIED_PASS
- 5 VERIFIED_FAIL
- 3 HOLD
- 5 qualified tasks
- 0 / 17 critical verifier mutation escapes
- Phase 12: 29 / 30 VERIFIED_PASS, 1 preserved VERIFIED_FAIL
- Phase 12: 30 / 30 source-exact no-model replays verified

These are bounded observations from the committed evidence set, not general model-performance claims.
