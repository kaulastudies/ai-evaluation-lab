# AI Evaluation Lab: YC product and evidence brief

Prepared 31 October 2026. This is a public product proposal and reviewer guide, not a submitted application or an investment announcement.

**Release checks for AI-generated code.** AI Evaluation Lab develops checks that help an engineering team decide whether a coding-agent patch satisfies a defined task contract. ProofGate is the working demonstration.

[Company website](https://aievaluationlab.tech/) · [Executable demo](https://aievaluationlab.tech/proofgate/) · [Competition and YC research](RESEARCH.md) · [Qatar and commercial validation](QATAR_AND_VALIDATION.md)

## The concrete problem

A code change can pass the available tests and still break a requirement those tests never exercised. In our recorded AP-005 example, the coding agent produced a transformation routine that passed its public test but failed independent checks for preserved rows, exact values, optional fields and input mutation.

ProofGate first qualifies a task verifier against a passing reference and known faults. It then evaluates the candidate against the frozen contract and keeps the verdict, failed checks and relevant artifacts. A reviewer can examine the failure and compare a bounded repair against the same criteria.

The initial buyer hypothesis is an engineering or release lead adopting coding agents. The proposed paid outcome is a maintained set of checks for one recurring repository workflow, with less manual work to establish why a change should be accepted. Neither time savings nor willingness to pay has been established by the synthetic experiments.

## Try it in two minutes

1. Open the [demo](https://aievaluationlab.tech/proofgate/) and run **Catch the false-green**. Public tests pass; the independent verifier fails four contract checks.
2. Select **Check the repair** and run the checks. The corrected candidate passes the same verifier.
3. Run **Test the verifier · all 6 controls**. The reference should pass; the known-bad baseline and four mutations should be rejected. Read the gate IDs in the results.

The site executes bundled Python in a browser worker. It does not request a new model generation. The browser run, historical evidence and source-exact local replay are different operations. The demo identifies its evidence snapshot; it need not share the latest documentation commit.

## What the evidence supports

The [canonical metrics](../../programs/repository-agent-reliability/metrics/metrics.json) at repository commit `6049b684ea131d832718dc9e6061090b0431f470` report:

| Observation | Interpretation and limit |
| --- | --- |
| 52 retained attempts: 44 pass, 5 fail, 3 hold | Five synthetic repository tasks; not 52 users or customer deployments |
| 3 of 46 success claims with passing public tests failed verification | Includes repairs; the initial-attempt subset is 2 of 44. Not a population failure-rate estimate |
| 17 of 17 configured critical mutations rejected | Evidence for these specific controls; not exhaustive verifier security |
| One of two repair episodes converted to a pass | AP-005 repaired successfully; AP-003's terminal failure remains visible |
| 30 AP-001 replication trials retained | Already included in the 52; replay does not create new model attempts |

One additional retained pass lacks model/provider metadata. Missing provenance and incomplete economic-cost coverage remain explicit in the ledger. Do not turn reported local-provider cost fields into a claim of zero operating cost.

Reproduce the evidence checks from a full Git clone, using Python 3.10 or later:

```bash
PYTHONPATH=src python programs/repository-agent-reliability/metrics/metrics_check.py
PYTHONPATH=src python programs/repository-agent-reliability/demo/run_demo_check.py
```

These checks use committed artifacts without new model inference. The local runner is not a security sandbox for arbitrary customer code. Customer execution needs reviewed isolation and permissioned artifacts.

## From prototype to repeat use

Start with one paid workflow, then reuse its contract patterns, adapters and verification execution across subsequent customers. The proposal is a $5,000 four-week pilot followed by $1,000 per month per maintained workflow. These are pricing hypotheses. At that recurring price, 1,000 workflows would represent $12 million annually; this is arithmetic, not a forecast or measured TAM.

The next proof is a buyer-authorized workflow, a baseline comparison, measured installation and maintenance effort, and a paid repeat use. More synthetic runs alone cannot establish demand. The main risks are customer-specific setup cost, weak checks, false rejections, execution isolation and adequate existing alternatives.

The public research program and existing grants remain distinct from this commercial proposal. ProofQ is a separate research direction; it is not the name or demonstrated capability of this coding-agent product.
