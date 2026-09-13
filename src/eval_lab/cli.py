from __future__ import annotations
import argparse, json
from eval_lab.pipeline import evaluate
from eval_lab.providers.http import provider_from_name
from eval_lab.providers.mock import MockProvider
from eval_lab.tasks import load_task

def main():
    p=argparse.ArgumentParser(); p.add_argument("task"); p.add_argument("--provider", default="mock"); a=p.parse_args()
    task=load_task(a.task); provider=MockProvider() if a.provider=="mock" else provider_from_name(a.provider)
    print(json.dumps(evaluate(task, provider), ensure_ascii=False, indent=2))
if __name__=="__main__": main()
