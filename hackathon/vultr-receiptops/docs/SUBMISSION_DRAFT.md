# ReceiptOps submission draft

This entry is not submitted. Live Vultr verification is complete. LabLab blocks
submission because the event has ended; the organizer has been asked to reopen it.

## Title

ReceiptOps: Verifiable Agent Execution

## Short description

ReceiptOps audits a fictional invoice ledger in disposable Vultr sandboxes, independently checks the result, and returns a signed evidence bundle that judges can verify offline.

## Long description

ReceiptOps helps a reviewer answer a practical question: what did an AI agent actually run, and can its result still be checked after the session ends?

The prototype uses a small fictional invoice ledger. Vultr Serverless Inference writes a Python program from an explicit task contract. The trusted controller runs that program in a disposable Docker container. A separate deterministic checker recomputes the totals, overdue balances and duplicate IDs from the original CSV. It allows one retry when the result is wrong.

The execution container has no network, a read-only root and input mount, a non-root user, dropped capabilities, memory and process limits, and an eight-second deadline. API keys and the Docker socket stay outside it. The containment panel runs observable probes for these controls and cleanup.

Each audit returns an Ed25519-signed receipt binding the input, program and output hashes to the recorded result. An offline verifier checks the signature against a separately trusted public key and independently recomputes the invoice answer. Tests reject tampered receipts, substituted inputs, untrusted signers and even a correctly signed but incorrect answer.

Both the frontend and controller run on a dedicated Vultr VM, with Vultr inference providing the generated program. The public demo accepts fictional sample data only. It does not approve or move money. Signatures authenticate the host's record; they are not hardware attestation. Docker shares the host kernel, so the prototype does not claim protection against every possible escape.

## Form choices

- Participation: Online
- Intended challenge: Blast Radius Zero
- Relevant technologies if present in the form: Vultr Cloud Compute, Vultr
  Serverless Inference, Python, Docker, FastAPI, artificial intelligence agents
- Author: Rama Chandra M, AI Evaluation Lab
- Public repository: https://github.com/kaulastudies/ai-evaluation-lab/tree/hackathon/receiptops-agent-rush/hackathon/vultr-receiptops
- Public demo: http://155.138.211.247
- Video: ReceiptOps_Demo.mp4 — edited walkthrough of actual verified product screens with synthetic narration
- PDF: ReceiptOps_Presentation_Draft.pdf — updated with live evidence

## Completion conditions

The live app must successfully generate and execute a program through Vultr,
pass the independent checker, complete its containment probes, and produce a
bundle accepted by the offline verifier. The video must show that actual run.
These execution checks passed on 9 November 2026. Submission still requires the organizer to reopen the form. A screenshot of setup screens,
a reference computation or a synthetic receipt is not live execution evidence.
