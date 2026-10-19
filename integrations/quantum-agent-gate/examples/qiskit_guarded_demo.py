"""Live Qiskit local simulator demonstration. No IBM credentials or hardware."""
from pathlib import Path
from tempfile import TemporaryDirectory
from qiskit import QuantumCircuit
from qag import Policy,ExecutionRequest,ExecutionLedger
from qag.qiskit_bridge import guarded_local_counts

qc=QuantumCircuit(2)
qc.h(0)
qc.cx(0,1)
qc.measure_all()
with TemporaryDirectory() as tmp:
    ledger=ExecutionLedger(Path(tmp)/'requests.sqlite')
    policy=Policy(backends={'local-statevector':'local','ibm-physical':'remote'})
    req=ExecutionRequest('agent-demo','bell-001','local-statevector',256)
    decision,counts=guarded_local_counts(qc,req,policy,ledger)
    print({'verdict':decision.verdict,'counts':counts,'status':ledger.status(req)})
    again,_=guarded_local_counts(qc,req,policy,ledger)
    print({'replay':again.verdict,'reasons':again.reasons})
