"""Real Qiskit 2.x circuit inspection and guarded V2 local simulation only."""
from .gate import CircuitFacts, Decision, ExecutionRequest, Policy, ExecutionLedger, preflight

def inspect_circuit(circuit):
    try:
        import qiskit
        from qiskit import QuantumCircuit
    except ImportError as exc:
        raise RuntimeError('Install qiskit>=2,<3') from exc
    if int(qiskit.__version__.split('.')[0]) != 2:
        raise RuntimeError('Unsupported Qiskit SDK version: '+qiskit.__version__)
    if not isinstance(circuit,QuantumCircuit):
        raise TypeError('A real Qiskit QuantumCircuit is required')
    return CircuitFacts(circuit.num_qubits,circuit.depth())

def preflight_qiskit(circuit,req:ExecutionRequest,policy:Policy,ledger:ExecutionLedger):
    return preflight(req,inspect_circuit(circuit),policy,ledger)

def guarded_local_counts(circuit,req:ExecutionRequest,policy:Policy,ledger:ExecutionLedger,*,seed:int=42):
    """Return (Decision, counts_or_None); never invokes any external QPU."""
    if policy.backends.get(req.target_id) != 'local':
        return Decision('DENY',('LOCAL_EXECUTION_ONLY',)),None
    facts=inspect_circuit(circuit)
    if len(circuit.cregs)!=1 or circuit.count_ops().get('measure',0)==0:
        return Decision('DENY',('ONE_MEASURED_REGISTER_REQUIRED',)),None
    decision=preflight(req,facts,policy,ledger)
    if decision.verdict!='ALLOW':
        return decision,None
    try:
        from qiskit.primitives import StatevectorSampler
        sampler=StatevectorSampler(default_shots=req.shots,seed=seed)
        result=sampler.run([circuit]).result()[0]
        counts=getattr(result.data,circuit.cregs[0].name).get_counts()
        ledger.set_status(req,'COMPLETED_LOCAL')
        return decision,counts
    except Exception:
        ledger.set_status(req,'FAILED_LOCAL_NEEDS_REVIEW')
        raise

def local_bell_counts(shots=512,seed=42):
    """Direct local primitive demonstration, not an agent submission entry point."""
    if not 1 <= shots <= 1024:
        raise ValueError('shots must be 1..1024')
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorSampler
    circuit=QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0,1)
    circuit.measure_all()
    return StatevectorSampler(default_shots=shots,seed=seed).run([circuit]).result()[0].data.meas.get_counts()
