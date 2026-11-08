# ReceiptOps demo recording script

Target duration: about 2 minutes 30 seconds. Record the actual deployed app.
Do not substitute a synthetic receipt or staged success screenshot.

| Time | Screen and action | Narration |
| --- | --- | --- |
| 0:00-0:15 | Workbench with ready services | I'm Rama Chandra M from AI Evaluation Lab. ReceiptOps audits an invoice ledger and gives the reviewer a record they can check after the run. |
| 0:15-0:35 | Fictional ledger, then Run audit | The model receives the calculation contract and schema. It writes a Python program, while the invoice rows stay outside the prompt. |
| 0:35-0:55 | Actual generated code and execution result | The program runs in a fresh container on Vultr. A separate checker recomputes every result field from the input. Here we can inspect the program and the observed result. |
| 0:55-1:25 | Containment panel, run probes | This is the containment check. The probe tries to reach the network and write outside its permitted temporary storage. It also checks the user, key exposure, timeout and cleanup. The displayed outcomes come from this run. |
| 1:25-1:45 | Receipt inspector, verify, tamper, verify | The receipt binds the input, program and output hashes under the host's signing key. Changing the record makes signature verification fail. |
| 1:45-2:10 | Terminal running offline verifier on the real downloaded bundle | The offline verifier needs no model call and never runs the downloaded program. It checks the signature using a separately trusted key and recomputes the invoice answer. A signed wrong answer still fails. |
| 2:10-2:30 | Return to the app with source link | The public prototype accepts only fictional data. Docker shares the host kernel, and the signature relies on a trusted signing host. The next step is a private pilot with authentication, TLS and stronger tenant isolation. |

Keep the output visible long enough to read. If a probe or audit fails, show the
failure and fix it before recording a completed demonstration. Crop account
credentials and infrastructure control panels out of the final recording.
