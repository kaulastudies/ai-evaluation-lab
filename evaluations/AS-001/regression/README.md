# AS-001 Regression Gate

The repository-level `tests/test_as001.py` exercises the deterministic verifier against:

- reference PASS;
- correct-output known-bad boundary violation FAIL;
- wrong-answer FAIL;
- audit-sequence tamper FAIL;
- prohibited network-operation FAIL;
- path-traversal FAIL.

This regression gate validates the verifier and controls before any live model run is allowed.

It is not model-performance evidence.
