# AP-003 Agent Brief

## Objective
Make event handling idempotent. `event_id` is the idempotency key. The first delivery
of an event must apply its amount exactly once. Any later delivery with the same
`event_id` must be ignored, even if the retry carries a different amount.

## Writable surface
Only `app/event_processor.py`.

## Public validation
`python -m unittest discover -s tests/public -v`

Passing public tests is necessary but not sufficient for acceptance. Preserve ordinary
processing of distinct events and make the smallest defensible change.

## Output contract
Return the complete replacement contents of `app/event_processor.py` and nothing else.
