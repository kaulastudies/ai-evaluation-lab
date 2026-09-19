# AP-002 Agent Brief

## Objective
Fix the authorization policy so privileged roles are scoped to the actor's workspace.
An editor or admin may update the document only when actor and document belong to the
same workspace. Cross-workspace access must remain denied.

## Writable surface
Only `app/workspace_policy.py`.

## Public validation
`python -m unittest discover -s tests/public -v`

Passing public tests is necessary but not sufficient for acceptance. Preserve existing
same-workspace behavior and make the smallest defensible change.

## Output contract
Return the complete replacement contents of `app/workspace_policy.py` and nothing else.
