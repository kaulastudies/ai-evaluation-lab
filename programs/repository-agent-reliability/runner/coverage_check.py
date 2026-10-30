"""Recheck exactly the records consumed by aggregation before a GREEN demo."""
import json
from pathlib import Path
import sys

RUNNER = Path(__file__).resolve().parent
PROGRAM = RUNNER.parent
sys.path.insert(0, str(PROGRAM / "metrics"))
from aggregate import discover_attempts
from engine import evaluate_candidate, load_runtime, candidate_admission
from evidence_trust import authenticate_attempt
from security import read_confined


def main():
    attempts = discover_attempts()
    if not attempts:
        raise ValueError("No aggregation evidence found")
    passed = True
    for attempt in attempts:
        directory = PROGRAM / attempt["evidence_path"]
        record = json.loads(read_confined(directory, "evaluation.json"))
        authenticate_attempt(directory, record)
        task, config = load_runtime(record["task_id"])
        candidates = list(directory.glob("candidate-*"))
        if record["final_verdict"] == "HOLD" and not candidates:
            response = read_confined(directory, "model-response.txt").decode()
            ok = not candidate_admission(response, config["admission"])["accepted"]
        else:
            if len(candidates) != 1:
                raise ValueError("Expected one candidate for scored attempt")
            current = evaluate_candidate(task, config, candidates[0], label=record["run_label"])
            ok = current["final_verdict"] == record["final_verdict"]
        print(f"{record['run_label']}: {'PASS' if ok else 'FAIL'}")
        passed = passed and ok
    print(f"Rechecked {len(attempts)} aggregation attempts with the current controller")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
