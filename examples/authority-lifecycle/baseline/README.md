# Delegated authority revocation — offline receipt demo

This small, synthetic proof of concept tests an agent delegation that is valid before revocation and rejected afterward. Every grant, revocation attempt, and action decision receives an ordered receipt with a hash-chain link and **local test-only HMAC**. The project uses Python standard library only; no network or paid services.

## Run

```bash
./run.sh
```

On Windows without a POSIX shell:

```powershell
python -m unittest discover -s tests -v
python revocation_demo.py > evidence.json
```

The script runs five independent tests then writes `evidence.json`, showing the grant, allowed action, revocation, and rejected post-revocation action. The test suite was executed locally on 5 Nov 2026: **5/5 passed**.

## What the tests exercise

1. An authorized agent can use delegated `write` scope before revocation. A later action is rejected with reason `revoked` and both decisions have receipts.
2. A non-principal cannot revoke the delegation; the failed attempt is recorded.
3. Replaying or re-registering the same revoked delegation ID cannot restore authority.
4. Wrong agent, out-of-scope action, and expired authority fail closed with recorded reasons.
5. Modifying a receipt after the fact invalidates local receipt verification.

## Relationship to existing work

The earlier `tip-agent-receipts.zip` is not available in this workspace, so this is a **standalone runnable extension concept**, not a patch to that original archive. It follows the previously described design of delegated authority, refusal/acceptance receipts, and verifiable evidence. It does **not** incorporate the Evercraft receipt-handling fix because its source was not available for inspection.

Relevant TIP public source inspected:

- [`node/src/services/revocation-service.js`](https://github.com/theailaborg/tip-protocol/blob/main/node/src/services/revocation-service.js) validates a signed revocation proposal and submits a transaction. A proposal is not necessarily a committed revocation.
- [`sdk/src/trust.js`](https://github.com/theailaborg/tip-protocol/blob/main/sdk/src/trust.js) exposes `getRevocations`, `isRevoked`, and `revoke`.

TIP identity revocation is **not equivalent** to revoking one agent's delegated scope. This example addresses a separate delegated-authority gate and should eventually be adapted to TIP's finalized state and identity/delegation model.

## Limitations and next integration steps

- No actual TIP node, ledger consensus, ML-DSA-65 signatures, Merkle checkpoints, or external verifiers.
- The HMAC key is an illustrative static test secret. It is **not** asymmetric signing or nonrepudiation.
- The local integer timestamps are a trusted fixture clock. A production gate must use server-assigned trustworthy time or monotonic sequence numbers; it must reject backdated requests, stale cached status, and rollback/forked state.
- Revocation here is immediate local state; production must clarify **proposed vs committed** revocation and fail closed if current finalized state cannot be checked.
- No distributed racing, concurrent workers, tenant isolation, key rotation, external identity binding, or authorization service failures are tested.
- The log is append-only by convention in this process; persistence, anti-truncation, independent checkpoints and external anchoring remain unimplemented.
- Replace the fixture state store with original agent-receipts/TIP code after the archive is recovered and independently reviewed. Port the Evercraft receipt fix only after obtaining its exact patch and tests.

No GitHub changes, external submissions, or messages were made.
  
