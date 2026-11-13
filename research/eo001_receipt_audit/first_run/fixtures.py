"""Produce labelled test-double evidence using the unchanged pinned v2 recorder."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from ..durable.harness import ProviderLab
from ..durable.runner import run_candidate
from .review import FAULTS, MODEL_SHA, RUNTIME_SHA, review

HERE = Path(__file__).resolve().parent


def verify_source(source):
    lock = json.loads((HERE / "source_lock.json").read_text())
    for name, expected in lock["files"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError("SOURCE_HASH_MISMATCH: " + name)
    return lock


def generate(source):
    lock = verify_source(source)
    result = {"fixture": True, "inference_source": "TEST_DOUBLE_ONLY", "upstream": lock,
              "sessions": {}, "receipts": []}
    with tempfile.TemporaryDirectory(prefix="eo-first-run-fixture-") as temporary:
        root = Path(temporary)
        for fault in FAULTS:
            receipts = root / (fault + "-receipts")
            receipts.mkdir()
            mode = "unsafe_retry" if fault == "ack_loss" else "safe"
            result["sessions"][fault] = run_candidate(
                ["node", str(HERE / "fixture_candidate.mjs"), str(source), str(receipts), mode],
                ProviderLab(root / (fault + "-provider")), fault)
            result["receipts"].extend(json.loads(p.read_text()) for p in sorted(receipts.glob("*.json")))
        error_receipts = root / "error-receipts"
        error_receipts.mkdir()
        result["error_session"] = run_candidate(
            ["node", str(HERE / "fixture_candidate.mjs"), str(source), str(error_receipts), "error"],
            ProviderLab(root / "error-provider"))
        result["error_receipt"] = json.loads(next(error_receipts.glob("*.json")).read_text())
        withheld_receipts = root / "withheld-receipts"
        withheld_receipts.mkdir()
        result["withheld_session"] = run_candidate(
            ["node", str(HERE / "fixture_candidate.mjs"), str(source), str(withheld_receipts), "withhold_confirmed"],
            ProviderLab(root / "withheld-provider"))
        result["withheld_receipts"] = [json.loads(p.read_text()) for p in withheld_receipts.glob("*.json")]
    result["readiness"] = {"schema": "evercraft.eo001.sovereign-inference-acceptance.v1",
        "state": "FIRST_INFERENCE_BLOCKED", "real_local_inference": False,
        "model_sha256": MODEL_SHA, "runtime_sha256": RUNTIME_SHA,
        "production_services_modified": False, "synthetic_only": True, "child_processes_stopped": True,
        "error": "RuntimeError: missing_runtime_libraries: libgomp.so.1 (synthetic fixture)"}
    result["review"] = review(result["sessions"], result["receipts"], result["readiness"])
    assert result["review"]["evidence_coverage"] == "MATCHED", result["review"]["problems"]
    assert result["review"]["model_decision_counts"] == {"safe": 8, "unsafe": 1}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = generate(args.source.resolve())
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"fixture_only": True, "review": evidence["review"]["model_decision_counts"]}))


if __name__ == "__main__":
    main()
