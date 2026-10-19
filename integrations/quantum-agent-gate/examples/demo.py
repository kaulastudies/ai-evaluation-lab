"""Offline deterministic preflight sample (no Qiskit required)."""
from pathlib import Path
from tempfile import TemporaryDirectory
from qag import Policy,ExecutionRequest,CircuitFacts,ExecutionLedger,preflight,make_lab_record,verify_record_hash

with TemporaryDirectory() as tmp:
    ledger=ExecutionLedger(Path(tmp)/'requests.sqlite')
    policy=Policy(backends={'local-statevector':'local','ibm-qpu':'remote'})
    facts=CircuitFacts(2,2)
    cases=[ExecutionRequest('agent','first','local-statevector',512),
           ExecutionRequest('agent','first','local-statevector',512),
           ExecutionRequest('agent','remote','ibm-qpu',512),
           ExecutionRequest('agent','too-many-shots','local-statevector',2048)]
    for idx,req in enumerate(cases):
        decision=preflight(req,facts,policy,ledger)
        record=make_lab_record(req,facts,decision,evaluation_id=f'QAG-demo-{idx}')
        assert verify_record_hash(record)
        print(req.request_id,decision.verdict,decision.reasons)
