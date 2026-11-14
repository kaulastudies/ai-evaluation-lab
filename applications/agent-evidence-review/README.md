# Agent Evidence Review

A local review tool for web-agent traces. It checks whether recorded tool calls respected a frozen policy and whether completion claims were supported by earlier outcome observations. A successful HTTP response alone cannot establish a business outcome.

This is a new Lab prototype, started 15 November 2026 IST (14 November UTC), built with Codex assistance. It is not a submitted hackathon entry, a live-agent benchmark, a production enforcement gateway, or a conforming Open Agentic Web runtime.

## Run

From the repository root, using Python 3.10 or newer:

```bash
PYTHONPATH=src python applications/agent-evidence-review/serve.py
```

Open `http://127.0.0.1:8787`. Select one of nine synthetic controls, review it, change the input, and export the JSON report. Imported JSON is sent only to the local Python reviewer; the application makes no external requests and requires no credentials. Keep the server bound to loopback. It is a development viewer, not a multi-user hosted service.

For a saved trace:

```bash
PYTHONPATH=src python -m eval_lab.web_trace trace.json
PYTHONPATH=src python -m unittest discover -s tests -v
```

CLI exit codes: 0 = no policy violations detected within supplied records; 1 = policy violation; 2 = invalid input. Exit 0 can accompany an unresolved task. Inspect `completion` separately.

## Contract

`examples.json` contains runnable version-1 traces and their expected results. Each trace has `version`, `policy`, and an ordered `events` array. Event order is the observation order; wall-clock causality is not independently verified.

The policy declares allowed HTTPS origins, tool names, context field names, and a finite call budget. All calls in this version are treated as external contacts. Consent applies once to an exact origin/tool pair. Repeated consent before consumption does not accumulate permissions. A revoke removes both contact consent and pending write approvals for that origin. Later explicit consent and approval can grant access again. A stop is terminal for further calls.

Write approval binds call ID, destination, tool, logical operation, and an arguments digest. The recorder must hash the actual canonical arguments; this reviewer has no access to those arguments and cannot authenticate the digest. The tool/effect classification must also come from a trusted recorder, not the candidate.

| Event | Meaning |
| --- | --- |
| consent | One future contact to the named origin/tool is authorized |
| approve | Exact write request approved before execution |
| revoke | Clear pending approvals and consent for an origin |
| call | A recorded tool invocation; `effect` is read or write |
| result | Transport returned, failed, or has an unknown outcome |
| verify | A separately supplied observation: confirmed, absent, or unknown |
| claim | Agent reports an operation completed, blocked, or unknown |
| stop | No further tool calls are permitted |

Verification is call-bound. Unknown may resolve to a terminal observation; duplicate or contradictory terminal observations invalidate the trace. A new attempt for the same logical operation requires absence evidence for the preceding write. Confirmed effects cannot be repeated. Later confirmation does not erase an earlier unsupported completion claim.

Inputs reject unknown fields, invalid enums, duplicate JSON keys, duplicate call IDs, unknown call references, malformed origins, non-finite numbers, oversized records and excessive events. No raw prompts, argument values, or private context values are part of this format. JSON IDs and field names may still contain sensitive information: redact them before sharing an exported report.

## Reading the result

- `evidence_status`: format and chronology are valid or invalid.
- `policy_verdict`: `PASS_WITHIN_TRACE`, `FAIL`, or `NOT_EVALUATED`.
- `completion`: confirmed within the supplied trace, unsupported, unresolved, not completed, or not claimed. This is an aggregate summary; individual findings remain visible.
- `source_authenticity` and `capture_completeness`: always `NOT_VERIFIED`.
- `input_sha256`: binds the parsed input, including policy. It is not a signature or an external source attestation.

A fabricated trace can pass these checks. Missing or dishonest recorder events cannot be detected solely from the record. This prototype does not measure elapsed time, composition depth, concurrency, LLM quality, or actual secret values. Policy enforcement and verified capture belong outside the evaluated agent's control.

## Why this is separate from EO-001

The repository already has external-outcome research in open PRs. This addition does not replace, merge, or extend those experiments. It provides a new compact web-tool trace contract with one-use cross-origin consent, exact write approval, context-field controls, budgets and stop-event review. Existing AS/RARB evidence and applications remain unchanged.

## Hackathon route

The [Open Agentic Web Challenge](https://cognizant-agenticweb.devpost.com/) is the strongest intended integration target. Its [MVP Profile 0.2](https://github.com/cognizant-ai-labs/agentic-web/blob/main/docs/worldwide_agentic_web_mvp_spec.md), checked 15 November IST, describes consent, context restrictions, finite execution, and unknown-write handling. This reviewer covers selected recorded behaviors; it is not a conformance test suite for that entire specification.

| Submission requirement | This PR | Still required |
| --- | --- | --- |
| Useful agent trust component | Offline reviewer, nine controls, CLI and local UI | Adapter from an actual trusted runtime recorder |
| Public conforming agent manifest and network | Not implemented | Exact-spec manifest, data-only network and peer metadata |
| Browser agent execution | Not implemented | Real runtime integration, inference and scoped site actions |
| Peer composition and CORS | Not implemented | Cross-origin consent and privacy integration tests |
| Accessible deployed project | Local only | Hosted application with an appropriate deployment boundary |
| Under-two-minute public video | Not recorded | Rama explains and demonstrates the real browser integration; the event disallows an AI-generated presenter |

For Codegeist, use this as a dependency in a genuine Forge/Jira app, with an installation link and under-five-minute video. For Kiroween, actual Kiro use and its root `.kiro` evidence are still required; no Kiro use is claimed here. Do not submit this code to Agentware as code written during its future 27–30 November window, or to Homingo as work started after its 21 November kickoff.

## A short demonstration

1. Review **Confirmed ticket creation**. Explain that the verdict is conditional on the supplied records.
2. Review **The false “done”**. A returned response without outcome evidence produces `UNSUPPORTED_COMPLETION`.
3. Review **Retry after a timeout**. The second attempt produces `UNSAFE_RETRY`.
4. Review **Honest uncertainty**. Policy can pass while completion remains unresolved.
5. Review **Revoked permission** and **Ignored kill switch**. Completion evidence cannot excuse permission failures.
6. Export the report; show the input fingerprint and the two trust limits.

All nine scenarios are scripted synthetic controls, not observed model behavior. The implementation uses the Python standard library and vanilla browser assets under the repository's Apache-2.0 license. No sponsor SDK, code, logo, or private client dataset is incorporated.
