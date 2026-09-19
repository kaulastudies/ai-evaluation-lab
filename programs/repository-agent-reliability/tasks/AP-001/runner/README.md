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
reference candidate, then repeats them to confirm deterministic replay hashes.
