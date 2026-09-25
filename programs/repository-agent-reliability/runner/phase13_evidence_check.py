import json
import sys
from pathlib import Path

def check_phase13():
    evidence_dir = Path(__file__).resolve().parent.parent / "tasks" / "AP-001" / "evidence" / "live" / "ap001-ibm-bob-phase13-001"
    
    if not evidence_dir.is_dir():
        print("Phase 13 evidence directory not found.")
        return 1

    eval_data = json.loads((evidence_dir / "evaluation.json").read_text(encoding="utf-8"))
    replay_data = json.loads((evidence_dir / "replay-report.json").read_text(encoding="utf-8"))

    expected = {
        "candidate_sha256": "6715d71eadc4ef50b5f968010519bd01b4d27730fabe35a7c842a8063eb75b89",
        "prompt_sha256": "d8e279ed4ca5edf84757202cda2fce1ff969e14f077ee08524b0a59b3ddef5b9",
        "completion_summary_sha256": "4a141a3b6edd3176cc22c85f2f0933be8515b64598f229e5f77837509a121886",
        "evaluation_record_hash": "b4fbcec993c6c36143fadc8ba50bda123d87d5908d6057306edc3f6302e744b5",
        "final_verdict": "VERIFIED_PASS",
        "historical_source_commit": "9cd80fdcbb2334dded7ebed61ff18dd84a5159e1",
        "historical_engine_identity": "523ecc00c8c79007643cc65f735976af378bb1f2",
        "qualified_verifier_status": "QUALIFIED",
        "trusted_files_unchanged": True,
        "replay_report_status": "SOURCE_EXACT_REPLAY_VERIFIED",
        "replay_report_hash": "a0a3bed05c6562f2f57bfd65259cf470d1c7049d507a19ece4bbc444b72f4b38"
    }

    errors = []

    if eval_data.get("candidate_sha256") != expected["candidate_sha256"]:
        errors.append("Candidate hash mismatch")
    if eval_data.get("prompt_sha256") != expected["prompt_sha256"]:
        errors.append("Prompt hash mismatch")
    if eval_data.get("completion_summary_sha256") != expected["completion_summary_sha256"]:
        errors.append("Completion summary hash mismatch")
    if eval_data.get("record_hash") != expected["evaluation_record_hash"]:
        errors.append("Evaluation record hash mismatch")
    if eval_data.get("final_verdict") != expected["final_verdict"]:
        errors.append("Final verdict mismatch")
    if eval_data.get("source_commit") != expected["historical_source_commit"]:
        errors.append("Historical source commit mismatch")
    if eval_data.get("source_engine_blob") != expected["historical_engine_identity"]:
        errors.append("Historical engine identity mismatch")
    if eval_data.get("verifier_qualification", {}).get("status") != expected["qualified_verifier_status"]:
        errors.append("Qualified verifier status mismatch")
    if eval_data.get("trusted_files_unchanged") != expected["trusted_files_unchanged"]:
        errors.append("Trusted files unchanged mismatch")
        
    for gate in eval_data.get("verification", {}).get("gates", []):
        if not gate.get("passed"):
            errors.append(f"Gate {gate.get('id')} did not pass")

    if replay_data.get("status") != expected["replay_report_status"]:
        errors.append("Replay report status mismatch")
    if replay_data.get("replay_report_sha256") != expected["replay_report_hash"]:
        errors.append("Replay report hash mismatch")

    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        return 1
        
    print("Phase 13 evidence check passed.")
    return 0

if __name__ == '__main__':
    sys.exit(check_phase13())
