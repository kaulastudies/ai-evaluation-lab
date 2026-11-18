"""Real Qiskit 2.x circuit inspection and guarded V2 local simulation only."""
import json
import multiprocessing

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
    # Accept an explicit finite primitive basis. Composite/custom definitions are
    # denied rather than recursively expanded (including cycles/shared DAGs).
    from qiskit.circuit import Measure, Barrier, Reset
    from qiskit.circuit.library import HGate, XGate, YGate, ZGate, SGate, SdgGate, TGate, TdgGate, CXGate, CZGate, RXGate, RYGate, RZGate
    classes = (HGate, XGate, YGate, ZGate, SGate, SdgGate, TGate, TdgGate, CXGate, CZGate, Measure, Reset)
    allowed = set(classes) | {type(cls()) for cls in classes} | {Barrier, RXGate, RYGate, RZGate}
    if len(circuit.data) > 2048:
        raise ValueError("Circuit exceeds operation budget")
    for instruction in circuit.data:
        if type(instruction.operation) not in allowed:
            raise ValueError("Composite/custom operations require decomposition into the approved primitive basis")
    return CircuitFacts(circuit.num_qubits,circuit.depth())

def preflight_qiskit(circuit,req:ExecutionRequest,policy:Policy,ledger:ExecutionLedger):
    return preflight(req,inspect_circuit(circuit),policy,ledger)

def _simulate(connection, circuit, shots, seed):
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3,) * 2)
        inspect_circuit(circuit)  # Validate the same private snapshot that runs.
        from qiskit.primitives import StatevectorSampler
        result = StatevectorSampler(default_shots=shots, seed=seed).run([circuit]).result()[0]
        counts = getattr(result.data, circuit.cregs[0].name).get_counts()
        connection.send_bytes(json.dumps({"counts": counts}).encode())
    except Exception as exc:
        connection.send_bytes(json.dumps({"error": type(exc).__name__}).encode())
    finally:
        connection.close()


def guarded_local_counts(circuit,req:ExecutionRequest,policy:Policy,ledger:ExecutionLedger,*,seed:int=42):
    """Bounded local simulation; composites must first be explicitly decomposed."""
    if policy.backends.get(req.target_id) != 'local':
        return Decision('DENY',('LOCAL_EXECUTION_ONLY',)),None
    try:
        inspect_circuit(circuit)
        snapshot = circuit.copy()
        facts = inspect_circuit(snapshot)
    except (ValueError, RecursionError):
        return Decision('DENY',('CIRCUIT_WORK_LIMIT',)),None
    if len(snapshot.cregs)!=1 or snapshot.count_ops().get('measure',0)==0:
        return Decision('DENY',('ONE_MEASURED_REGISTER_REQUIRED',)),None
    # A hard ceiling also bounds statevector memory if callers loosen Policy.
    if facts.qubits > 16 or req.shots > 4096:
        return Decision('DENY',('SIMULATOR_RESOURCE_LIMIT',)),None
    decision=preflight(req,facts,policy,ledger)
    if decision.verdict!='ALLOW':
        return decision,None
    context = multiprocessing.get_context('spawn')
    parent, child = context.Pipe(duplex=False)
    worker = context.Process(target=_simulate, args=(child, snapshot, req.shots, seed), daemon=True)
    try:
        worker.start()
        child.close()
        if not parent.poll(20):
            raise RuntimeError('Simulation wall-time budget exceeded')
        payload = json.loads(parent.recv_bytes(1024 * 1024))
        worker.join(2)
        if worker.is_alive() or worker.exitcode != 0 or 'error' in payload:
            raise RuntimeError('Simulation failed within resource boundary')
        ledger.set_status(req,'COMPLETED_LOCAL')
        return decision,payload['counts']
    except Exception:
        ledger.set_status(req,'FAILED_LOCAL_NEEDS_REVIEW')
        raise
    finally:
        if worker.pid and worker.is_alive():
            worker.kill()
            worker.join(2)
        parent.close()
        child.close()


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
