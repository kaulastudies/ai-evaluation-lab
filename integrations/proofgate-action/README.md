# ProofGate for pull requests

ProofGate catches false-greens: pull requests whose tests pass while the code still breaks what the task required. On every pull request it runs your public checks and an independent verifier, then posts one verdict on the PR.

| Verdict | Meaning |
|---|---|
| ✅ `VERIFIED_PASS` | Public checks and every critical verifier gate passed |
| ⚠️ `FALSE_GREEN` | Public checks passed, but a critical gate failed |
| ❌ `VERIFIED_FAIL` | Public checks failed |
| ⏸️ `HOLD` | No trustworthy verdict: missing contract, verifier changed by the PR, or the verifier did not run cleanly |

## The trust rule

The contract and the verifier are always read from the **base** commit, never from the pull request. A pull request that edits them is put on `HOLD` for a person to review, instead of being judged by rules it wrote itself. This matters most when the code was written by an AI agent.

## Add it to a repository

1. Commit a contract and verifier to your default branch, for example in `.proofgate/`:

```json
{
  "task_id": "billing-export",
  "title": "Export keeps every invoice line",
  "trusted_dir": ".proofgate",
  "allowed_paths": ["src/export/*"],
  "public_checks": [{"id": "tests", "run": "pytest -q"}],
  "verifier": {"run": "python3 {trusted}/verify.py --json", "format": "json-gates"},
  "gates": [{"id": "G01", "description": "No invoice lines dropped", "critical": true}]
}
```

The verifier prints one JSON line: `{"gates": [{"id": "G01", "passed": true, "diagnostic": "..."}]}`. `{trusted}` is replaced with the path of the base-branch copy of `trusted_dir`.

2. Add a workflow:

```yaml
on: pull_request
permissions:
  contents: read
  pull-requests: write
jobs:
  proofgate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      - uses: kaulastudies/ai-evaluation-lab/integrations/proofgate-action@main
        with:
          contract: .proofgate/contract.json
```

Each run uploads `proofgate-evidence.json` as an artifact: the base and head commits, the contract hash, hashes of every trusted file, changed files, each command's exit code and bounded output, the gate results and the verdict.

## Live example

[`examples/proofgate-pr-demo`](../../examples/proofgate-pr-demo) uses task AP-005 from the Repository Agent Reliability program. Its pull requests replay recorded AI-agent patches, so you can see ProofGate catch a real false-green and then pass the real repair.

## Limits

- Beta (v0.1). It runs on standard-library Python on GitHub-hosted runners.
- The verifier runs in the same job as the candidate code. Reading it from the base commit stops a pull request from rewriting the rules, but it does not sandbox code that tries to interfere with the verifier at runtime. Use a separate job or container for untrusted contributors.
- Pull requests from forks get a read-only token, so the verdict appears in the job summary instead of a comment.
- A verdict covers the gates in the contract. It is not a general guarantee of correctness.
