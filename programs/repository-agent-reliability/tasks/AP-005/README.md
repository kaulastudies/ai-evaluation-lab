# AP-005 — Data transformation edge cases

AP-005 tests whether a coding agent can repair a plausible transformation routine when
ordinary happy-path tests miss falsy-value, cardinality, optional-field, and mutation
edge cases.

The vulnerable fixture passes its public test because that test uses only active rows,
non-zero integer values, and non-empty notes. The qualified verifier additionally checks
that:

1. row count, order, and duplicate identifiers are preserved;
2. `0` and `False` remain exact values with exact scalar types;
3. missing, empty-string, and explicit-`None` note states remain distinct where the
   contract requires;
4. source rows are not mutated and output records expose exactly the public fields.

The task must be verifier-qualified before any live model run is admitted as evidence.
