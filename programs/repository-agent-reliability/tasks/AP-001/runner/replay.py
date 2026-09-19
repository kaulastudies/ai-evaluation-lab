from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


BUNDLE_ROOT = Path(__file__).resolve().parent


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(record: dict) -> str:
    payload = {k: v for k, v in record.items() if k != "record_hash"}
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_verification(raw: dict) -> dict:
    return {
        "task_id": raw["task_id"],
        "task_version": raw["task_version"],
        "verifier_version": raw["verifier_version"],
        "candidate": "workspace",
        "gates": raw["gates"],
        "status": raw["status"],
    }


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def main() -> int:
    manifest = json.loads(
        (BUNDLE_ROOT / "manifest.json").read_text(encoding="utf-8")
    )
    record = json.loads(
        (BUNDLE_ROOT / "evaluation_record.json").read_text(encoding="utf-8")
    )

    expected_files = manifest["files"]
    hash_failures: list[str] = []

    for relative, expected_hash in sorted(expected_files.items()):
        path = BUNDLE_ROOT / relative
        if not path.is_file():
            hash_failures.append(f"{relative}: missing")
            continue
        actual = sha256_file(path)
        if actual != expected_hash:
            hash_failures.append(
                f"{relative}: expected {expected_hash}, actual {actual}"
            )

    if hash_failures:
        print("HASH VALIDATION FAILED")
        for failure in hash_failures:
            print(f"  {failure}")
        return 2

    record_hash_ok = canonical_hash(record) == record.get("record_hash")

    candidate_root = BUNDLE_ROOT / "candidate"
    public = run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests/public",
            "-v",
        ],
        candidate_root,
    )
    public_passed = public.returncode == 0
    public_match = (
        public_passed
        == bool(record["public_validation"]["passed"])
    )

    verifier_process = run(
        [
            sys.executable,
            str(BUNDLE_ROOT / "verifier" / "acceptance.py"),
            str(candidate_root),
            "--json",
        ],
        BUNDLE_ROOT,
    )

    try:
        raw_verification = json.loads(verifier_process.stdout)
    except json.JSONDecodeError:
        print("VERIFIER OUTPUT WAS NOT VALID JSON")
        print(verifier_process.stdout)
        print(verifier_process.stderr, file=sys.stderr)
        return 3

    verification = normalize_verification(raw_verification)
    verifier_match = verification == record["verification"]

    candidate_hash_ok = (
        sha256_file(BUNDLE_ROOT / "candidate" / "app" / "resource_view.py")
        == record["candidate_sha256"]
    )
    task_hash_ok = (
        sha256_file(BUNDLE_ROOT / "task.yaml")
        == record["task_contract_sha256"]
    )
    verifier_hash_ok = (
        sha256_file(BUNDLE_ROOT / "verifier" / "acceptance.py")
        == record["verifier_source_sha256"]
    )
    qualification_hash_ok = (
        sha256_file(
            BUNDLE_ROOT / "evidence" / "verifier-qualification.json"
        )
        == record["qualification_evidence_sha256"]
    )

    replay_verdict = verification["status"]
    verdict_match = replay_verdict == record["final_verdict"]

    replay_false_green = bool(
        record["agent_claimed_success"]
        and public_passed
        and replay_verdict == "VERIFIED_FAIL"
    )
    false_green_match = replay_false_green == record["false_green"]

    checks = {
        "manifest_hashes": True,
        "record_hash": record_hash_ok,
        "candidate_hash": candidate_hash_ok,
        "task_contract_hash": task_hash_ok,
        "verifier_source_hash": verifier_hash_ok,
        "qualification_evidence_hash": qualification_hash_ok,
        "public_result_match": public_match,
        "verifier_result_match": verifier_match,
        "final_verdict_match": verdict_match,
        "false_green_match": false_green_match,
    }

    print(json.dumps(checks, indent=2))
    ok = all(checks.values())

    if ok:
        print(
            "REPLAY VERIFIED "
            f"task={record['task_id']} "
            f"verdict={record['final_verdict']} "
            f"record_hash={record['record_hash']}"
        )
        return 0

    print("REPLAY MISMATCH")
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
