# AP-003 — Idempotent event processing

AP-003 targets duplicate-delivery reliability.

The synthetic processor applies a numeric side effect for each event. Delivery systems
may retry an event, so `event_id` is the idempotency key: the first delivery must apply,
while every later delivery with the same `event_id` must be ignored even if the retried
payload differs.

Public tests cover ordinary first-time and distinct-event behavior. The qualified
verifier adds duplicate-delivery, same-payload collision, and changed-payload retry
checks.

The verifier must qualify against the reference solution, the known-bad implementation,
and all configured critical mutations before scoring an agent candidate.
