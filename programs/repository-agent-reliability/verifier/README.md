# Verifier Boundary

Implementation rules:

- verifier executes outside the coding agent's writable workspace;
- task contract and verifier version are immutable during a scored run;
- verifier returns structured gate IDs and bounded diagnostics;
- hidden verifier source is never exposed to the repair model;
- verifier qualification is executed before agent scoring;
- if qualification fails, scored runs return `HOLD`.

The first executable verifier will be implemented only after the AP-001 synthetic fixture
and its reference / known-bad controls are frozen.
