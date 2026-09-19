# AP-004 - API contract regression

AP-004 targets externally visible API response-contract drift.

The synthetic response builder receives an internal user record and returns an HTTP-like
`(status_code, body)` tuple. The external contract requires:

- status code `200`;
- required response keys `id`, `name`, `email`, and `nickname`;
- stable field types;
- `nickname` to remain present with `null`/`None` when no nickname is available;
- no internal fields to leak into the public response.

Public tests cover only the ordinary happy path. The vulnerable implementation passes
those tests while omitting a nullable field on another input shape and leaking an
internal password hash. The qualified verifier exercises the complete contract.

The verifier must qualify against a reference implementation, the known-bad
implementation, and all configured critical mutations before scoring an agent candidate.
