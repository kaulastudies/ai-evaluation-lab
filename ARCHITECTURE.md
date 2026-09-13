# Architecture

## Operating flow

```text
PROJECT
  |
  v
WORK PACKAGE
  |
  v
EVALUATION TASK
  |----------------------|
  v                      v
EVIDENCE / EXPECTATION   MODEL RUN
  |                      |
  |----------+-----------|
             v
      INDEPENDENT REVIEW
             |
             v
          VERIFIER
        /          \
     AGREE        DISAGREE
       |              |
       |              v
       |         ADJUDICATION
       |              |
       +-------+------+
               v
      ACCEPTED EVALUATION RECORD
               |
        +------+------+
        v             v
 FAILURE ANALYTICS   REGRESSION
        |             |
        +------+------+
               v
        RELEASE EVIDENCE
```

## Design principles

1. Tasks are versioned.
2. Model execution is replaceable and cannot define evaluation truth.
3. Human review and deterministic verification are independently inspectable.
4. Disagreement is recorded, not silently overwritten.
5. Adjudication is explicit.
6. Accepted records are serialized canonically and SHA-256 hashed.
7. Regression links are first-class.
8. Public Alpha uses only synthetic/public material.

## Alpha components

- `tasks.py` - task loading and validation.
- `providers/` - model-provider interface and adapters.
- `verifier.py` - deterministic boundary tests.
- `pipeline.py` - review, verification, disagreement and adjudication.
- `records.py` - canonical record creation and hashing.
- `alpha_demo.py` - synthetic end-to-end demo.
