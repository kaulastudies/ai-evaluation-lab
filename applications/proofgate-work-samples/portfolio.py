"""Export bounded RARB work samples; this does not assess a person's skill."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess

REPO = Path(__file__).resolve().parents[2]
BASE = "programs/repository-agent-reliability/tasks"
ORIGIN = "https://github.com/kaulastudies/ai-evaluation-lab"
PIN = "19ab17439f24a5b010e7136e37ba505d23785225"
RUNS = ("ap005-ollama-llama3-001", "ap005-ollama-llama3-002-repair")
BOUNDARY = (
    "This packet documents a software artifact and a self-reported contribution. "
    "It does not verify identity, authorship, independent ability, qualifications, "
    "or suitability for employment. These public practice samples can be studied "
    "and copied; they are unsuitable as a secret or proctored hiring test."
)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def blob(ref: str, path: str, repo: Path = REPO) -> bytes:
    if not re.fullmatch(r"[a-f0-9]{40}", ref):
        raise ValueError("An immutable 40-character Git commit is required")
    result = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=repo,
                            capture_output=True, check=True)
    return result.stdout


def sample(run: str, repo: Path = REPO) -> dict:
    # Restrict this initial release to two public, synthetic AP-005 examples.
    # Read Git objects, never candidate code; exporting cannot execute a patch.
    if run not in RUNS:
        raise ValueError("Unknown practice run")
    path = f"{BASE}/AP-005/evidence/live/{run}"
    files = {name: blob(PIN, f"{path}/{name}", repo) for name in
             ("evaluation.json", "manifest.json", "model-response.txt",
              "candidate-record_transformer.py", "replay-report.json")}
    trial = json.loads(files["evaluation.json"])
    manifest = json.loads(files["manifest.json"])
    replay = json.loads(files["replay-report.json"])
    evaluation = trial["evaluation"]
    record_hash = evaluation["record_hash"]
    payload = {k: v for k, v in evaluation.items() if k != "record_hash"}
    checks = [digest(canonical(payload)) == record_hash,
              trial["run_label"] == manifest["run_label"] == replay["run_label"] == run,
              trial["source_commit"] == manifest["source_commit"] == replay["source_commit"],
              digest(files["model-response.txt"]) == manifest["response_sha256"],
              len(files["model-response.txt"]) == manifest["response_bytes"],
              digest(files["candidate-record_transformer.py"]) == manifest["candidate_sha256"],
              trial["candidate_sha256"] == manifest["candidate_sha256"],
              record_hash == manifest["evaluation_record_hash"] == replay["stored_record_hash"] == replay["replayed_record_hash"],
              trial["final_verdict"] == evaluation["final_verdict"] == manifest["final_verdict"] == replay["replayed_verdict"],
              bool(replay["checks"]) and all(v is True for v in replay["checks"].values())]
    if not all(checks):
        raise ValueError(f"Evidence is inconsistent for {run}")
    replay_payload = {k: v for k, v in replay.items() if k != "replay_report_sha256"}
    if digest(canonical(replay_payload)) != replay["replay_report_sha256"]:
        raise ValueError("Stored replay report hash does not match")
    return {
        "task": "AP-005", "run": run,
        "verdict": trial["final_verdict"],
        "public_tests_passed": evaluation["public_validation"]["passed"],
        "false_green": evaluation["false_green"],
        "gates": evaluation["verification"]["gates"],
        "record_hash": record_hash,
        "evidence_commit": PIN,
        "evaluator_commit": trial["source_commit"],
        "evidence_url": f"{ORIGIN}/tree/{PIN}/{path}",
        "task_url": f"{ORIGIN}/blob/{PIN}/{BASE}/AP-005/agent_brief.md",
        "model": manifest["model"], "provider": manifest["provider"],
        "code_origin": "Recorded AI-generated candidate; not claimant-authored code",
        "artifact_hashes": {name: digest(data) for name, data in files.items()},
        "integrity_status": "MATCHED_PINNED_PUBLIC_EVIDENCE",
        "replay_status": "Stored historical source-exact replay; export does not rerun the verifier",
    }


def declaration(value: dict) -> dict:
    if set(value) != {"alias", "contribution", "ai_assistance", "sharing_consent"}:
        raise ValueError("Declaration needs exactly alias, contribution, ai_assistance, sharing_consent")
    for key, limit in (("alias", 80), ("contribution", 2000), ("ai_assistance", 1000)):
        if not isinstance(value[key], str) or not value[key].strip() or len(value[key]) > limit:
            raise ValueError(f"Invalid {key}")
    if value["sharing_consent"] is not True:
        raise ValueError("Export requires explicit consent to include the declaration")
    return dict(value)


def packet(details: dict, runs: list[str], repo: Path = REPO) -> dict:
    if not runs or len(runs) != len(set(runs)):
        raise ValueError("Choose at least one run; do not duplicate a sample")
    if RUNS[1] in runs:
        # A successful repair must retain its earlier failed attempt.
        runs = list(RUNS)
    result = {"schema": "proofgate-work-sample/0.1", "declaration": declaration(details),
              "declaration_status": "SELF_REPORTED_NOT_IDENTITY_VERIFIED",
              "samples": [sample(run, repo) for run in runs], "boundary": BOUNDARY,
              "employment_outcomes": "No measured employment or income outcomes"}
    result["packet_sha256"] = digest(canonical(result))
    return result


def verify(value: dict, repo: Path = REPO) -> None:
    # A matching unkeyed hash alone is insufficient: reconstruct from pinned Git.
    expected = packet(value["declaration"], [s["run"] for s in value["samples"]], repo)
    if value != expected:
        raise ValueError("Packet differs from its declaration and pinned evidence")


def render(value: dict) -> str:
    e = lambda x: html.escape(str(x), quote=True)
    d = value["declaration"]
    cards = []
    for s in value["samples"]:
        gates = "".join(f"<li>{e(g['id'])}: {'PASS' if g['passed'] else 'FAIL'} — {e(g['diagnostic'])}</li>" for g in s["gates"])
        cards.append(f"<article><p class='eyebrow'>PUBLIC PRACTICE SAMPLE · {e(s['task'])}</p><h2>{e(s['verdict'])}</h2>"
                     f"<p>Public tests passed: {e(s['public_tests_passed'])} · False green: {e(s['false_green'])}</p>"
                     f"<ul>{gates}</ul><p>{e(s['code_origin'])}; {e(s['provider'])} / {e(s['model'])}.</p>"
                     f"<p><a href='{e(s['task_url'])}'>Read the task</a> · <a href='{e(s['evidence_url'])}'>Inspect the original evidence</a></p>"
                     f"<p class='muted'>{e(s['replay_status'])}</p><p class='hash'>Evaluation hash: {e(s['record_hash'])}</p></article>")
    return f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<meta http-equiv='Content-Security-Policy' content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>ProofGate Work Samples — {e(d['alias'])}</title>
<style>body{{font:17px/1.6 system-ui;background:#f3f5f8;color:#152237;margin:0}}main{{max-width:900px;margin:48px auto;padding:0 24px}}h1{{font-size:42px;line-height:1.1}}h2{{font-size:24px}}article,.panel{{background:white;border:1px solid #ccd5df;border-radius:12px;padding:24px;margin:24px 0}}.eyebrow{{font-size:12px;letter-spacing:.1em;color:#215e66}}a{{color:#145c9e}}.hash{{font:12px/1.6 ui-monospace;overflow-wrap:anywhere}}.muted{{color:#526273;font-size:14px}}.notice{{border-left:5px solid #b66a17;padding:16px;background:#fff4dd}}p{{white-space:pre-wrap}}@media(max-width:600px){{h1{{font-size:32px}}main{{margin:24px auto}}article{{padding:16px}}}}</style>
<main><p class='eyebrow'>AI EVALUATION LAB · EARLY PROTOTYPE · 4 NOVEMBER 2026</p><h1>Show the work.<br>Keep the evidence.</h1>
<p>Portable work-sample evidence for a conversation with a human reviewer.</p><p class='notice'>{e(BOUNDARY)}</p>
<section class='panel'><h2>{e(d['alias'])}</h2><p><b>Declared contribution</b> — self-reported</p><p>{e(d['contribution'])}</p>
<p><b>AI assistance</b> — self-reported</p><p>{e(d['ai_assistance'])}</p></section>
{''.join(cards)}<section class='panel'><h2>What can a reviewer check?</h2><p>The packet matches the pinned public records. The initial patch failed the independent checks despite passing public tests. The later AI-generated repair passed those checks. Ask the person to explain this difference and discuss a separate, consented work sample.</p>
<p>Practice access is free. There is no ranking, hiring decision, identity check or job placement service in this prototype.</p>
<p class='hash'>Packet SHA-256: {e(value['packet_sha256'])}</p><p class='muted'>A hash detects changes relative to a trusted copy. It is not a signature or proof of authorship. Personal declarations stay in the local export; this tool has no network upload.</p></section></main></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--declaration", type=Path, required=True)
    export.add_argument("--run", choices=RUNS, action="append")
    export.add_argument("--out", type=Path, required=True)
    check = commands.add_parser("verify")
    check.add_argument("packet", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "verify":
            verify(json.loads(args.packet.read_text(encoding="utf-8")))
            print("MATCHED_PINNED_PUBLIC_EVIDENCE; self-reported contribution remains unverified")
        else:
            result = packet(json.loads(args.declaration.read_text(encoding="utf-8")), args.run or list(RUNS))
            args.out.mkdir(parents=True, exist_ok=True)
            for name in ("packet.json", "index.html"):
                if (args.out / name).exists():
                    raise ValueError("Output already exists; choose a new directory")
            (args.out / "packet.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            (args.out / "index.html").write_text(render(result), encoding="utf-8")
            print("Exported packet.json and index.html; nothing uploaded")
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Unable to complete: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
