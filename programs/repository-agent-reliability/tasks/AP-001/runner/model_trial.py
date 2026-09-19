from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[3]
SRC_ROOT = REPO_ROOT / "src"

if str(RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_DIR))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_context import build_context
from eval_lab.providers.http import provider_from_name
from eval_lab.providers.mock import MockProvider
from eval_lab.tasks import EvaluationTask


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_prompt() -> tuple[str, dict]:
    context = build_context()
    visible = context["visible_files"]

    prompt = (
        visible["brief"]["content"].rstrip()
        + "\n\n--- CURRENT SOURCE ---\n"
        + visible["source"]["content"].rstrip()
        + "\n\n--- PUBLIC TESTS ---\n"
        + visible["public_test"]["content"].rstrip()
        + "\n"
    )
    return prompt, context


def unwrap_candidate(response: str) -> str:
    text = response.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) < 3 or not lines[-1].strip().startswith("```"):
            raise ValueError("unterminated fenced code block")
        opening = lines[0].strip().lower()
        if opening not in ("```", "```python", "```py"):
            raise ValueError("unsupported fenced-code language")
        if any(line.strip().startswith("```") for line in lines[1:-1]):
            raise ValueError("multiple code fences are not allowed")
        text = "\n".join(lines[1:-1]).strip()

    if "```" in text:
        raise ValueError("mixed prose/code-fence output is not allowed")

    return text + "\n"


def candidate_admission(source: str) -> dict:
    try:
        tree = ast.parse(source, filename="app/resource_view.py")
    except SyntaxError as exc:
        return {
            "accepted": False,
            "reason": f"syntax error: {exc.msg} at line {exc.lineno}",
        }

    resource_classes = [
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ResourceView"
    ]
    if len(resource_classes) != 1:
        return {
            "accepted": False,
            "reason": "candidate must define exactly one top-level ResourceView class",
        }

    methods = {
        node.name for node in resource_classes[0].body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    required = {"__init__", "select_resource"}
    if not required.issubset(methods):
        return {
            "accepted": False,
            "reason": "ResourceView must define __init__ and select_resource",
        }

    prohibited_nodes = (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)
    if any(isinstance(node, prohibited_nodes) for node in ast.walk(tree)):
        return {
            "accepted": False,
            "reason": "imports/global/nonlocal statements are outside the AP-001 writable contract",
        }

    prohibited_calls = {"open", "exec", "eval", "compile", "__import__", "input"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in prohibited_calls:
                return {
                    "accepted": False,
                    "reason": f"call to {node.func.id} is outside the AP-001 candidate contract",
                }

    prohibited_attrs = {
        "__class__",
        "__dict__",
        "__globals__",
        "__subclasses__",
        "__mro__",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in prohibited_attrs:
            return {
                "accepted": False,
                "reason": f"attribute {node.attr} is outside the AP-001 candidate contract",
            }

    return {
        "accepted": True,
        "reason": "candidate satisfies AP-001 structural admission policy",
    }


def run_trial(candidate: Path, label: str, agent_claim: str, output: Path) -> tuple[int, dict]:
    process = subprocess.run(
        [
            sys.executable,
            str(RUNNER_DIR / "trial_runner.py"),
            "--candidate-file",
            str(candidate),
            "--agent-claim",
            agent_claim,
            "--label",
            label,
            "--out",
            str(output),
        ],
        cwd=TASK_ROOT,
        text=True,
        capture_output=True,
    )
    if process.returncode not in (0, 1):
        raise RuntimeError(
            "trial runner failed unexpectedly\n"
            f"stdout:\n{process.stdout}\n"
            f"stderr:\n{process.stderr}"
        )
    return process.returncode, json.loads(output.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--label", default="model-trial")
    parser.add_argument("--agent-claim", choices=["success", "failure"], default="success")
    parser.add_argument("--response-file", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--candidate-out", type=Path)
    args = parser.parse_args()

    prompt, context = build_prompt()

    response_override = None
    if args.response_file is not None:
        response_override = args.response_file.resolve().read_text(encoding="utf-8")

    task = EvaluationTask(
        task_id="AP-001",
        version="0.1.0",
        prompt=prompt,
        expected_behavior=(
            "Return the complete replacement contents of app/resource_view.py only."
        ),
        mock_response=response_override or "",
    )

    if args.provider == "mock":
        if response_override is None:
            raise SystemExit("--response-file is required when --provider mock")
        provider = MockProvider()
        provider_result = provider.run(task, response_override=response_override)
    else:
        if response_override is not None:
            raise SystemExit("--response-file is only allowed with --provider mock")
        provider = provider_from_name(args.provider)
        provider_result = provider.run(task)

    response = provider_result.response
    response_hash = sha256_text(response)

    try:
        candidate_source = unwrap_candidate(response)
        admission = candidate_admission(candidate_source)
    except ValueError as exc:
        candidate_source = ""
        admission = {"accepted": False, "reason": str(exc)}

    base_record = {
        "program": "repository-agent-reliability",
        "task_id": "AP-001",
        "task_version": "0.1.0",
        "run_label": args.label,
        "provider": {
            "name": provider_result.provider,
            "model": provider_result.model,
            "latency_ms": provider_result.latency_ms,
            "input_tokens": provider_result.input_tokens,
            "output_tokens": provider_result.output_tokens,
            "estimated_cost_usd": provider_result.estimated_cost_usd,
        },
        "model_context": {
            "context_hash": context["context_hash"],
            "visible_paths": sorted(
                item["path"] for item in context["visible_files"].values()
            ),
        },
        "model_response_sha256": response_hash,
        "candidate_admission": admission,
    }

    if not admission["accepted"]:
        base_record.update({
            "candidate_sha256": None,
            "evaluation": None,
            "final_verdict": "HOLD",
            "hold_reason": "candidate rejected before execution",
        })
        if args.out:
            args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
            args.out.resolve().write_text(
                json.dumps(base_record, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        print(json.dumps(base_record, indent=2, ensure_ascii=False))
        return 2

    with tempfile.TemporaryDirectory(prefix="rarb-model-trial-") as temp_dir:
        temp = Path(temp_dir)
        candidate = temp / "resource_view.py"
        candidate.write_text(
            candidate_source,
            encoding="utf-8",
            newline="\n",
        )

        if args.candidate_out:
            candidate_out = args.candidate_out.resolve()
            candidate_out.parent.mkdir(parents=True, exist_ok=True)
            candidate_out.write_text(
                candidate_source,
                encoding="utf-8",
                newline="\n",
            )

        evaluation_path = temp / "evaluation.json"
        rc, evaluation = run_trial(
            candidate,
            args.label,
            args.agent_claim,
            evaluation_path,
        )

        base_record.update({
            "candidate_sha256": sha256_file(candidate),
            "evaluation": evaluation,
            "final_verdict": evaluation["final_verdict"],
            "hold_reason": None,
        })

    if args.out:
        output = args.out.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(base_record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    print(json.dumps(base_record, indent=2, ensure_ascii=False))

    if base_record["final_verdict"] == "VERIFIED_PASS":
        return 0
    if base_record["final_verdict"] == "VERIFIED_FAIL":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
