from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import uuid


VERIFIER_VERSION = "0.1.0"


class DeferredFetcher:
    def __init__(self):
        self.callbacks = {}

    def __call__(self, resource, callback):
        self.callbacks[resource] = callback

    def resolve(self, resource, value):
        self.callbacks.pop(resource)(value)


def load_resource_view(candidate_root: Path):
    module_path = candidate_root / "app" / "resource_view.py"
    if not module_path.is_file():
        raise FileNotFoundError(f"candidate missing {module_path}")
    module_name = f"ap001_candidate_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.ResourceView


def evaluate(candidate_root: Path):
    ResourceView = load_resource_view(candidate_root)
    gates = []

    # G03: ordinary behavior.
    fetcher = DeferredFetcher()
    view = ResourceView()
    view.select_resource("alpha", fetcher)
    fetcher.resolve("alpha", "ALPHA")
    g03 = view.current_resource == "alpha" and view.value == "ALPHA"
    gates.append({
        "id": "AP001-G03",
        "passed": g03,
        "diagnostic": "ordinary single-resource behavior preserved" if g03
        else "ordinary single-resource behavior regressed",
    })

    # G01/G02: overlapping requests, newer response resolves first.
    fetcher = DeferredFetcher()
    view = ResourceView()
    view.select_resource("alpha", fetcher)
    view.select_resource("beta", fetcher)

    fetcher.resolve("beta", "BETA")
    g01 = view.current_resource == "beta" and view.value == "BETA"
    gates.append({
        "id": "AP001-G01",
        "passed": g01,
        "diagnostic": "newer response committed correctly" if g01
        else "newer response did not commit correctly",
    })

    fetcher.resolve("alpha", "ALPHA")
    g02 = view.current_resource == "beta" and view.value == "BETA"
    gates.append({
        "id": "AP001-G02",
        "passed": g02,
        "diagnostic": "superseded response was ignored" if g02
        else "superseded alpha response overwrote beta state",
    })

    return {
        "task_id": "AP-001",
        "task_version": "0.1.0",
        "verifier_version": VERIFIER_VERSION,
        "candidate": str(candidate_root),
        "gates": gates,
        "status": "VERIFIED_PASS" if all(g["passed"] for g in gates) else "VERIFIED_FAIL",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = evaluate(args.candidate_root.resolve())
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['status']}  task={result['task_id']} verifier={result['verifier_version']}")
        for gate in result["gates"]:
            mark = "PASS" if gate["passed"] else "FAIL"
            print(f"  {gate['id']}: {mark} - {gate['diagnostic']}")

    return 0 if result["status"] == "VERIFIED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
