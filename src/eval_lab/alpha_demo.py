from __future__ import annotations
import argparse, json
from pathlib import Path
from eval_lab.pipeline import evaluate
from eval_lab.providers.mock import MockProvider
from eval_lab.tasks import load_tasks

def run(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    records, provider = [], MockProvider()
    for task in load_tasks(Path("examples")/"tasks"):
        primary = evaluate(task, provider)
        records.append(primary)
        if task.regression_response is not None:
            records.append(evaluate(task, provider, run_label="regression", response_override=task.regression_response, regression_of=primary["evaluation_id"]))
    for i, record in enumerate(records, 1):
        (output/f"{i:02d}-{record['task_id'].lower()}-{record['run_label']}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    summary = {
        "records": len(records),
        "accepted": sum(r["final_status"]=="ACCEPTED" for r in records),
        "needs_edit": sum(r["final_status"]=="NEEDS_EDIT" for r in records),
        "rejected": sum(r["final_status"]=="REJECTED" for r in records),
        "disagreements": sum(bool(r["disagreement"]) for r in records),
        "regressions": sum(r["run_label"]=="regression" for r in records),
    }
    (output/"summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    return records

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output", default="runs/alpha"); a=p.parse_args()
    records=run(Path(a.output)); print(f"Wrote {len(records)} evaluation records to {a.output}")
if __name__=="__main__": main()
