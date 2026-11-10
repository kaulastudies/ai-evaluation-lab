# Provenance and TIP integration plan

8 November 2026 · design proposal; no TIP integration is deployed by this document

ProofPay can make payment investigations easier by preserving the connection between a request, its approval, the attempted action and the observed result. The next useful provenance step is a versioned receipt that an independent reviewer can check. External signing or registration should follow a tested receipt contract, rather than determine whether a payment succeeded.

## What exists in this application

| Evidence | Implemented behavior | Boundary |
|---|---|---|
| Approval digest | `service.ts` hashes an ordered JSON array containing operation ID, workspace ID, SKU, title, integer amount, currency, merchant, mode, approval version and expiry using SHA-256. Dispatch checks the stored digest. | This is an application integrity check. An actor with database and application control can replace the record and digest. It is not a human signature or external attestation. |
| Provider verification record | Confirmation stores selected order and capture fields, observation time, operation ID, source and mode with the accounting transition in a D1 transaction. | ProofPay records its observation of a provider response. PayPal has not signed this exported record. Rehearsal records are explicitly simulated. |
| Model provenance | A proposal may retain bounded provider response/model identifiers, provider origin and receipt time. | These are adapter observations. They do not prove which model executed, establish output correctness or demonstrate a genuine model run by themselves. |
| Events and export | An owner can inspect an operation's ordered events, request IDs, approval digest and verification records. Receipt schema 1 includes the exact approval binding and workspace ID needed for offline recomputation. | The database log is not externally anchored, independently timestamped or complete by cryptographic construction. Older exports lack the binding fields and must be re-exported. |
| Offline receipt verifier | `scripts/verify-receipt.mjs` independently recomputes the existing SHA-256 approval digest and checks confirmation fields against the operation and its stored event. | This establishes consistency within an unsigned record, not authenticity, event completeness, current execution authority, a genuine provider call or TIP compatibility. |
| Agent identity | The operation contains a display label and a proposal-source label. | No registered agent identity, signed delegation, agent key lifecycle or ANS resolution is implemented here. |

Source: [service](../lib/proofpay/service.ts), [types](../lib/proofpay/types.ts), [AI adapter](../lib/proofpay/ai.ts) and [architecture](ARCHITECTURE.md). None of these controls establishes TIP compatibility, legal non-repudiation, regulatory compliance or production readiness.

## Keep three workstreams distinct

The team's STANAIC/digital-convergence discussions and separate `tip-agent-receipts` research prototype are relevant prior work. That prototype has been described by the team as an ANS-style registry with delegation, signed receipts and batch checkpoints using ML-DSA-65 and SHAKE-256. Its source and reported test/throughput results were not imported or independently rerun in this ProofPay review. Those results must not appear as ProofPay results.

The public Trust Identity Protocol pages at `theailab.org` identify their publisher as The AI Lab Intelligence Unobscured, Inc. Public searches in this review did not establish the exact relationship between that publisher and the team's STANAIC work. Treat the relationship as unresolved; do not infer an affiliation or endorsement from a matching acronym. [1]

The publisher's agent-observability page describes a commercial service with signed agent records, while its dated 15 October 2026 announcement describes agent identities, delegations, action receipts and network-wide agent revocation as proposed. These pages do not establish an available, versioned integration contract for ProofPay. Before implementing an adapter, obtain the applicable specification/version, license, API or SDK, test-network access, key/identity requirements and a working interoperability example. [2][3]

ProofPay integration is the third workstream. It is currently absent. Use “experimental provenance adapter” for development work until the required conformance evidence exists.

## Proposed receipt contract

Use a new schema version; do not silently change the existing approval digest. Keep source evidence and derived observations separate.

| Part | Proposed contents |
|---|---|
| Envelope | Schema/profile version, receipt ID, operation ID, workspace scope, rehearsal/sandbox mode, creation time, source-code version and exact hash/signature algorithm identifiers. |
| Actors | Stable application actor IDs with roles such as requester, proposer, approver and executor; issuer/key IDs only when verified. Preserve missing actor evidence as missing. |
| Authority | Exact approval version/digest, scope, expiry and any future signed delegation reference. Distinguish application owner approval from native PayPal buyer approval. |
| Action | Attempt ID, tool/adapter version, original provider request IDs and state transition. A retry or lookup must not become an unrelated payment operation. |
| Observation | The existing allowlisted provider snapshot, its source and observed time. Preserve a separate field for external provider signatures if a provider actually supplies and verifies one. |
| Integrity | Digest of exact canonical bytes, previous receipt/checkpoint reference, signer key ID and detached signature when available. An external registration receipt belongs in a separate attachment. |

This maps naturally to an entity/activity/agent provenance model, but no W3C PROV serialization or conformance is claimed. W3C PROV-O provides a vocabulary for exchanging such relationships; an export mapping would need its own tests. [4]

### Preserve financial meaning during canonicalization

Define and version the receipt's JSON serialization profile. RFC 8785 JCS is one candidate; it specifies deterministic JSON processing, rejects duplicate property names and preserves string data rather than performing Unicode normalization. It is an Informational RFC, not an IETF Standards Track specification. [5]

Use typed integer minor-unit amounts within a validated range. Reject unsupported currencies, negative purchase amounts, non-finite values and ambiguous representations before signing. Reject duplicate keys before ordinary JSON parsing can discard them. Keep provider amount strings exactly as observed alongside the validated comparison value.

Do not apply a content-oriented normalization routine to executable payment authority. A proposed CNA profile must first demonstrate that meaningful changes remain distinguishable. Test `100` versus `-100`, currency and merchant substitutions, punctuation, whitespace inside strings, Unicode lookalikes, reordered arrays, absent versus null fields and version changes. Formatting-only changes outside string values may have the same canonical representation only when the selected profile explicitly defines that equivalence.

### Signing, delegation and revocation

Import the separate research prototype only after pinning its source, checking its license and reproducing its tests in an isolated environment. Keep signer keys outside the payment database and model context. Define key issuance, rotation, compromise response and recovery before enabling signatures. NIST FIPS 204 specifies ML-DSA; selecting that algorithm does not validate a particular implementation or make the complete application “post-quantum secure.” [6]

A service signature must say that the service signed an observation. Do not relabel it as the owner's personal signature. Record a distinct approval artifact only if the owner actually performs the required signing ceremony. Do not add biometric collection to this purchasing prototype.

Future delegation should bind the principal, agent, workspace, permitted action, merchant, currency, amount ceiling, validity window and audience. An agent's identity or registry listing alone grants no payment authority. Recheck delegation and revocation at dispatch; an unavailable authority source must not silently permit new execution. Preserve read-only investigation of previously dispatched operations.

Record revocation time and reason separately from historical signature verification. Distinguish “signature matches the recorded key,” “key trusted at the relevant time” and “key currently revoked.” A fresh signature over an old export cannot prove that the old approval was signed when it happened.

### External registration without changing payment truth

Write a receipt/outbox item transactionally with the relevant local event. A separate registrar can submit its digest or checkpoint using a stable registration key. Retries must be idempotent. Registry failure leaves an explicit `pending` or `failed` anchoring state; it must not reverse a confirmed payment, release an uncertain reservation or trigger another capture.

Keep prompts, personal identifiers, transaction details and keys out of public registrations. Even a hash of a predictable amount or small catalogue can be guessed; hashing is not anonymization. Assess private registration or a randomized commitment with controlled disclosure, and document retention and deletion consequences before publishing anything. A chain can reveal alteration relative to a trusted checkpoint; it cannot prove that every real-world action was logged.

## Offline verifier and the next acceptance gate

The earlier export omitted `workspace_id`, although it was part of the approval digest. Receipt schema 1 now adds owner-only `operation.workspaceId` and an `approvalBinding` containing the exact field order, values and `proofpay-approval-v1` profile. The digest algorithm is unchanged: SHA-256 over the UTF-8 bytes of JavaScript `JSON.stringify` applied to the ordered array. This is a narrow application profile, not JCS, CNA or a TIP profile.

Run the read-only checker against a fresh exported file:

```sh
node scripts/verify-receipt.mjs /path/to/receipt.json
```

Exit 0 reports internal consistency as JSON; exit 1 reports an unsupported, malformed or inconsistent input. The checker makes no network requests. It accepts only receipt schema 1, the exact listed object fields, the existing ordered-array approval profile, USD with integer minor units and a single final full capture for a confirmed operation. Unknown fields, schema/profile versions and multi-capture/refund structures require a new reviewed contract rather than silent acceptance.

Input limits are 1 MiB per regular file, 32 levels of JSON nesting, 5,000 events, strings up to their declared field limit, positive safe integer versions/timestamps and purchase amounts up to 999,999,999,999 cents. It rejects duplicate decoded JSON keys, invalid UTF-8, unpaired Unicode surrogates, non-finite numbers and negative zero. The largest text fields accepted by the operation schema are 8,192 characters; event detail is limited to 16,384 characters. An oversized genuine export may be unsupported; do not truncate it to make it pass.

The [receipt tests](../tests/review-receipt.mjs) exercise real local service exports backed by SQLite and the simulated provider, then mutate every approval binding field and provider confirmation field. These are local rehearsal results, not PayPal or model execution evidence. A deliberate whole-record rewrite test also demonstrates the boundary: an author who replaces the data and digest can create another internally consistent record. Missing model evidence is not inferred from labels or prose, and an expired historical approval is not permission to execute again.

The next implementation should add a separately versioned signed-receipt profile only after the receipt contract is stable and key ownership is defined. Acceptance requires wrong-key, revoked-key, expired-delegation, cross-workspace replay, altered-record, missing-checkpoint and offline-verification tests. External TIP/ANS support additionally requires a confirmed protocol identity and demonstrated interoperability. Signing and registration remain roadmap work.

## Sources checked 8 November 2026

1. [Publisher identity](https://theailab.org/about).
2. [Publisher's agent-observability description](https://theailab.org/agent-observability).
3. [15 October agent-record proposal](https://theailab.org/insights/public-record-of-what-ai-agents-do). The current [TIP overview/specification page](https://theailab.org/trust-identity-protocol) is a separate source; verify the applicable profile before integration.
4. [W3C PROV-O](https://www.w3.org/TR/prov-o/).
5. [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/info/rfc8785/).
6. [NIST FIPS 204](https://csrc.nist.gov/pubs/fips/204/final), including its published errata notice.
