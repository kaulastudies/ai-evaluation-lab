# Quantum Agent Gate (QAG)

**Experimental local-only Qiskit 2.x integration for testing the execution decisions of quantum-programming agents.** A research component of [AI Evaluation Lab](https://github.com/kaulastudies/ai-evaluation-lab). Independent of IBM and Qiskit; not endorsed or accepted by the Qiskit Ecosystem at submission time.

Agents can create mathematically valid quantum circuits yet request unauthorized backends, excess shots, or duplicate jobs. QAG turns these requests into testable safety contracts. Unlike quantum correctness benchmarks, QAG checks the **decision to execute**. The current SDK adapter reads actual Qiskit QuantumCircuit facts, enforces trusted backend and resource policy, reserves request IDs atomically in SQLite, then calls the **real Qiskit V2 StatevectorSampler locally**. Hardware/QPU execution is deliberately absent.

## Install and reproduce (Python 3.10+)

Run from this directory:

    python -m pip install -e '.[qiskit,test]'
    python -m pytest -q
    python -m examples.qiskit_guarded_demo

For no-SDK offline policy checks use pip install -e '.[test]' and pytest; five SDK integration tests will be explicitly skipped. The [.github/workflows/qag-qiskit.yml](../../.github/workflows/qag-qiskit.yml) GitHub Actions workflow installs Qiskit SDK 2.x and exercises them.

## Example API

    from qiskit import QuantumCircuit
    from qag import Policy, ExecutionRequest, ExecutionLedger
    from qag.qiskit_bridge import guarded_local_counts

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    policy = Policy(backends={'local-statevector': 'local'}, max_shots=1024)
    request = ExecutionRequest('agent-1', 'bell-001', 'local-statevector', 256)
    ledger = ExecutionLedger('local-requests.sqlite')
    decision, counts = guarded_local_counts(qc, request, policy, ledger)
    print(decision.verdict, counts, ledger.status(request))

The SQLite database is local working state; do not commit it. Run agents only through a trusted host adapter that denies direct simulator/backend access.

## Controls and verification

| Control | Expected result |
|---|---|
| Bell-state circuit, authorized local target | ALLOW, actual sampler counts, COMPLETED_LOCAL |
| Excessive shots, qubits or depth | DENY before execution |
| Physical backend, even with approval | DENY by local-only adapter |
| Duplicate actor/request ID | DENY; never automatically retry |
| Circuit without measurement | DENY before reservation |
| Unknown backend | DENY |

See [QAG-001 task contract](research/QAG-001.md), [SUPPORT.md](SUPPORT.md), [SECURITY.md](SECURITY.md), and [CONTRIBUTING.md](CONTRIBUTING.md).

## AI Evaluation Lab integration

The qag.evidence adapter exports SHA-256 hashed records using fields from the Lab public evaluation-record schema, with task IDs and explicit verifier decisions. Compatibility with the main Lab canonical hash implementation has not yet been verified. No agent-model evaluations or real-QPU executions are claimed.

## Status and eligibility

MIT-licensed (see LICENSE), follows Qiskit's Code of Conduct, targets Qiskit SDK 2.x and V2 StatevectorSampler, with best-effort experimental support. CI must pass before submitting to the official ecosystem form. This package is not a production security system and has no paid-hardware execution path.
