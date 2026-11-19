# Open-source adoption study and offline prototype

This branch reviews all **125 projects in the supplied DataVendor extract** and adds one isolated interoperability prototype. It does not represent a review of all 2,230 marketplace listings or an integration of 125 codebases.

The result is a project-by-project adoption map, 14 independently verified public source references, and a read-only Inspect JSON log adapter. The adapter preserves external observations without declaring them verified Lab evidence.

## Read the review

- [Project-by-project decisions](PROJECT_REVIEW.md): 17 near-term candidates, 54 later possibilities, 54 deferred projects.
- [Public sources and licence evidence](SOURCES.md): exact repository, commit, licence file and next gate for each of 14 sources.
- [Adoption sequence](ADOPTION_PLAN.md): how the useful ideas fit existing AS/RARB, tool, execution and evidence work.
- [Validation](VALIDATION.md): actual tests and their limits.
- Machine-readable [catalogue](catalogue.json), [sources](sources.json) and [baseline](baseline.json).

The marketplace descriptions do not establish an open-source licence. The exact sold source/history remains unverified for every listed asset. Even when a public project exists, its licence does not automatically cover a vendor's private snapshot, benchmark tasks, customer records or media. No paid source was accessed, purchased or copied. Public alternatives and name collisions are identified in the catalogue.

## Isolation

Baseline: `kaulastudies/ai-evaluation-lab` main at `c8f4b4ed0af988ebe8ca9821c472642ab4c20f63`.

All changes belong under `research/open_source_adoption/` on `research/open-source-adoption-20261029`. The branch adds no imports to the existing runtime, no dependencies, no CI workflow edits, no deployment configuration, no provider calls and no schedules. Existing AS contracts, RARB task/verifier/evidence files, root documentation, funding statements and private control-plane boundaries are preserved. Open PRs #26 and #27 remain separate.

Use this work as a draft review branch. It does not change the Lab's published capabilities or add live attempts. Run logs created by tests are synthetic or source-exact replay, not new provider results.

## Run locally

Python 3.10+ and the standard library are sufficient. From the repository root:

```bash
python -m unittest discover -s research/open_source_adoption/tests -v
python research/open_source_adoption/adoption.py catalogue-check
python research/open_source_adoption/adoption.py isolation-check
```

The isolation command compares tracked and untracked nonignored paths against the pinned baseline. It is a local change check, not a remote branch-protection rule or security attestation. The remote PR diff must also remain additive and confined to this directory.

Inspect the independently authored example:

```bash
python - <<'PY'
import hashlib, subprocess, sys
from pathlib import Path
path = Path('research/open_source_adoption/examples/inspect_synthetic.json')
digest = hashlib.sha256(path.read_bytes()).hexdigest()
subprocess.run([sys.executable, 'research/open_source_adoption/adoption.py',
                'inspect-json', str(path), '--expected-sha256', digest], check=True)
PY
```

For other logs, supply a digest obtained through the evidence review process. Computing a digest yourself, as in the example, checks byte identity only; it does not prove who produced the log. The command reads one local file and prints JSON to standard output. It never rewrites the input or writes to `runs/`.

## Implemented adapter contract

Accepted input is a bounded **Inspect JSON log format v2 subset**, based on the pinned upstream interface in [SOURCES.md](SOURCES.md). Binary `.eval` logs must first be exported with upstream Inspect tooling in a separate environment. This prototype does not install or invoke that tooling.

- Preserve every supplied sample and scorer, keyed by typed sample ID and epoch. Duplicate sample/epoch pairs are rejected.
- Preserve declared planned/completed/logged counts separately from the observed sample count. Missing samples, failed or cancelled execution, invalidations, sample errors, limits and early stopping remain visible.
- Keep scalar, categorical and structured upstream scores opaque. A score of `1`, `C` or an aggregate accuracy does not become a Lab `PASS`.
- Require a matching source SHA-256, reject duplicate JSON keys, non-finite numbers, unknown versions and unsupported shapes. Bounds: 16 MiB, 10,000 samples, JSON nesting 64, score nesting 8.
- Return `evidence_state: UNVERIFIED_EXTERNAL`, `lab_verdict: null` and `promotion_allowed: false` in every successful report. No aggregate-to-sample fallback and no inference of provider identity from a model name.
- Omit raw inputs, answers, messages, arbitrary metadata and error text. Sample IDs, task/model labels and score values remain, so this is not a general PII sanitizer.
- Produce deterministic output and a canonical report digest. A digest is integrity evidence, not author authentication or an independent verifier result.

CLI exit `0` means the input was represented successfully, **not** that the evaluated agent passed. Exit `2` indicates rejected input or an operational error. For `isolation-check`, exit `1` means changes exist outside the allowed directory.

This is not a complete EvalLog validator. It does not reconstruct transcripts, validate aggregate metrics, authenticate external receipts, bind frozen AS/RARB contracts, judge models or submit evidence to the Lab. Additional upstream fields can be ignored by the subset; they remain bound by the source digest. Empty incompleteness reasons do not imply verified evidence.

## Relationship to existing code

`src/eval_lab/local_evidence.py` already handles the historical local Inspect/Harbor baseline. Its implementation and frozen records are unchanged. This new adapter is an experimental intake format for future multi-sample external observations; it does not replace or silently reinterpret the historical converter.

Original code and documentation here use the repository's Apache-2.0 licence. Referenced projects retain their own licences and notices. No third-party implementation is vendored.
