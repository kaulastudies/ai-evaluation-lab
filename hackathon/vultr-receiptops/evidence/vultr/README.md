# Live Vultr evidence — 9 November 2026

These are downloaded observations from the dedicated ReceiptOps Vultr VM,
not unit-test fixtures. The invoice rows are fictional public demonstration data.

| Evidence | Observation |
| --- | --- |
| `audit.json` | Vultr Qwen 3.8 Flash Next program; checker passes on attempt 1; container removed |
| `browser-audit.json` | A second successful audit initiated from the public workbench |
| `containment.json` | All eight configured-control probes pass; signature verified outside VM |
| `offline-verification.json` | Downloaded audit passes signature, bound-artifact and result checks |
| `receiptops-public-key.txt` | Public verification key, separately published here for pinning |
| `status.json` | Deployment readiness and policy; readiness alone is not execution evidence |

Key fingerprint: `7a64d821c16d86f0`.

```bash
python verify_bundle.py evidence/vultr/audit.json \
  --public-key evidence/vultr/receiptops-public-key.txt
```

The trusted host signs its observations. A signature is not hardware attestation
or independent proof that the host is honest. Docker shares the host kernel.
The HTTP demo accepts the built-in fictional sample only. Private use requires
TLS, authentication and additional tenant and data controls.

Initial live requests failed because a completion was not valid JSON. The
provider integration was corrected before these successful audit observations.
The public UI's containment button was also corrected to use POST. Failed
attempts remain counted in the deployed database's usage budget.

The hackathon entry has not been submitted; the event's submission window is closed.
