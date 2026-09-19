from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


DEMO_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = DEMO_ROOT.parent
REPO_ROOT = PROGRAM_ROOT.parents[1]

RUNNER_ROOT = PROGRAM_ROOT / "runner"
METRICS_ROOT = PROGRAM_ROOT / "metrics"

GENERATED_EVIDENCE_FILES = [
    METRICS_ROOT / "summary.json",
    METRICS_ROOT / "REPORT.md",
    DEMO_ROOT / "EVIDENCE_BRIEF.json",
    DEMO_ROOT / "EVIDENCE_BRIEF.md",
]


@dataclass
class CheckResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def run_check(name: str, command: list[str]) -> CheckResult:
    process = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    return CheckResult(
        name=name,
        command=command,
        returncode=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def regenerate_artifacts() -> list[CheckResult]:
    return [
        run_check(
            "metrics_generate",
            [
                sys.executable,
                str(METRICS_ROOT / "aggregate.py"),
                "--out-json",
                str(METRICS_ROOT / "summary.json"),
                "--out-md",
                str(METRICS_ROOT / "REPORT.md"),
            ],
        ),
        run_check(
            "evidence_brief_generate",
            [
                sys.executable,
                str(DEMO_ROOT / "build_evidence_brief.py"),
                "--out-json",
                str(DEMO_ROOT / "EVIDENCE_BRIEF.json"),
                "--out-md",
                str(DEMO_ROOT / "EVIDENCE_BRIEF.md"),
            ],
        ),
    ]


def validate_system() -> list[CheckResult]:
    return [
        run_check(
            "runner_self_check",
            [sys.executable, str(RUNNER_ROOT / "self_check.py")],
        ),
        run_check(
            "source_exact_replay",
            [sys.executable, str(RUNNER_ROOT / "replay_check.py")],
        ),
        run_check(
            "source_exact_repair_replay",
            [
                sys.executable,
                str(RUNNER_ROOT / "repair_replay_check.py"),
            ],
        ),
        run_check(
            "metrics_check",
            [sys.executable, str(METRICS_ROOT / "metrics_check.py")],
        ),
        run_check(
            "demo_evidence_check",
            [sys.executable, str(DEMO_ROOT / "demo_check.py")],
        ),
    ]


def generated_files_fresh() -> tuple[bool, str]:
    relative = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in GENERATED_EVIDENCE_FILES
    ]
    process = subprocess.run(
        ["git", "diff", "--exit-code", "--", *relative],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    return process.returncode == 0, process.stdout + process.stderr


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_status(
    checks: list[CheckResult],
    artifacts_fresh: bool,
) -> dict[str, Any]:
    summary = load_json(METRICS_ROOT / "summary.json")
    brief = load_json(DEMO_ROOT / "EVIDENCE_BRIEF.json")

    counts = summary["counts"]
    metrics = summary["metrics"]

    return {
        "schema_version": "1.0.0",
        "program": "repository-agent-reliability",
        "demo_entrypoint": "phase7c-one-command-v1",
        "status": (
            "GREEN"
            if all(check.passed for check in checks)
            and artifacts_fresh
            else "FAILED"
        ),
        "checks": {
            check.name: {
                "passed": check.passed,
                "returncode": check.returncode,
            }
            for check in checks
        },
        "generated_artifacts_match_head_evidence": artifacts_fresh,
        "evidence_snapshot": {
            "attempts_total": counts["attempts_total"],
            "verified_pass": counts["verified_pass"],
            "verified_fail": counts["verified_fail"],
            "hold": counts["hold"],
            "qualified_tasks": summary[
                "verifier_qualification"
            ]["qualified_tasks"],
            "critical_mutation_escapes": summary[
                "verifier_qualification"
            ]["critical_mutation_escapes"],
            "critical_mutations_total": summary[
                "verifier_qualification"
            ]["critical_mutations_total"],
            "claim_evidence_gap": metrics[
                "claim_evidence_gap"
            ]["value"],
            "false_green_rate": metrics[
                "false_green_rate"
            ]["value"],
            "repair_conversion": metrics[
                "repair_conversion"
            ]["value"],
        },
        "evidence_boundary": brief["not_yet_demonstrated"],
    }


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def render_markdown(status: dict[str, Any]) -> str:
    snap = status["evidence_snapshot"]

    lines = [
        "# RARB Demo Status",
        "",
        f"**Overall: {status['status']}**",
        "",
        (
            "- Generated evidence artifacts match committed evidence: "
            f"**{status['generated_artifacts_match_head_evidence']}**"
        ),
        "",
        "## Validation checks",
        "",
    ]

    for name, result in status["checks"].items():
        lines.append(
            f"- {name}: **{'PASS' if result['passed'] else 'FAIL'}**"
        )

    lines.extend(
        [
            "",
            "## Evidence snapshot",
            "",
            f"- Attempts: **{snap['attempts_total']}**",
            (
                f"- Verdicts: **{snap['verified_pass']} VERIFIED_PASS / "
                f"{snap['verified_fail']} VERIFIED_FAIL / "
                f"{snap['hold']} HOLD**"
            ),
            f"- Qualified tasks: **{snap['qualified_tasks']}**",
            (
                "- Critical verifier mutation escapes: "
                f"**{snap['critical_mutation_escapes']} / "
                f"{snap['critical_mutations_total']}**"
            ),
            (
                "- Claim-Evidence Gap: "
                f"**{fmt_pct(snap['claim_evidence_gap'])}**"
            ),
            (
                "- False-Green Rate: "
                f"**{fmt_pct(snap['false_green_rate'])}**"
            ),
            (
                "- Repair Conversion: "
                f"**{fmt_pct(snap['repair_conversion'])}**"
            ),
            "",
            "## Evidence boundary",
            "",
        ]
    )

    for item in status["evidence_boundary"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "The status file is a compact demo index. Detailed evidence remains "
            "in `metrics/REPORT.md`, `demo/EVIDENCE_BRIEF.md`, and the frozen "
            "task evidence directories.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument(
        "--show-failure-logs",
        action="store_true",
    )
    args = parser.parse_args()

    generation = regenerate_artifacts()
    failed_generation = [
        result for result in generation if not result.passed
    ]
    if failed_generation:
        for result in failed_generation:
            print(f"{result.name}: FAIL")
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        return 1

    checks = validate_system()
    artifacts_fresh, freshness_diff = generated_files_fresh()

    status = compact_status(checks, artifacts_fresh)
    markdown = render_markdown(status)

    if args.out_json:
        out_json = args.out_json.resolve()
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(
            json.dumps(status, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    if args.out_md:
        out_md = args.out_md.resolve()
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(
            markdown,
            encoding="utf-8",
            newline="\n",
        )

    print("=== RARB ONE-COMMAND DEMO ===")
    for check in checks:
        print(
            f"{check.name}: "
            f"{'PASS' if check.passed else 'FAIL'}"
        )
        if (
            args.show_failure_logs
            and not check.passed
        ):
            if check.stdout:
                print(check.stdout.rstrip())
            if check.stderr:
                print(check.stderr.rstrip(), file=sys.stderr)

    print(
        "generated_artifacts_match_head_evidence: "
        + ("PASS" if artifacts_fresh else "FAIL")
    )

    if not artifacts_fresh and freshness_diff:
        print(freshness_diff.rstrip())

    print("")
    print(markdown.rstrip())
    print("")
    print(
        "PHASE 7C ONE-COMMAND DEMO GREEN"
        if status["status"] == "GREEN"
        else "PHASE 7C ONE-COMMAND DEMO FAILED"
    )

    return 0 if status["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
