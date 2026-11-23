# ProofGate pull-request demo

A small record transformer from task AP-005 of the Repository Agent Reliability program. Every pull request that touches this folder is checked by [ProofGate](../../integrations/proofgate-action).

The code on `main` has three bugs that the public test does not catch: inactive rows are dropped, a value of `0` becomes `None`, and an empty note becomes `None`. The independent verifier in `.proofgate/` (trusted, read from the base branch) checks four requirements the task actually states.

The demo pull requests replay patches recorded from a real coding-agent run, without new model calls:

| Pull request | Patch | Expected verdict |
|---|---|---|
| Agent attempt 1 | `ap005-ollama-llama3-001` | ⚠️ False-green: public test passes, all four gates fail |
| Agent repair | `ap005-ollama-llama3-002-repair` | ✅ Verified pass |
| Verifier edit | changes `.proofgate/` | ⏸️ Hold: a PR cannot change the rules it is judged by |

Run it locally from the repository root:

```bash
python3 integrations/proofgate-action/proofgate_pr.py --base main --head HEAD \
  --contract examples/proofgate-pr-demo/.proofgate/contract.json
```
