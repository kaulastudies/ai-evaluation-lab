# ProofGate Work Samples

A small, working extension of AI Evaluation Lab's RARB evidence tools, built on
4 November 2026. It exports a local work-sample packet for a conversation with a
human reviewer. This is an early prototype with zero external beneficiaries,
no employer pilot and no measured employment or income outcomes.

## Why build this

Someone learning AI evaluation or software testing needs to explain what they
checked, what failed and why the evidence supports their conclusion. A CV line,
certificate or passing test screenshot gives a reviewer little to inspect.
AI-generated patches make it especially important to distinguish the person's
declared contribution from the artifact's actual behavior.

This prototype puts those pieces in one portable packet. Its intended use is
practice and review for self-taught adults seeking evaluation and testing work.
Whether employers find it useful remains a question to test.

## What works today

- Export the public AP-005 failed attempt and successful repair with original
  task links, four gate results, candidate hashes and evaluation hashes.
- Reconstruct the packet from an immutable Git commit during verification.
- Record a pseudonymous, self-reported contribution and AI assistance.
- Generate a readable HTML file and a machine-readable JSON file locally.
- Keep the earlier failure when the successful repair is selected.
- Require explicit consent for the declaration included in the local export.

Export never executes candidate code or calls a model. It reads only two curated
synthetic public records from Git. Its evidence-integrity check is distinct from
running the verifier again. RARB's original replay commands do that separately.

## Run it

Use a full clone of AI Evaluation Lab, Python 3.10+ and Git. No API account or
third-party Python package is needed. Run from the repository root:

```sh
python applications/proofgate-work-samples/portfolio.py export \
  --declaration applications/proofgate-work-samples/demo-declaration.json \
  --out /tmp/proofgate-work-example
python applications/proofgate-work-samples/portfolio.py verify \
  /tmp/proofgate-work-example/packet.json
python -m unittest discover -s applications/proofgate-work-samples -v
```

Open the generated `index.html` locally. Choose a new output directory each time.
The example declaration is explicitly a demonstration; it is not a beneficiary
record or a claim that a person independently wrote the candidate code.

Fresh verification of the original examples, with no model inference:

```sh
python programs/repository-agent-reliability/runner/replay.py \
  --evidence-dir programs/repository-agent-reliability/tasks/AP-005/evidence/live/ap005-ollama-llama3-001
python programs/repository-agent-reliability/runner/repair_replay.py \
  --evidence-dir programs/repository-agent-reliability/tasks/AP-005/evidence/live/ap005-ollama-llama3-002-repair
```

Both commands reproduced their recorded outcomes on 4 November 2026: the initial
patch remained `VERIFIED_FAIL`, and the repair remained `VERIFIED_PASS`.

## What a packet does not prove

A software result is not a measure of a person's overall ability. The tool does
not verify identity, authorship, independent effort, educational qualifications
or suitability for employment. A hash is not a signature. Public practice tasks
can be copied and are unsuitable as secret or proctored hiring tests.

The first version supports only two historical AP-005 examples. It does not
onboard arbitrary repositories, verify a new worker's submission, match jobs,
rank applicants or operate an employment marketplace. Real work samples would
need agreed task ownership, consent, AI-use rules, safe execution and human
review. These features are future work, not current capabilities.

Declarations stay in local files. The tool has no upload service, telemetry,
login or external API call. Sharing a packet is a separate choice by its owner.

## Proposed pilot — not yet conducted

Interview 10 self-taught adult evaluators/testers and five hiring reviewers in
India before expanding the build. Ask participants to explain a real barrier
they faced and inspect whether this packet helps at all. Pay for interview time
where funding allows. Do not solicit confidential work or live job assessments.

If both groups find the format useful, co-design a six-week pilot with up to
20 consenting adult workers and three review partners. These are recruitment
targets, not existing participants or commitments. Each real work sample would
be scoped with a partner and paid; practice must not become unpaid commercial
production work. Employer decisions remain human-led.

Measure completion and dropout, participant time, packet comprehension, reviewer
time, correction requests and disagreements. Track paid trials, payment delays
and repeat paid work at 30 and 90 days, with consent. A usable packet without
better opportunity is an incomplete result. Report null outcomes and change or
stop the approach if the evidence does not support it.

## Sustainability hypothesis

Keep practice/export access free for workers. Test paid task design, verifier
maintenance and review support for organizations, with grants supporting early
research and access. Charge no recruitment fee to workers and promise no job.
There are currently no product revenues or employer contracts for this extension.

Original code follows the parent repository's Apache-2.0 license.
