from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEMO_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = DEMO_ROOT.parent
METRICS_PATH = PROGRAM_ROOT / "metrics" / "summary.json"


def load_summary() -> dict[str, Any]:
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


def pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def find_attempt(
    attempts: list[dict[str, Any]],
    run_label: str,
) -> dict[str, Any]:
    matches = [
        attempt
        for attempt in attempts
        if attempt["run_label"] == run_label
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one attempt named {run_label}; "
            f"found {len(matches)}"
        )
    return matches[0]


def build_payload(summary: dict[str, Any]) -> dict[str, Any]:
    attempts = summary["attempts"]
    counts = summary["counts"]
    metrics = summary["metrics"]

    ap001_hold = find_attempt(attempts, "ap001-ollama-llama3-002")
    ap001_pass = find_attempt(attempts, "ap001-ollama-llama3-003")
    ap001_nebius_pass = find_attempt(
        attempts,
        "phase-11c-nebius-nemotron-pilot-v1-ap-001-"
        "nebius-nemotron-3-super-120b-a12b-i001",
    )
    ap002_pass = find_attempt(attempts, "ap002-ollama-llama3-001")
    ap003_initial = find_attempt(attempts, "ap003-ollama-llama3-001")
    ap003_repair_hold = find_attempt(
        attempts,
        "ap003-ollama-llama3-002-repair",
    )
    ap003_terminal = find_attempt(
        attempts,
        "ap003-ollama-llama3-003-repair",
    )
    ap004_hold = find_attempt(attempts, "ap004-ollama-llama3-001")
    ap004_pass = find_attempt(attempts, "ap004-ollama-llama3-002")
    ap005_fail = find_attempt(attempts, "ap005-ollama-llama3-001")
    ap005_repair = find_attempt(
        attempts,
        "ap005-ollama-llama3-002-repair",
    )

    return {
        "schema_version": "1.0.0",
        "program": "repository-agent-reliability",
        "headline": (
            "Verify the evaluation before trusting the verdict."
        ),
        "evidence_snapshot": {
            "live_attempts": counts["attempts_total"],
            "verified_pass": counts["verified_pass"],
            "verified_fail": counts["verified_fail"],
            "hold": counts["hold"],
            "qualified_tasks": summary[
                "verifier_qualification"
            ]["qualified_tasks"],
            "critical_mutations_total": summary[
                "verifier_qualification"
            ]["critical_mutations_total"],
            "critical_mutation_escapes": summary[
                "verifier_qualification"
            ]["critical_mutation_escapes"],
            "claim_evidence_gap": metrics[
                "claim_evidence_gap"
            ]["value"],
            "false_green_rate": metrics[
                "false_green_rate"
            ]["value"],
            "initial_false_green_rate": metrics[
                "initial_false_green_rate"
            ]["value"],
            "repair_conversion": metrics[
                "repair_conversion"
            ]["value"],
            "median_time_to_verified_success_ms": metrics[
                "median_time_to_verified_success_ms"
            ]["value"],
        },
        "task_evidence": [
            {
                "task_id": "AP-001",
                "theme": "stale asynchronous response",
                "observations": [
                    {
                        "run_label": ap001_hold["run_label"],
                        "verdict": ap001_hold["final_verdict"],
                        "note": (
                            "Model response was rejected before execution; "
                            "no candidate verdict was inferred."
                        ),
                    },
                    {
                        "run_label": ap001_pass["run_label"],
                        "verdict": ap001_pass["final_verdict"],
                        "note": (
                            "Admitted candidate passed public validation "
                            "and the qualified verifier."
                        ),
                    },
                    {
                        "run_label": ap001_nebius_pass["run_label"],
                        "verdict": ap001_nebius_pass["final_verdict"],
                        "note": (
                            "The preregistered Nebius/NVIDIA pilot was "
                            "admitted, passed public validation and every "
                            "qualified verifier gate, preserved the trusted "
                            "boundary, and passed source-exact replay."
                        ),
                    },
                ],
            },
            {
                "task_id": "AP-002",
                "theme": "permission-boundary isolation",
                "observations": [
                    {
                        "run_label": ap002_pass["run_label"],
                        "verdict": ap002_pass["final_verdict"],
                        "note": (
                            "Admitted candidate passed four verifier gates "
                            "under qualified controls."
                        ),
                    }
                ],
            },
            {
                "task_id": "AP-003",
                "theme": "idempotency and duplicate processing",
                "observations": [
                    {
                        "run_label": ap003_initial["run_label"],
                        "verdict": ap003_initial["final_verdict"],
                        "note": (
                            "Public tests passed, but the qualified verifier "
                            "caught duplicate-processing failures: a genuine "
                            "false-green."
                        ),
                    },
                    {
                        "run_label": ap003_repair_hold["run_label"],
                        "verdict": ap003_repair_hold["final_verdict"],
                        "note": (
                            "First bounded repair attempt was rejected at "
                            "admission because the raw output format was invalid."
                        ),
                    },
                    {
                        "run_label": ap003_terminal["run_label"],
                        "verdict": ap003_terminal["final_verdict"],
                        "note": (
                            "Final allowed repair was admitted and public tests "
                            "passed, but the same qualified verifier gates still "
                            "failed. Repair budget was exhausted."
                        ),
                    },
                ],
            },
            {
                "task_id": "AP-004",
                "theme": "API contract regression",
                "observations": [
                    {
                        "run_label": ap004_hold["run_label"],
                        "verdict": ap004_hold["final_verdict"],
                        "note": (
                            "The first live model response used v1 and had an "
                            "unterminated fenced code block, so it was rejected "
                            "before execution and frozen as HOLD."
                        ),
                    },
                    {
                        "run_label": ap004_pass["run_label"],
                        "verdict": ap004_pass["final_verdict"],
                        "note": (
                            "A separately versioned v2 initial attempt was "
                            "admitted, passed public validation, passed all four "
                            "qualified verifier gates, and preserved the trusted "
                            "boundary."
                        ),
                    },
                ],
            },
            {
                "task_id": "AP-005",
                "theme": "data-transformation edge cases",
                "observations": [
                    {
                        "run_label": ap005_fail["run_label"],
                        "verdict": ap005_fail["final_verdict"],
                        "note": (
                            "The initial candidate was admitted and passed public "
                            "tests, but the qualified verifier rejected all four "
                            "edge-case gates: a genuine false-green."
                        ),
                    },
                    {
                        "run_label": ap005_repair["run_label"],
                        "verdict": ap005_repair["final_verdict"],
                        "note": (
                            "A bounded repair received only failed gate IDs and "
                            "diagnostics, was admitted, passed public validation "
                            "and all four qualified verifier gates, and converted "
                            "the parent VERIFIED_FAIL to VERIFIED_PASS."
                        ),
                    },
                ],
            },
        ],
        "demonstrated": [
            (
                "Verifier qualification with reference, known-bad, and "
                "critical mutation controls across all five benchmark tasks."
            ),
            (
                "Public-test false-green detection under a qualified verifier."
            ),
            (
                "Trusted-boundary checks and deterministic evaluation records."
            ),
            (
                "Bounded evidence-guided repair with an explicit attempt budget."
            ),
            (
                "A successful bounded repair conversion from VERIFIED_FAIL to "
                "VERIFIED_PASS on AP-005."
            ),
            (
                "Source-exact no-model replay across historical evaluator "
                "versions, including repair HOLD, terminal repair failure, and "
                "successful repair conversion."
            ),
            (
                "Separately versioned initial-output protocols without rewriting "
                "the frozen earlier HOLD."
            ),
            (
                "Live initial model evidence across AP-001 through AP-005."
            ),
            (
                "One preregistered Nebius/NVIDIA-backed AP-001 initial "
                "attempt using nvidia/nemotron-3-super-120b-a12b, with a "
                "source-exact replayable VERIFIED_PASS."
            ),
            (
                "Evidence-derived metrics without fabricating missing fields."
            ),
        ],
        "not_yet_demonstrated": [
            (
                "The original AP-001 Section 9 sequence as written, including "
                "a successful repair conversion within AP-001 itself."
            ),
            (
                "Repeated multi-model or statistically meaningful benchmark "
                "performance."
            ),
            (
                "Production-scale runtime evidence, including repeated "
                "throughput, reliability, and complete economic-cost "
                "measurement."
            ),
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    snap = payload["evidence_snapshot"]

    lines = [
        "# RARB Demo Evidence Brief",
        "",
        f"> {payload['headline']}",
        "",
        "## What RARB does",
        "",
        "RARB treats the coding agent as the system under test. "
        "A patch is not accepted because the model says it is done or "
        "because public tests happen to pass. The task verifier is "
        "qualified first, then the candidate is scored against the frozen "
        "contract, and the resulting evidence can be replayed without "
        "rerunning model inference.",
        "",
        "## Current evidence snapshot",
        "",
        f"- **{snap['live_attempts']}** committed live attempts",
        f"- **{snap['verified_pass']} VERIFIED_PASS / "
        f"{snap['verified_fail']} VERIFIED_FAIL / "
        f"{snap['hold']} HOLD**",
        f"- **{snap['qualified_tasks']}** qualified tasks",
        f"- **{snap['critical_mutation_escapes']} / "
        f"{snap['critical_mutations_total']}** critical verifier "
        "mutations escaped",
        f"- Claim-Evidence Gap: **{pct(snap['claim_evidence_gap'])}**",
        f"- False-Green Rate: **{pct(snap['false_green_rate'])}**",
        f"- Initial False-Green Rate: "
        f"**{pct(snap['initial_false_green_rate'])}**",
        f"- Repair Conversion: **{pct(snap['repair_conversion'])}**",
        (
            "- Median recorded generation latency among verified successes: "
            f"**{snap['median_time_to_verified_success_ms'] / 1000:.2f}s**"
        ),
        "",
        "## Successful bounded-repair example: AP-005",
        "",
        "1. The initial AP-005 candidate passed public tests.",
        "2. The qualified verifier rejected all four edge-case gates.",
        "3. RARB froze the initial attempt as `VERIFIED_FAIL` and "
        "`false_green=true`.",
        "4. The repair received bounded failed-gate evidence only.",
        "5. The repair candidate was admitted and passed public tests.",
        "6. The same qualified verifier passed all four gates.",
        "7. RARB recorded `repair_conversion=true` and `VERIFIED_PASS`.",
        "8. The repair outcome is source-exact replayable without model "
        "inference.",
        "",
        "## Failure-preservation example: AP-003",
        "",
        "AP-003 remains the counterexample: bounded repair was attempted but "
        "did not convert within its configured budget. RARB preserved that "
        "terminal failure instead of manufacturing a successful outcome.",
        "",
        "## Task evidence",
        "",
    ]

    for task in payload["task_evidence"]:
        lines.append(f"### {task['task_id']} - {task['theme']}")
        lines.append("")
        for item in task["observations"]:
            lines.append(
                f"- `{item['run_label']}` - "
                f"**{item['verdict']}** - {item['note']}"
            )
        lines.append("")

    lines.extend(["## Demonstrated", ""])
    for item in payload["demonstrated"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Not yet demonstrated", ""])
    for item in payload["not_yet_demonstrated"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "These numbers describe the committed RARB evidence set only. "
            "They are not claims about general coding-agent performance. "
            "The successful AP-005 repair conversion closes the general "
            "repair-conversion evidence gap, but it does not retroactively "
            "satisfy the original AP-001-specific Section 9 sequence. "
            "The AP-004 v1 HOLD and v2 VERIFIED_PASS are separate observed "
            "attempts; this evidence does not by itself establish that the "
            "protocol change caused the different outcome. Local Ollama "
            "provider billing is reported as zero, but economic execution "
            "cost is unmetered and therefore Cost / Verified Success "
            "remains N/A. The single Nebius/NVIDIA AP-001 pilot establishes "
            "provider-backed repository-task execution under the RARB "
            "protocol; it does not establish statistical or production-scale "
            "performance.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()

    summary = load_summary()
    payload = build_payload(summary)
    markdown = render_markdown(payload)

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(
            markdown,
            encoding="utf-8",
            newline="\n",
        )

    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
