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

    ap001_hold = find_attempt(
        attempts,
        "ap001-ollama-llama3-002",
    )
    ap001_pass = find_attempt(
        attempts,
        "ap001-ollama-llama3-003",
    )
    ap002_pass = find_attempt(
        attempts,
        "ap002-ollama-llama3-001",
    )
    ap003_initial = find_attempt(
        attempts,
        "ap003-ollama-llama3-001",
    )
    ap003_repair_hold = find_attempt(
        attempts,
        "ap003-ollama-llama3-002-repair",
    )
    ap003_terminal = find_attempt(
        attempts,
        "ap003-ollama-llama3-003-repair",
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
        ],
        "demonstrated": [
            (
                "Verifier qualification with reference, known-bad, and "
                "critical mutation controls."
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
                "Source-exact no-model replay across historical evaluator "
                "versions, including repair HOLD and terminal repair failure."
            ),
            (
                "Evidence-derived metrics without fabricating missing fields."
            ),
        ],
        "not_yet_demonstrated": [
            (
                "A successful bounded repair conversion from "
                "VERIFIED_FAIL to VERIFIED_PASS."
            ),
            (
                "Repeated multi-model or statistically meaningful benchmark "
                "performance."
            ),
            (
                "AP-004 and AP-005 live task evidence."
            ),
            (
                "Nebius/NVIDIA production-runtime evidence."
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
        "## The strongest live example: AP-003",
        "",
        "1. The initial candidate passed public tests.",
        "2. The qualified verifier rejected it on idempotency gates.",
        "3. RARB classified the run as `VERIFIED_FAIL` and `false_green=true`.",
        "4. Only bounded failed-gate evidence was exposed for repair.",
        "5. Repair attempt 1 was rejected at admission and recorded as `HOLD`.",
        "6. Repair attempt 2 was admitted, again passed public tests, and "
        "still failed the qualified verifier.",
        "7. The repair budget was exhausted and the terminal failure was "
        "frozen instead of silently rerun.",
        "8. Both repair outcomes are source-exact replayable without model "
        "inference.",
        "",
        "That is the product behavior: **RARB measures whether a patch "
        "deserves to ship; it does not manufacture a passing result.**",
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

    lines.extend(
        [
            "## Demonstrated",
            "",
        ]
    )
    for item in payload["demonstrated"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Not yet demonstrated",
            "",
        ]
    )
    for item in payload["not_yet_demonstrated"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "These numbers describe the committed RARB evidence set only. "
            "They are not claims about general coding-agent performance. "
            "Local Ollama provider billing is reported as zero, but economic "
            "execution cost is unmetered and therefore Cost / Verified Success "
            "remains N/A.",
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
