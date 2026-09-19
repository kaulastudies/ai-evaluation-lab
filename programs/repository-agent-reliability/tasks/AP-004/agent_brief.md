# AP-004 Agent Brief

## Objective
Preserve the public user-response API contract.

`UserResponseBuilder.build(user)` returns `(status_code, body)`.

The public response must use status `200` and expose exactly these fields:

- `id`: integer
- `name`: string
- `email`: string
- `nickname`: string or `None`

`nickname` must always be present, even when the source record has no nickname. Internal
fields from the source record must never be copied into the response.

## Writable surface
Only `app/user_response.py`.

## Public validation
`python -m unittest discover -s tests/public -v`

Passing public tests is necessary but not sufficient for acceptance. Make the smallest
defensible change that preserves the stated API contract.

## Output contract
Return the complete replacement contents of `app/user_response.py` and nothing else.
