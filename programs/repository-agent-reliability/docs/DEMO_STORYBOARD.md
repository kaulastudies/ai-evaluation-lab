# Demo Storyboard — v0

## Act 1: Qualify the judge
Reference -> PASS; known-bad -> FAIL; mutations -> rejected; verifier -> QUALIFIED.

## Act 2: Evaluate the coding agent
Task contract -> Nemotron attempt -> public tests green -> agent says FIXED ->
qualified verifier says VERIFIED_FAIL.

## Act 3: Evidence-guided repair
Failed gate ID + bounded diagnostic -> repair -> VERIFIED_PASS.

## Act 4: Research evidence
Show claim–evidence gap, false-green rate, repair conversion, cost, latency, attempts.

## Act 5: Replay
Re-run verification without model inference.

Closing line:
**AI can propose the patch. AI Evaluation Lab measures whether the patch deserves to ship.**
