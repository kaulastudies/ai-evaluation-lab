from concurrent.futures import ThreadPoolExecutor
import pytest
from qag import Policy,ExecutionRequest,CircuitFacts,ExecutionLedger,preflight

@pytest.fixture
def p():
    return Policy(backends={'local-sim':'local','qpu-1':'remote'})

@pytest.fixture
def ledger(tmp_path):
    return ExecutionLedger(tmp_path/'ledger.sqlite')

def req(name='r1',target='local-sim',shots=512):
    return ExecutionRequest('agent',name,target,shots)

def test_safe_local_reserved(p,ledger):
    r=preflight(req(),CircuitFacts(2,2),p,ledger)
    assert r.verdict=='ALLOW' and r.reserved

def test_duplicate_is_denied(p,ledger):
    assert preflight(req(),CircuitFacts(2,2),p,ledger).verdict=='ALLOW'
    assert preflight(req(),CircuitFacts(2,2),p,ledger).reasons==('DUPLICATE_OR_UNRESOLVED_REQUEST',)

def test_shots(p,ledger):
    assert 'SHOT_LIMIT' in preflight(req(shots=1025),CircuitFacts(2,2),p,ledger).reasons

@pytest.mark.parametrize('facts,reason',[(CircuitFacts(9,2),'QUBIT_LIMIT'),(CircuitFacts(2,81),'DEPTH_LIMIT'),(CircuitFacts(0,2),'QUBIT_LIMIT'),(CircuitFacts(2,-1),'DEPTH_LIMIT')])
def test_circuit_bounds(p,ledger,facts,reason):
    assert reason in preflight(req(),facts,p,ledger).reasons

def test_remote_denied(p,ledger):
    r=preflight(req(target='qpu-1'),CircuitFacts(2,2),p,ledger)
    assert r.verdict=='DENY' and {'REMOTE_DISABLED','REMOTE_APPROVAL_REQUIRED'} <= set(r.reasons)

def test_unknown_target(p,ledger):
    assert 'TARGET_NOT_ALLOWLISTED' in preflight(req(target='unknown'),CircuitFacts(2,2),p,ledger).reasons

def test_exact_remote_approval(ledger):
    p=Policy(backends={'qpu-1':'remote'},allow_remote=True,remote_approvals=frozenset({('agent','r1','qpu-1')}))
    assert preflight(req(target='qpu-1'),CircuitFacts(2,2),p,ledger).verdict=='ALLOW'
    assert 'REMOTE_APPROVAL_REQUIRED' in preflight(req('r2','qpu-1'),CircuitFacts(2,2),p,ledger).reasons

def test_missing_identity(p,ledger):
    assert 'IDENTITY_REQUIRED' in preflight(ExecutionRequest(' ','','local-sim',100),CircuitFacts(2,2),p,ledger).reasons

def test_concurrent_reservation(p,ledger):
    with ThreadPoolExecutor(max_workers=6) as executor:
        verdicts=list(executor.map(lambda _:preflight(req('parallel'),CircuitFacts(2,2),p,ledger).verdict,range(6)))
    assert verdicts.count('ALLOW')==1 and verdicts.count('DENY')==5

def test_local_completion_and_no_replay(p,ledger):
    r=req('finish')
    assert preflight(r,CircuitFacts(2,2),p,ledger).verdict=='ALLOW'
    assert ledger.status(r)=='RESERVED'
    ledger.set_status(r,'COMPLETED_LOCAL')
    assert ledger.status(r)=='COMPLETED_LOCAL'
    assert preflight(r,CircuitFacts(2,2),p,ledger).verdict=='DENY'
    with pytest.raises(RuntimeError):
        ledger.set_status(r,'COMPLETED_LOCAL')

def test_failed_job_needs_reconciliation(p,ledger):
    r=req('failed')
    assert preflight(r,CircuitFacts(2,2),p,ledger).verdict=='ALLOW'
    ledger.set_status(r,'FAILED_LOCAL_NEEDS_REVIEW')
    assert preflight(r,CircuitFacts(2,2),p,ledger).verdict=='DENY'

def test_unknown_cannot_transition(p,ledger):
    with pytest.raises(RuntimeError):
        ledger.set_status(req('missing'),'COMPLETED_LOCAL')
