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

@pytest.mark.parametrize('value', [float('nan'), float('inf'), True, False, 2.0, '2', None])
@pytest.mark.parametrize('field,reason', [('shots','SHOT_LIMIT'), ('qubits','QUBIT_LIMIT'), ('depth','DEPTH_LIMIT')])
def test_non_integer_resource_is_denied_without_reservation(p, ledger, value, field, reason):
    request = req(shots=value) if field == 'shots' else req()
    facts = CircuitFacts(value if field == 'qubits' else 2, value if field == 'depth' else 2)
    result = preflight(request, facts, p, ledger)
    assert result.verdict == 'DENY' and reason in result.reasons
    assert not result.reserved and ledger.status(request) is None
    # Rejecting malformed input must not consume the idempotency key.
    assert preflight(req(), CircuitFacts(2, 2), p, ledger).verdict == 'ALLOW'

@pytest.mark.parametrize('name', ['max_shots', 'max_qubits', 'max_depth'])
@pytest.mark.parametrize('value', [float('nan'), float('inf'), True, False, 2.0, '2', None, -1])
def test_policy_rejects_invalid_resource_limits(name, value):
    with pytest.raises(ValueError, match=name):
        Policy(backends={'local-sim':'local'}, **{name: value})

@pytest.mark.parametrize('name', ['max_shots', 'max_qubits'])
def test_policy_requires_positive_shot_and_qubit_limits(name):
    with pytest.raises(ValueError, match=name):
        Policy(backends={'local-sim':'local'}, **{name: 0})

def test_inclusive_resource_limits_and_zero_depth(ledger):
    policy = Policy(backends={'local-sim':'local'}, max_shots=1, max_qubits=1, max_depth=0)
    assert preflight(req(shots=1), CircuitFacts(1, 0), policy, ledger).verdict == 'ALLOW'
