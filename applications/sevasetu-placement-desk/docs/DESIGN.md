# Proposed record-led placement workflow

This is Option B for review alongside SevaSetu Careers (Option A). It is a proposal for PDS 6, not a confirmed AWPO specification. It should complement existing placement services if the responsible team finds it useful.

## Record presence is not verification

An identifier locates a record; it does not authorise access or prove that every field is accurate. Each field or qualification needs a source, verification state and review date. This applies to information acquired before, during and after service. Existing records can contain claims, outdated values and revoked documents.

| Information | Proposed authoritative source to confirm with owner | Behaviour in this demo |
|---|---|---|
| Candidate ID, name and placement registration | Approved placement register and authenticated identity | Fictional ID lookup; candidate session restricted to own ID |
| DOB / age at a stated cutoff | Designated identity/service record | Unverified DOB gives review; raw DOB withheld from counsellor |
| Service dates and release status | Designated service/release record | Source shown; retiring is distinct from retired |
| Completed service | Approved reckonable-service field or approved calculation | Calendar interval only, capped at current sample date and cutoff; never labelled official reckonable service |
| Last pay | Designated pay record, only if needed for this workflow | Separate permission and purpose; absent from suitability rules and CV |
| Existing qualifications and skills | Source record or authorised certificate/role-history confirmation | Credited only when evidence status supports it; total service is not a substitute for job-specific experience |
| New or post-service qualification | Issuer confirmation or approved verification officer/process | Pending first; sample response must match identity, serial, metadata and fingerprint |
| Role requirements and vacancy lifecycle | Employer's current advertisement / authorised placement feed | Explicit illustrative requirements, cutoff and deadline; no inferred relaxation or equivalence |

The sample data is frozen at **2 November 2026** so the demonstration and tests are reproducible. A deployment date does not refresh the source records or make sample vacancies real. Production would use a trusted current date, refresh intervals and source change/revocation checks.

## Authentication and integration boundary

The browser talks to a small service contract: `catalog`, `lookup`, `assess`, `submit`, `verify`, `cv`, `history`. Its public implementation uses a fictional fixture entirely in the browser. The local implementation uses real HTTP requests to a Node service and projects records server-side.

Local endpoints are `POST /api/session`, `GET /api/catalog`, and `POST /api/{lookup,assess,submit,verify,cv,history}`. Requests include candidate ID and declared purpose; an optional lookup cutoff must be a valid ISO date. The authenticated actor is taken from the server session, never from the operation body. Session changes rotate the cookie while preserving the fictional case workspace. A separate server instance/session starts with a fresh sample register.

For a pilot, replace the demonstration session creator with the owner's approved identity provider. Resolve the candidate ID to a record on the server, enforce approved access and field projections there, keep real fixtures out of the static bundle, and store claims/reviews/logs in the approved environment. Do not send service records to a public model. The current rule and CV path does not need an LLM.

The production data adapter should return a record envelope including source system, record version, retrieval time, field-level authority, freshness, release status and permitted purposes. A verification response should include issuer authority, candidate binding, document reference, valid/revoked/unknown status, checked time and reviewer. Unknown or conflicting evidence must stay uncredited.

Document bytes are not uploaded in this prototype: an optional local test file is fingerprinted and only its metadata/hash reaches the local API. A real upload/review service would need approved storage, access, file checks, retention and reviewer workflow. No external issuer is contacted by this demonstration.

## Decision and CV behaviour

The comparison lists evidence against each stated requirement. Any unresolved evidence produces review and leaves other recorded gaps visible. A missing degree is not treated as an equivalent diploma; service length is not treated as trade experience; future service and future qualifications are not counted as already completed. Closed vacancies remain closed.

The CV includes only confirmed sample claims with source references. Unconfirmed, conflicting, expired and revoked qualifications are omitted. DOB and pay are excluded even for a verifier. A separate receipt lists the claims used, excluded qualification IDs and CV hash. This is a draft for human review, not a certification of eligibility.

Audit events record actor, purpose, action, outcome, candidate code and previous-event hash. They omit DOB, pay values and document contents. The in-memory hash chain can demonstrate integrity checks, but it is not a durable, append-only production audit service.

## Questions for the responsible team

1. Who is the primary user: placement staff, the candidate or both? Is this an addition to an existing portal?
2. Which organisation owns the register and identifiers, and who may retrieve which fields?
3. Are DOB, release dates, reckonable service and qualifications already verified individually? What source/freshness indicators exist?
4. Is last pay necessary for placement at all, and if so for what purpose and user?
5. Who verifies later qualifications, and is an issuer response, document review or another process required?
6. Who supplies current employer requirements, age cutoffs, relaxations and equivalence rules?
7. Which existing CV schema, export format and workflow should the prototype follow?
8. Could the owner provide a non-sensitive schema, anonymised sample export or sandbox for a supervised pilot? No real candidate data is requested for the public demo.

Options can be integrated later: Option A supplies vacancy discovery; Option B supplies authorised record retrieval and verified-fact preparation. The owner should first confirm that this division fits the actual need.
