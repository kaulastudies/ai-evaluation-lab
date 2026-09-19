# AP-001 Runner Boundary

The model-visible context is restricted to the agent brief, vulnerable source, and
public tests. The context manifest records their paths and hashes and explicitly excludes
`verifier/**`, `controls/**`, and `evidence/**`.

The trial runner:

1. refuses to score unless verifier qualification is `QUALIFIED`;
2. creates a temporary copy of the public fixture;
3. installs only the candidate implementation into that workspace;
4. runs public tests;
5. invokes the qualified verifier out of band;
6. checks that trusted evaluator files are unchanged after scoring;
7. emits a deterministic, hash-bound evaluation record.

Important wording: the local integrity check proves trusted files were unchanged after
scoring. It is not an OS-level filesystem sandbox. During live model generation, only
the model-visible workspace will be exposed to the model/agent. Stronger execution
isolation is a separate runtime control.

`offline_check.py` validates both a false-green known-bad candidate and a verified-pass
reference candidate, then repeats them to confirm deterministic record hashes.

## Replay bundles

`export_replay_bundle.py` creates a deterministic post-run ZIP containing the candidate,
public tests, qualified verifier source, qualification evidence, task contract,
model-context manifest, and evaluation record. The bundle contains no model credentials
and requires no model inference to replay.

`replay.py` validates artifact hashes and reproduces the public-test result, verifier
gates, final verdict, false-green classification, and evaluation-record hash.

`replay_bundle_check.py` exports and replays both the known-bad false-green control and
the reference passing control. A valid verifier failure is a successful replay when it
matches the recorded failure.

Replay bundles intentionally omit verifier re-qualification controls/reference solutions.
Use the full repository when re-qualification itself must be reproduced.

## Model candidate adapter

`model_trial.py` is the boundary between a model provider and the qualified AP-001
evaluation pipeline.

It builds the prompt only from the model-visible brief, vulnerable source, and public
tests. A provider response is converted into a single candidate `resource_view.py`,
subjected to a small AP-001 structural admission policy, and only then passed to the
existing trial runner.

The admission policy is **not** an operating-system sandbox. It is a pre-execution
contract check that rejects imports and a small set of introspection/file-execution
constructs that are unnecessary for AP-001. Strong runtime isolation remains a separate
control.

Live providers use the repository's existing provider abstraction. `--provider nebius`
therefore becomes available automatically once Token Factory access is working.

Example live command after Nebius access is available:

    python model_trial.py --provider nebius --label ap001-nebius-001 --out result.json --candidate-out candidate.py

`model_trial_check.py` validates three offline paths using the mock provider:

- known-bad candidate -> `VERIFIED_FAIL` with `false_green=true`;
- reference candidate -> `VERIFIED_PASS`;
- structurally prohibited candidate -> `HOLD` before execution.
