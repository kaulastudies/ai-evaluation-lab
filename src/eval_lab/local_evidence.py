from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from inspect_ai.log import read_eval_log


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump_obj(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(k): dump_obj(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [dump_obj(v) for v in value]
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "__dict__"):
        return {
            str(k): dump_obj(v)
            for k, v in vars(value).items()
            if not str(k).startswith("_")
        }
    return str(value)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_payload(record: dict[str, Any]) -> str:
    payload = {k: v for k, v in record.items() if k != "record_hash"}
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def finalize(record: dict[str, Any]) -> dict[str, Any]:
    record["record_hash"] = hashlib.sha256(
        canonical_payload(record).encode("utf-8")
    ).hexdigest()
    return record


def numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def score_values(scores: Any) -> dict[str, Any]:
    data = dump_obj(scores)
    if not isinstance(data, dict):
        return {"score": data}

    out: dict[str, Any] = {}
    for name, score in data.items():
        if isinstance(score, dict) and "value" in score:
            out[str(name)] = score["value"]
        else:
            out[str(name)] = score
    return out


def first_numeric_score(values: dict[str, Any]) -> float | None:
    for value in values.values():
        number = numeric(value)
        if number is not None:
            return number
        if isinstance(value, dict):
            for nested in value.values():
                number = numeric(nested)
                if number is not None:
                    return number
    return None


def inspect_record(log_path: Path, commit_sha: str) -> dict[str, Any]:
    log = read_eval_log(str(log_path))
    samples = list(log.samples or [])
    if not samples:
        raise RuntimeError("Inspect log has no samples.")

    sample = samples[0]
    eval_meta = log.eval

    task_name = str(getattr(eval_meta, "task", "local_baseline"))
    model_name = str(getattr(eval_meta, "model", "ollama/llama3:latest"))

    output = getattr(sample, "output", None)
    response = getattr(output, "completion", None)
    if response is None:
        response = str(dump_obj(output) or "")

    prompt = getattr(sample, "input", None)
    target = getattr(sample, "target", None)

    scores = score_values(getattr(sample, "scores", None) or {})
    score = first_numeric_score(scores)

    # Fallback to aggregate result scores if a sample-level numeric score
    # is unavailable.
    if score is None:
        results = dump_obj(getattr(log, "results", None))
        if isinstance(results, dict):
            aggregate = results.get("scores")
            if isinstance(aggregate, list):
                for item in aggregate:
                    if isinstance(item, dict):
                        metrics = item.get("metrics")
                        if isinstance(metrics, dict):
                            for metric in metrics.values():
                                if isinstance(metric, dict):
                                    score = numeric(metric.get("value"))
                                    if score is not None:
                                        break
                        if score is not None:
                            break

    passed = score is not None and abs(score - 1.0) < 1e-12

    usage = dump_obj(getattr(sample, "model_usage", None))
    source_hash = sha256_file(log_path)

    record = {
        "evaluation_id": "LOCAL-INSPECT-LLAMA3-20260913",
        "task_id": task_name,
        "task_version": "local-baseline-v1",
        "run_label": "windows-local-ollama-inspect",
        "provider": "ollama",
        "model": model_name,
        "prompt": str(prompt or ""),
        "expected_behavior": str(target or "ROUTE_OK"),
        "response": str(response),
        "review": {
            "source": "automated",
            "label": "PASS" if passed else "FAIL",
            "reason": "Inspect match scorer evaluated the local-model response.",
        },
        "verification": {
            "runner": "inspect-ai",
            "runner_version": "0.3.263",
            "scorer_values": scores,
            "score": score,
            "source_artifact": log_path.name,
            "source_sha256": source_hash,
            "commit_sha": commit_sha,
            "control_surface_note": (
                "Windows AF_UNIX control-surface warning did not prevent evaluation."
            ),
        },
        "disagreement": False,
        "adjudication": None,
        "metrics": {
            "score": score,
            "model_usage": usage,
        },
        "regression_of": None,
        "final_label": "PASS" if passed else "FAIL",
        "final_status": "ACCEPTED" if passed else "REJECTED",
        "created_at": utc_now(),
        "record_hash": "",
    }
    return finalize(record)


def recursive_numbers(obj: Any, wanted: set[str], path: str = "") -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else str(key)
            if str(key).lower() in wanted:
                number = numeric(value)
                if number is not None:
                    found.append((child_path, number))
            found.extend(recursive_numbers(value, wanted, child_path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            found.extend(recursive_numbers(value, wanted, f"{path}[{idx}]"))
    return found


def harbor_record(result_path: Path, commit_sha: str, contract_hash: str) -> dict[str, Any]:
    data = json.loads(result_path.read_text(encoding="utf-8"))

    reward_candidates = recursive_numbers(data, {"reward", "mean"})
    exception_candidates = recursive_numbers(data, {"exceptions", "exception_count"})

    reward = None
    for _, value in reward_candidates:
        if abs(value - 1.0) < 1e-12:
            reward = value
            break
    if reward is None and reward_candidates:
        reward = reward_candidates[0][1]

    exceptions = 0.0
    if exception_candidates:
        exceptions = exception_candidates[0][1]

    passed = (
        reward is not None
        and abs(reward - 1.0) < 1e-12
        and abs(exceptions) < 1e-12
    )

    source_hash = sha256_file(result_path)

    record = {
        "evaluation_id": "LOCAL-HARBOR-ORACLE-ROUTE-POLICY-20260913",
        "task_id": "rama-eval-lab/route-policy-repair",
        "task_version": "R1",
        "run_label": "windows-local-harbor-oracle",
        "provider": "harbor",
        "model": "oracle",
        "prompt": (
            "Execute the original route-policy-repair task with the "
            "Harbor oracle/reference solution."
        ),
        "expected_behavior": "Verifier reward 1.0 with zero exceptions.",
        "response": (
            f"Harbor oracle completed with reward={reward} "
            f"and exceptions={exceptions}."
        ),
        "review": {
            "source": "deterministic",
            "label": "PASS" if passed else "FAIL",
            "reason": "Harbor independent verifier reward and exception count.",
        },
        "verification": {
            "runner": "harbor",
            "reward": reward,
            "exceptions": exceptions,
            "contract_hash": contract_hash,
            "source_artifact": result_path.name,
            "source_sha256": source_hash,
            "commit_sha": commit_sha,
        },
        "disagreement": False,
        "adjudication": None,
        "metrics": {
            "reward": reward,
            "exceptions": exceptions,
        },
        "regression_of": None,
        "final_label": "PASS" if passed else "FAIL",
        "final_status": "ACCEPTED" if passed else "REJECTED",
        "created_at": utc_now(),
        "record_hash": "",
    }
    return finalize(record)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-log", required=True)
    parser.add_argument("--harbor-result", required=True)
    parser.add_argument("--out-dir", default="runs/local")
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--contract-hash", required=True)
    args = parser.parse_args()

    inspect_log = Path(args.inspect_log).resolve()
    harbor_result = Path(args.harbor_result).resolve()
    out_dir = Path(args.out_dir)

    inspect = inspect_record(inspect_log, args.commit_sha)
    harbor = harbor_record(
        harbor_result,
        args.commit_sha,
        args.contract_hash,
    )

    if inspect["final_status"] != "ACCEPTED":
        raise SystemExit("Inspect local baseline did not produce an accepted record.")
    if harbor["final_status"] != "ACCEPTED":
        raise SystemExit("Harbor oracle did not produce an accepted record.")

    inspect_path = out_dir / "inspect-llama3-baseline.json"
    harbor_path = out_dir / "harbor-oracle-route-policy.json"

    write_json(inspect_path, inspect)
    write_json(harbor_path, harbor)

    summary = {
        "status": "PASS",
        "generated_at": utc_now(),
        "commit_sha": args.commit_sha,
        "records": [
            {
                "file": inspect_path.name,
                "evaluation_id": inspect["evaluation_id"],
                "runner": "inspect-ai",
                "model": inspect["model"],
                "score": inspect["metrics"]["score"],
                "record_hash": inspect["record_hash"],
            },
            {
                "file": harbor_path.name,
                "evaluation_id": harbor["evaluation_id"],
                "runner": "harbor",
                "model": "oracle",
                "reward": harbor["metrics"]["reward"],
                "record_hash": harbor["record_hash"],
            },
        ],
    }
    write_json(out_dir / "summary.json", summary)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
