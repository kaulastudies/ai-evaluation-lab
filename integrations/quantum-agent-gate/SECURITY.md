# Security boundaries and scope

This project is an experiment, not a production security boundary. It verifies requests only when a trusted host controls backend identities, approvals and access to every execution route. Agents with direct runtime credentials, arbitrary Python, or alternative QPU APIs can bypass it. SQLite reservation does not provide distributed job idempotence or provider billing guarantees.

The guarded Qiskit adapter has NO real-QPU or cloud execution route. A reserved request is not evidence of completed execution; users must distinguish reservation and completion. Do not deploy this to protect paid quantum workloads. No backend credentials are necessary or supported.
