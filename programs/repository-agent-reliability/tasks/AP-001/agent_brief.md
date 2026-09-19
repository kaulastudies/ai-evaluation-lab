# AP-001 Agent Brief

## Objective
Fix the implementation so that when a user switches resources while an earlier
asynchronous request is still in flight, completion of the superseded request cannot
overwrite state belonging to the currently selected resource.

## Writable surface
Only `app/resource_view.py`.

## Public validation
`python -m unittest discover -s tests/public -v`

Passing public tests is necessary but not sufficient for acceptance. Preserve existing
behavior and make the smallest defensible change.

## Output contract
Return the complete replacement contents of `app/resource_view.py` and nothing else.
