"""Real Qiskit 2.x V2 integration; CI installs the SDK."""
import importlib.util
import pytest
from qag import Policy,ExecutionRequest,ExecutionLedger
from qag.qiskit_bridge import inspect_circuit,guarded_local_counts,local_bell_counts

pytestmark=pytest.mark.skipif(importlib.util.find_spec('qiskit') is None,reason='Qiskit SDK not installed locally')

def bell():
    from qiskit import QuantumCircuit
    qc=QuantumCircuit(2)
    qc.h(0)
    qc.cx(0,1)
    qc.measure_all()
    return qc

def test_v2_sampler_bell():
    facts=inspect_circuit(bell())
    assert facts.qubits==2 and facts.depth>=2
    counts=local_bell_counts(512,seed=42)
    assert set(counts)<={'00','11'} and sum(counts.values())==512

def test_guarded_sampler_and_duplicate(tmp_path):
    ledger=ExecutionLedger(tmp_path/'ledger.sqlite')
    policy=Policy(backends={'local-statevector':'local','ibm-physical':'remote'})
    req=ExecutionRequest('agent','bell-001','local-statevector',128)
    decision,counts=guarded_local_counts(bell(),req,policy,ledger)
    assert decision.verdict=='ALLOW' and sum(counts.values())==128
    assert set(counts)<={'00','11'} and ledger.status(req)=='COMPLETED_LOCAL'
    duplicate,counts2=guarded_local_counts(bell(),req,policy,ledger)
    assert duplicate.verdict=='DENY' and counts2 is None

def test_remote_never_runs_even_with_approval(tmp_path):
    ledger=ExecutionLedger(tmp_path/'ledger.sqlite')
    req=ExecutionRequest('agent','hw','ibm-physical',128)
    policy=Policy(backends={'ibm-physical':'remote'},allow_remote=True,remote_approvals=frozenset({('agent','hw','ibm-physical')}))
    decision,counts=guarded_local_counts(bell(),req,policy,ledger)
    assert decision.reasons==('LOCAL_EXECUTION_ONLY',) and counts is None
    assert ledger.status(req) is None

def test_unmeasured_rejected(tmp_path):
    from qiskit import QuantumCircuit
    qc=QuantumCircuit(2)
    qc.h(0)
    ledger=ExecutionLedger(tmp_path/'ledger.sqlite')
    req=ExecutionRequest('agent','bad','local-statevector',128)
    decision,counts=guarded_local_counts(qc,req,Policy(backends={'local-statevector':'local'}),ledger)
    assert decision.reasons==('ONE_MEASURED_REGISTER_REQUIRED',) and counts is None
    assert ledger.status(req) is None

def test_shot_overrun_rejected_before_sampler(tmp_path):
    ledger=ExecutionLedger(tmp_path/'ledger.sqlite')
    req=ExecutionRequest('agent','over','local-statevector',2048)
    decision,counts=guarded_local_counts(bell(),req,Policy(backends={'local-statevector':'local'}),ledger)
    assert decision.verdict=='DENY' and 'SHOT_LIMIT' in decision.reasons and counts is None
    assert ledger.status(req) is None

def test_nested_and_repeated_composite_definitions_denied(tmp_path):
    from qiskit import QuantumCircuit
    definition = QuantumCircuit(1)
    definition.x(0)
    for _ in range(8):
        wrapper = QuantumCircuit(1)
        gate = definition.to_gate()
        wrapper.append(gate, [0])
        wrapper.append(gate, [0])
        definition = wrapper
    circuit = QuantumCircuit(1)
    circuit.append(definition.to_gate(), [0])
    circuit.measure_all()
    ledger = ExecutionLedger(tmp_path / 'nested.sqlite')
    req = ExecutionRequest('agent', 'nested', 'local', 128)
    decision, counts = guarded_local_counts(circuit, req, Policy(backends={'local': 'local'}), ledger)
    assert decision.reasons == ('CIRCUIT_WORK_LIMIT',) and counts is None
    assert ledger.status(req) is None

def test_instruction_budget_enforced():
    from qiskit import QuantumCircuit
    circuit = QuantumCircuit(1)
    for _ in range(2049):
        circuit.x(0)
    with pytest.raises(ValueError, match='operation budget'):
        inspect_circuit(circuit)
