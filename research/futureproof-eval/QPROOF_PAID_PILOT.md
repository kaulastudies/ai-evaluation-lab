# QProof Audit — quantum results verification pilot

**By AI Evaluation Lab | Experimental v0.1**

## What a customer buys

A fixed-scope independent review of **up to 10 small, analytically tractable quantum circuits** with measurement-count results. Deliverables: machine-readable report, reproducible local CLI workflow, flagged anomalies, evidence hashes and a 30-minute findings call.

**Launch pilot price: USD $299** (or INR equivalent at invoice date). 50% upfront, 50% on delivery. Target delivery within **5 business days after receiving complete, non-sensitive inputs**. Human review included. Payment by a mutually agreed supported invoice/payment method; no checkout is active.

### Input format

`{"cases":[{"id":"zero","theta_radians":0,"ones":0,"shots":100}]}`

Run: `python -m research.futureproof_eval.qproof_audit example.json --output report.json`

Accept only consented, non-sensitive inputs. No API key, proprietary circuit, access token, or confidential customer material in public GitHub issues. Request a private transfer channel if necessary.

### What the report establishes

A shot-aware **screening flag** comparing observed binary measurement fractions with a Born-rule reference for a single-qubit Ry preparation and Z-basis measurement, plus source-input hash for reproducibility. Results do **not** certify hardware, fault tolerance, quantum advantage, or statistically controlled family-wise error across circuits.

### Acceptance and boundaries

The initial package supports only single-qubit `Ry(theta)` circuits with binary measurement counts in the computational basis; this is **not** a general quantum program verifier. Customers can reproduce the same JSON report from identical input and tool version. Failed or anomalous runs are reported without replacing customer data.

Custom circuits, hardware backend integrations, simulator execution, and comparative performance studies are quoted separately and require a written scope.

## How to order

Contact: ramachandra.health@gmail.com (verify delivery contact before publication) or reach the maintainer through repository contact options. We will confirm fit, written scope, privacy and payment before starting.

## Sales target

One paid pilot; do not claim a customer, order, or revenue until a signed scope/payment is actually received.
