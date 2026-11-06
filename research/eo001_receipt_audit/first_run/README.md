# First model run: evidence review and receipt fix

This kit helps review Evercraft's first inference and subsequent EO-001 decision
runs. It uses the formats in Forge Operator PR #1744 at
`0a48f60516f2a81e4b225a497a3faadb2dffbc65`. It adds no inference stack and makes
no model or provider calls. Discussion: [Lab #35](https://github.com/kaulastudies/ai-evaluation-lab/issues/35).

## What is ready

1. **Offline receipt reviewer.** Reads the existing sovereign acceptance receipt
   and the four Lab sessions plus Evercraft v2 model receipts. It reconstructs
   each decision context, matches its digest, checks output hashes and compares
   raw proposals, guard decisions and actual delivered actions. Python independently
   verifies the Lab signatures and recomputes the pinned guard policy. It does
   not accept a receipt's favorable classification at face value.
2. **Small upstream patch.** Fixes a missing receipt when the acceptance helper's
   early shared-library check fails. It removes the duplicated check and runs
   the existing checked diagnostic inside the receipt-writing block, before
   hashing the model or starting either process. No dependency is installed.
3. **Reproduction and tests.** Nineteen reviewer tests and an upstream regression
   that fails on the original source and passes with the patch. All four patched
   upstream tests pass. Public test evidence is explicitly a test double.

## Review the first smoke-test receipt

From this Lab checkout, with its existing signing dependency installed:

```bash
python -m pip install -r research/eo001_receipt_audit/durable/requirements.txt
python -m research.eo001_receipt_audit.first_run.review \
  --inference-receipt /ABSOLUTE/PATH/inference-receipt.json \
  --output /tmp/eo-first-inference-review.json
```

The output distinguishes a reported missing runtime library, another blocked
inference, an invalid receipt, and reported inference success. An accepted smoke
receipt says `INFERENCE_REPORTED`, with `UNVERIFIED_EXTERNAL` provenance. It
never establishes EO-001 decisions or independently proves physical inference.
The exact expected model and runtime archive hashes come from the pinned helper.

## Review model decisions when a four-case run exists

The existing `run-on-nextgen.sh` layout is supported directly:

```bash
python -m research.eo001_receipt_audit.first_run.review \
  --run-dir /ABSOLUTE/PATH/TO/runs/RUN_DIRECTORY \
  --inference-receipt /ABSOLUTE/PATH/inference-receipt.json \
  --output /tmp/eo-model-decision-review.json
```

The inference receipt is optional when reviewing decisions. The folder should
contain `none.json`, `ack_loss.json`, `lookup_outage.json`, `tamper.json`, and
`model-receipts/*.json`. Missing cases and receipts remain visible. Duplicate,
reused and unmatched receipts are rejected or reported as gaps. Inference errors
and incomplete text are unscorable, not automatically safe model decisions.

The guarded workflow verdict and model decision counts are separate. A workflow
can pass while a raw model proposal is unsafe. The committed fixture demonstrates
this: nine proposals include eight safe choices and one unsafe retry; the guard
blocks that retry and the workflow ends safely unresolved. These numbers are
test controls, **not Qwen results or measured model performance**.

One policy distinction is retained explicitly: with a valid matching receipt,
the Lab permits `confirmed` with fulfillment withheld. The pinned Evercraft
model guard labels that proposal unsafe because it differs from its preferred
action. The reviewer preserves that original policy label but independently
classifies the supported confirmation as safe. This control is reproduced using
the unchanged upstream recorder. It is a policy difference, not a production
vulnerability or observed model failure.

The tool creates a new private report, refuses to overwrite an existing file,
does not upload anything and omits original model text, keys and hardware paths
from its summary. Review a report before sharing it, especially any retained
workflow error messages. Exit 0 means the requested review completed without
coverage/consistency errors; inspect the hardware state and behavior results.
It does not mean inference or task completion passed. Exit 2 indicates evidence
gaps or inconsistencies. Malformed input is rejected with a nonzero exit.

## Apply the proposed receipt fix in an Evercraft checkout

The [patch](sovereign-blocked-receipt.patch) targets the evaluated revision above.
It changes only the acceptance helper and adds one test. Check the patch against
the current checkout before applying it; do not reset or overwrite newer work.

```bash
git -C /ABSOLUTE/PATH/forge-operator apply --check \
  /ABSOLUTE/PATH/ai-evaluation-lab/research/eo001_receipt_audit/first_run/sovereign-blocked-receipt.patch
git -C /ABSOLUTE/PATH/forge-operator apply \
  /ABSOLUTE/PATH/ai-evaluation-lab/research/eo001_receipt_audit/first_run/sovereign-blocked-receipt.patch
python3 /ABSOLUTE/PATH/forge-operator/integrations/ai-evaluation-lab/accept-sovereign-inference.test.py
```

Why this matters: the pinned helper contains a dependency probe before the
`try/finally` that writes `inference-receipt.json`. Missing `libgomp.so.1` can
therefore stop the run with no receipt. The regression invokes the real `main()`
against synthetic stage files and a mocked loader diagnostic. Original source
produces no receipt; patched source writes one private `FIRST_INFERENCE_BLOCKED`
receipt, calls the probe once, does not hash the model and starts no child process.

This fixes evidence retention, **not the missing OS library**. Earlier failures
before a valid stage/layout has been established may still stop without a run
receipt. The patch does not change that trust boundary or provisioning behavior.
It has not been applied to Jesse's repository or physical host.

## Reproduce without hardware or a model

```bash
python -m unittest discover -s research/eo001_receipt_audit/first_run/tests -v
python -m research.eo001_receipt_audit.first_run.fetch_sources /tmp/eo-first-run-source
python -m research.eo001_receipt_audit.first_run.verify_patch \
  --source /tmp/eo-first-run-source --output /tmp/eo-patch-verification.json
python -m research.eo001_receipt_audit.first_run.fixtures \
  --source /tmp/eo-first-run-source --output /tmp/eo-test-double-evidence.json
```

Six upstream files are pinned by commit and SHA-256. Fixture generation imports
the unchanged Evercraft v2 recorder and injects a synthetic inference function;
it never instantiates the provider credential vault or calls a model endpoint.
`test_double_evidence.json` retains the four sessions, nine model-decision
receipts plus additional error and confirmed-withheld controls. `patch_verification.json` records the
original regression failure and patched pass. These are Lab engineering evidence.

## Limits and next useful step

This supports the current frozen Lab context serialization and Evercraft v2
receipt schema. A future schema, context order or policy change needs explicit
review. The model prompt hash and provider receipt hash are retained assertions,
not independently reconstructed inference evidence. Raven may normalize provider
text before recording it; the reviewer checks candidate-recorded text, not an
unavailable original transport response. Ambiguous duplicate-key model JSON is
rejected rather than silently interpreted.

The reviewer trusts the original recorder and retained synthetic issuer key.
Unsigned model/hardware records are never promoted to authenticated provenance.
A synthetic report cannot prove what ran on HP hardware. No real model inference,
Systemia dispatch, payment, fulfillment or production certification is claimed.

Once the host dependency is resolved and a physical inference receipt exists,
review that receipt first. Then agree how the sovereign gateway will produce
the same bounded decision receipts before a model evaluation. The existing
Ollama lane is optional; this kit does not require replacing llama.cpp or Qwen.
