"""Offline delegated-authority revocation + tamper-evident receipt demonstration.

Synthetic fixture only. Not a TIP protocol node or cryptographic signature implementation.
"""
import hashlib
import hmac
import json
from dataclasses import dataclass


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()


@dataclass(frozen=True)
class Delegation:
    delegation_id: str
    principal: str
    agent: str
    scopes: tuple[str, ...]
    not_before: int
    expires_at: int


class Gate:
    """Local test fixture with append-only hash-chain receipts and HMAC fixture authentication."""

    def __init__(self, key=b'local-test-key-not-production'):
        self.delegations = {}
        self.revocations = {}
        self.receipts = []
        self.key = key

    def _record(self, kind, at, payload):
        prev = self.receipts[-1]['hash'] if self.receipts else '0' * 64
        body = {'seq': len(self.receipts) + 1, 'kind': kind, 'at': at,
                'payload': payload, 'previous_hash': prev}
        receipt = {**body, 'hash': digest(body)}
        receipt['fixture_mac'] = hmac.new(self.key, canonical(receipt), hashlib.sha256).hexdigest()
        self.receipts.append(receipt)
        return receipt

    def grant(self, delegation):
        if delegation.delegation_id in self.delegations:
            raise ValueError('duplicate delegation id')
        self.delegations[delegation.delegation_id] = delegation
        return self._record('GRANT', delegation.not_before, vars(delegation))

    def revoke(self, delegation_id, at, issuer):
        d = self.delegations[delegation_id]
        if issuer != d.principal:
            return self._record('REJECT_REVOCATION', at,
                                {'delegation_id': delegation_id, 'reason': 'unauthorized_issuer'})
        if delegation_id in self.revocations:
            return self._record('REJECT_REVOCATION', at,
                                {'delegation_id': delegation_id, 'reason': 'already_revoked'})
        self.revocations[delegation_id] = at
        return self._record('REVOKE', at, {'delegation_id': delegation_id, 'issuer': issuer})

    def action(self, delegation_id, agent, scope, at):
        d = self.delegations.get(delegation_id)
        reason = None
        if d is None:
            reason = 'unknown_delegation'
        elif agent != d.agent:
            reason = 'wrong_agent'
        elif not (d.not_before <= at < d.expires_at):
            reason = 'outside_validity_window'
        elif delegation_id in self.revocations and at >= self.revocations[delegation_id]:
            reason = 'revoked'
        elif scope not in d.scopes:
            reason = 'scope_denied'
        decision = 'REJECT' if reason else 'ALLOW'
        return self._record('ACTION', at, {'delegation_id': delegation_id, 'agent': agent,
                    'scope': scope, 'decision': decision, 'reason': reason})

    def verify(self):
        prev = '0' * 64
        for i, receipt in enumerate(self.receipts, 1):
            body = {k: receipt[k] for k in ('seq', 'kind', 'at', 'payload', 'previous_hash')}
            if receipt['seq'] != i or receipt['previous_hash'] != prev:
                return False
            if not hmac.compare_digest(receipt['hash'], digest(body)):
                return False
            unsigned = {k: v for k, v in receipt.items() if k != 'fixture_mac'}
            expected = hmac.new(self.key, canonical(unsigned), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(receipt['fixture_mac'], expected):
                return False
            prev = receipt['hash']
        return True


def run_demo():
    gate = Gate()
    gate.grant(Delegation('del-001', 'principal-A', 'agent-A', ('read', 'write'), 100, 1000))
    before = gate.action('del-001', 'agent-A', 'write', 150)
    gate.revoke('del-001', 200, 'principal-A')
    after = gate.action('del-001', 'agent-A', 'write', 201)
    return gate, {'before': before['payload']['decision'],
                  'after': after['payload']['decision'],
                  'after_reason': after['payload']['reason'],
                  'chain_verified': gate.verify()}


if __name__ == '__main__':
    gate, summary = run_demo()
    print(json.dumps({'summary': summary, 'receipts': gate.receipts}, indent=2))
  
