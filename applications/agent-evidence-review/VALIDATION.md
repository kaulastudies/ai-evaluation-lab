# Validation — 15 November 2026 IST

Base: `c619f1335d3039eecdee0502f470b9f323fe84f4` on `main`.

| Check | Observed result |
| --- | --- |
| Original root test suite | 22 passed before edits |
| Root suite with new reviewer and local-server tests | 49 passed: 22 existing and 27 new |
| Scripted examples | All nine match expected policy and completion outcomes |
| Deliberate removal of consent, write-approval, private-context, stop and completion checks | All five mutations detected by failing assertions |
| CLI outcomes | Pass, failure and invalid-input exit codes exercised |
| Local HTTP server | Review response, hostile Origin/Host rejection, file allowlist, invalid-input recovery passed |
| JavaScript | `node --check` passed |
| Python | New code and RARB compilation passed |
| AS-001 contract, published Ollama/Groq evidence, AS-002 | Passed |
| Phase 12 evidence integrity | Passed |
| RARB deterministic replay/demo gate | Passed |
| Alpha demo | Six records generated successfully in temporary output |

Visual browser testing was attempted but could not run: the available Chromium failed before page load because the environment denied its process-singleton socket. No desktop/mobile rendering or browser interaction pass is claimed. The server and engine tests are separate from this limitation.

No live model, external tool provider, sponsor platform, hosted deployment, cross-origin runtime composition or hackathon submission was exercised. Test counts are engineered controls, not model reliability statistics.
