"""Fail-closed preflight. Hosts must own backend mappings, identities and approvals."""
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, FrozenSet
import sqlite3

@dataclass(frozen=True)
class Policy:
    backends: Mapping[str,str]
    max_shots: int = 1024
    max_qubits: int = 8
    max_depth: int = 80
    allow_remote: bool = False
    remote_approvals: FrozenSet[tuple[str,str,str]] = frozenset()

    def __post_init__(self):
        for name, minimum in (('max_shots', 1), ('max_qubits', 1), ('max_depth', 0)):
            value = getattr(self, name)
            if type(value) is not int or value < minimum:
                raise ValueError(f'{name} must be an integer >= {minimum}')

@dataclass(frozen=True)
class ExecutionRequest:
    actor: str
    request_id: str
    target_id: str
    shots: int

@dataclass(frozen=True)
class CircuitFacts:
    qubits: int
    depth: int

@dataclass(frozen=True)
class Decision:
    verdict: str
    reasons: tuple[str,...]
    reserved: bool = False

class ExecutionLedger:
    """SQLite reservation ledger; not a remote QPU submission protocol."""
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS requests (actor TEXT NOT NULL, request_id TEXT NOT NULL, target_id TEXT NOT NULL, status TEXT NOT NULL, PRIMARY KEY(actor, request_id))')

    def _connect(self):
        return sqlite3.connect(self.path, timeout=5, isolation_level=None)

    def reserve(self, req: ExecutionRequest) -> bool:
        with self._connect() as db:
            try:
                db.execute('BEGIN IMMEDIATE')
                db.execute('INSERT INTO requests (actor, request_id, target_id, status) VALUES (?,?,?,?)', (req.actor, req.request_id, req.target_id, 'RESERVED'))
                db.execute('COMMIT')
                return True
            except sqlite3.IntegrityError:
                db.execute('ROLLBACK')
                return False

    def status(self, req: ExecutionRequest):
        with self._connect() as db:
            row = db.execute('SELECT status FROM requests WHERE actor=? AND request_id=?', (req.actor, req.request_id)).fetchone()
            return row[0] if row else None

    def set_status(self, req: ExecutionRequest, status: str):
        if status not in {'COMPLETED_LOCAL','FAILED_LOCAL_NEEDS_REVIEW'}:
            raise ValueError('Unsupported final status')
        with self._connect() as db:
            updated = db.execute('UPDATE requests SET status=? WHERE actor=? AND request_id=? AND status=?', (status, req.actor, req.request_id, 'RESERVED'))
            if updated.rowcount != 1:
                raise RuntimeError('Cannot transition request: not reserved')

def preflight(req: ExecutionRequest, facts: CircuitFacts, policy: Policy, ledger: ExecutionLedger) -> Decision:
    reasons: list[str] = []
    if not req.actor.strip() or not req.request_id.strip():
        reasons.append('IDENTITY_REQUIRED')
    if type(req.shots) is not int or not 1 <= req.shots <= policy.max_shots:
        reasons.append('SHOT_LIMIT')
    if type(facts.qubits) is not int or not 1 <= facts.qubits <= policy.max_qubits:
        reasons.append('QUBIT_LIMIT')
    if type(facts.depth) is not int or not 0 <= facts.depth <= policy.max_depth:
        reasons.append('DEPTH_LIMIT')
    kind = policy.backends.get(req.target_id)
    if kind not in {'local','remote'}:
        reasons.append('TARGET_NOT_ALLOWLISTED')
    if kind == 'remote':
        if not policy.allow_remote:
            reasons.append('REMOTE_DISABLED')
        if (req.actor,req.request_id,req.target_id) not in policy.remote_approvals:
            reasons.append('REMOTE_APPROVAL_REQUIRED')
    if reasons:
        return Decision('DENY',tuple(reasons))
    if not ledger.reserve(req):
        return Decision('DENY',('DUPLICATE_OR_UNRESOLVED_REQUEST',))
    return Decision('ALLOW',('PREFLIGHT_RESERVED_ONLY',),True)
