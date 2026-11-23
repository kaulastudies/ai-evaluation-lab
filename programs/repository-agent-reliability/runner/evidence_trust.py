"""Reviewed historical artifacts, pinned outside submitted evidence packages.

These anchors authenticate existing evidence only, not new security claims.
Updating them requires review alongside the changed artifacts.
"""
import hashlib
import json
from pathlib import Path
from security import read_confined, validate_record, component, task_id

PROGRAM_ROOT = Path(__file__).resolve().parents[1]
ANCHORS_SHA256 = "2d611c5f13df44352087f77d1b61607c7d19c43c2452253d87b598dc04c0ecdd"


def anchors():
    raw = read_confined(Path(__file__).parent, "evidence-anchors.json", 2 * 1024 * 1024)
    if hashlib.sha256(raw).hexdigest() != ANCHORS_SHA256:
        raise ValueError("Trusted evidence inventory changed")
    return json.loads(raw)


def authenticate_directory(directory, prefix):
    inventory = anchors()
    expected = {p[len(prefix)+1:]: digest for p, digest in inventory.items() if p.startswith(prefix + "/")}
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    if not expected or actual != set(expected):
        raise ValueError("Evidence inventory is not the reviewed historical inventory")
    snapshot = {}
    for relative, digest in expected.items():
        snapshot[relative] = read_confined(directory, relative)
        if hashlib.sha256(snapshot[relative]).hexdigest() != digest:
            raise ValueError("Evidence differs from reviewed historical artifact: " + relative)
    return snapshot


def authenticate_attempt(directory, record):
    task_id(record["task_id"])
    component(record["run_label"])
    digest = hashlib.sha256(read_confined(directory, "evaluation.json")).hexdigest()
    matches = [path.rsplit("/", 1)[0] for path, value in anchors().items()
               if path.endswith("/evaluation.json") and value == digest]
    if len(matches) != 1:
        raise ValueError("Evaluation is not a reviewed historical record")
    prefix = matches[0]
    snapshot = authenticate_directory(directory, prefix)
    if json.loads(snapshot["evaluation.json"]) != record:
        raise ValueError("Evaluation changed while authenticating the package")
    evaluation = record.get("evaluation")
    if record.get("runtime_schema") == "agent-workspace-v1":
        validate_record(record)
    else:
        validate_record(evaluation)
    return snapshot


def validate_response(record, manifest, data):
    digest = hashlib.sha256(data).hexdigest()
    if digest != record.get("model_response_sha256") or digest != manifest.get("response_sha256"):
        raise ValueError("Response identity mismatch before execution")
    if len(data) != manifest.get("response_bytes"):
        raise ValueError("Response length mismatch before execution")
    validate_record(record.get("evaluation"))
