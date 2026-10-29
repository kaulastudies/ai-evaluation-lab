# Judge review and competition positioning

Reviewed against the official four equally weighted criteria on October 29, 2026. This is our internal assessment, not a prediction of the judges' scores.

| Criterion | Demonstrable strength | Remaining weakness | Concrete response |
| --- | --- | --- | --- |
| Technological implementation | Qualified Python verifiers, controlled model context, bounded repair, source-exact replay, preserved Nebius/Nemotron executions | New live Nemotron repair has not yet been run with a configured key | Provide the runtime action and capture one real result before presenting it as new evidence |
| Design | Judges can execute real checks in the browser, select faults, compare public tests with independent gates and export evidence | Cold Python runtime download; desktop-oriented code views | Host the pinned runtime on the demo origin, show progress/cancel, use one clear default case |
| Potential impact | Specific audience: engineers reviewing coding-agent patches and selecting agents for repository workflows | Evidence is synthetic; no measured production adoption or savings | Show a concrete falsy-value regression and its detection; describe production pilots as future work |
| Quality of idea | Qualify the verifier before trusting agent success; preserve failures and reproduce verdicts | Evaluation can look like another leaderboard if only aggregate scores are shown | Lead with the executable false-green and mutation challenge, then reveal the ledger and provenance |

## Strongest 60-second demonstration

1. Run the AP-005 recorded candidate: public PASS, independent FAIL.
2. Run the repaired candidate: public PASS, independent PASS.
3. Run the zero-to-null mutation: public PASS, AP005-G02 FAIL.
4. Run all six qualification controls: reference accepted, five faulty controls rejected.
5. Switch to the Nebius/Nemotron candidate and execute its real Python checks.

The repair example and Nebius candidate are separate, correctly attributed runs. Do not imply Nemotron produced the archived Ollama repair.

## Submission pitch

ProofGate helps engineers review coding-agent changes by making a verdict inspectable and reproducible. Its demo does not ask judges to trust a green score: they can run the Python checks, introduce a known fault, and inspect what fails. NVIDIA Nemotron generates and can repair repository-task candidates through Nebius Token Factory; a qualified verifier decides whether each candidate meets its contract.

## Required final evidence

- Working judge access without an account barrier or a tested alternative access path.
- Public code with the exact submitted revision and Apache 2.0 license.
- A public YouTube demonstration under three minutes, showing actual execution.
- Honest disclosure of existing work, significant submission-period additions, provider integration, feedback and remaining limits.
- Submission confirmation before October 30, 2026 at 10:30 PM IST.

Do not add unrelated features or Tavily calls solely to chase another prize. The strongest entry is the one whose main claim a judge can reproduce quickly.
