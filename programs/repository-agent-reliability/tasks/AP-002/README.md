# AP-002 — Workspace authorization boundary

AP-002 is the second synthetic RARB task and targets authorization-boundary leakage.
Roles are workspace-scoped. The vulnerable implementation incorrectly treats privileged
roles as global, allowing a foreign-workspace editor or admin to update a document.

Public tests cover ordinary same-workspace behavior. The qualified verifier adds
cross-workspace privileged-role and owner-identifier-collision checks. The verifier
must qualify against a reference implementation, known-bad implementation, and three
critical mutations before it is trusted to score candidates.
