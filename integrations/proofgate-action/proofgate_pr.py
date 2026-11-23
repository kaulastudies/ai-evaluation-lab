"""ProofGate for pull requests.

Runs a repository's public checks and an independent verifier against the code in a
pull request, and reports one of four verdicts:

  VERIFIED_PASS  public checks and every critical verifier gate pass
  FALSE_GREEN    public checks pass, but at least one critical gate fails
  VERIFIED_FAIL  public checks fail
  HOLD           no trustworthy verdict: contract missing or invalid, verifier
                 changed by the pull request, or the verifier did not run cleanly

Trust boundary: the contract and the verifier are read from the BASE commit, never
from the pull request. A pull request that edits the trusted directory is put on
HOLD for human review instead of being judged by its own verifier.

Standard library only, so it runs on any GitHub-hosted runner without installs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

SCHEMA_VERSION = "proofgate-pr-evidence/0.1"
TOOL_VERSION = "0.1.0"
COMMENT_MARKER = "<!-- proofgate-verdict -->"
OUTPUT_LIMIT = 4000
DEFAULT_TIMEOUT = 300

VERDICT_TEXT = {
    "VERIFIED_PASS": ("✅", "Verified pass", "Public checks and every critical verifier gate passed."),
    "FALSE_GREEN": ("⚠️", "False-green caught", "Public checks passed, but the independent verifier found broken requirements."),
    "VERIFIED_FAIL": ("❌", "Verified fail", "Public checks failed."),
    "HOLD": ("⏸️", "Hold for review", "ProofGate could not reach a trustworthy verdict."),
}


class ContractError(Exception):
    pass


def git(repo: Path, *args: str, binary: bool = False):
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout if binary else result.stdout.decode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tail(text: str) -> str:
    return text if len(text) <= OUTPUT_LIMIT else "…" + text[-OUTPUT_LIMIT:]


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, p) or path == p.rstrip("/") for p in patterns)


def load_contract(repo: Path, base: str, contract_path: str) -> tuple[dict, bytes]:
    try:
        raw = git(repo, "show", f"{base}:{contract_path}", binary=True)
    except RuntimeError as exc:
        raise ContractError(
            f"No contract at {contract_path} on the base commit. "
            "Add it to the base branch first so the pull request cannot write its own rules."
        ) from exc
    try:
        contract = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractError(f"Contract is not valid JSON: {exc}") from exc

    for key in ("task_id", "trusted_dir", "public_checks", "verifier", "gates"):
        if key not in contract:
            raise ContractError(f"Contract is missing '{key}'")
    if not contract["gates"] or not all("id" in g for g in contract["gates"]):
        raise ContractError("Contract must declare at least one gate, each with an id")
    if contract["verifier"].get("format", "json-gates") != "json-gates":
        raise ContractError("Only verifier format 'json-gates' is supported")
    return contract, raw


def export_trusted(repo: Path, base: str, trusted_dir: str, dest: Path) -> Path:
    """Extract the trusted directory exactly as it exists on the base commit."""
    archive = git(repo, "archive", "--format=tar", base, trusted_dir, binary=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            target = (dest / member.name).resolve()
            if not str(target).startswith(str(dest.resolve())) or member.issym() or member.islnk():
                raise ContractError(f"Unsafe path in trusted directory: {member.name}")
        if hasattr(tarfile, "data_filter"):
            tar.extractall(dest, filter="data")
        else:
            tar.extractall(dest)
    return dest / trusted_dir


def run_command(cmd: str, cwd: Path, trusted: Path, timeout: int) -> dict:
    expanded = cmd.replace("{trusted}", shlex.quote(str(trusted)))
    started = time.monotonic()
    env = {k: v for k, v in os.environ.items() if k != "GITHUB_TOKEN"}
    env["PROOFGATE_TRUSTED_DIR"] = str(trusted)
    try:
        proc = subprocess.run(
            expanded, cwd=cwd, shell=True, capture_output=True, text=True,
            timeout=timeout, env=env,
        )
        return {
            "command": cmd,
            "exit_code": proc.returncode,
            "timed_out": False,
            "seconds": round(time.monotonic() - started, 3),
            "stdout_tail": tail(proc.stdout),
            "stderr_tail": tail(proc.stderr),
            "_stdout": proc.stdout,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "exit_code": None,
            "timed_out": True,
            "seconds": round(time.monotonic() - started, 3),
            "stdout_tail": tail(exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")),
            "stderr_tail": tail(exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")),
            "_stdout": "",
        }


def parse_gates(stdout: str, declared: list[dict]) -> tuple[list[dict], str | None]:
    """Read verifier JSON and line it up with the gates the contract declared."""
    payload = None
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                payload = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if payload is None or not isinstance(payload.get("gates"), list):
        return [], "Verifier did not print a JSON object with a 'gates' list"

    reported = {g.get("id"): g for g in payload["gates"] if isinstance(g, dict)}
    results = []
    for g in declared:
        hit = reported.get(g["id"])
        results.append({
            "id": g["id"],
            "description": g.get("description", ""),
            "critical": bool(g.get("critical", True)),
            "reported": hit is not None,
            "passed": bool(hit and hit.get("passed") is True),
            "diagnostic": (hit or {}).get("diagnostic", "gate not reported by verifier"),
        })
    missing = [r["id"] for r in results if not r["reported"]]
    if missing:
        return results, f"Verifier did not report declared gates: {', '.join(missing)}"
    return results, None


def decide(trust_violations, public, verifier_error, gates) -> tuple[str, str]:
    if trust_violations:
        return "HOLD", "This pull request changes the trusted verifier or contract, so it cannot be judged by them. A reviewer must approve those changes separately."
    if any(c["timed_out"] or c["exit_code"] is None for c in public):
        return "HOLD", "A public check timed out."
    if any(c["exit_code"] != 0 for c in public):
        return "VERIFIED_FAIL", "At least one public check failed."
    if verifier_error:
        return "HOLD", verifier_error
    failed = [g["id"] for g in gates if g["critical"] and not g["passed"]]
    if failed:
        return "FALSE_GREEN", f"Public checks passed, but {len(failed)} critical gate(s) failed: {', '.join(failed)}."
    return "VERIFIED_PASS", "Public checks and all critical gates passed."


def evaluate(repo: Path, base: str, head: str, contract_path: str, timeout: int) -> dict:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    record = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "started_at": started_at,
        "base_sha": base,
        "head_sha": head,
        "contract_path": contract_path,
    }
    try:
        contract, raw = load_contract(repo, base, contract_path)
    except ContractError as exc:
        record.update(verdict="HOLD", reason=str(exc), gates=[], public_checks=[], changed_files=[])
        return record

    record["task_id"] = contract["task_id"]
    record["title"] = contract.get("title", "")
    record["contract_sha256"] = sha256(raw)

    merge_base = git(repo, "merge-base", base, head).strip()
    changed = [p for p in git(repo, "diff", "--name-only", f"{merge_base}..{head}").splitlines() if p]
    trusted_dir = contract["trusted_dir"].rstrip("/")
    trusted_patterns = [trusted_dir + "/*", trusted_dir, contract_path]
    allowed = contract.get("allowed_paths", [])
    record["changed_files"] = changed
    record["trust_violations"] = [p for p in changed if matches(p, trusted_patterns)]
    record["outside_allowed_paths"] = [p for p in changed if allowed and not matches(p, allowed)] if allowed else []

    with tempfile.TemporaryDirectory(prefix="proofgate-trusted-") as tmp:
        try:
            trusted = export_trusted(repo, base, trusted_dir, Path(tmp))
        except (ContractError, RuntimeError) as exc:
            record.update(verdict="HOLD", reason=f"Could not load trusted verifier from base: {exc}", gates=[], public_checks=[])
            return record
        record["trusted_files_sha256"] = {
            str(p.relative_to(trusted)): sha256(p.read_bytes())
            for p in sorted(trusted.rglob("*")) if p.is_file()
        }

        public = []
        for check in contract["public_checks"]:
            res = run_command(check["run"], repo / check.get("cwd", "."), trusted, int(check.get("timeout", timeout)))
            res["id"] = check.get("id", check["run"])
            public.append(res)

        v = contract["verifier"]
        vres = run_command(v["run"], repo / v.get("cwd", "."), trusted, int(v.get("timeout", timeout)))
        verifier_error = None
        gates: list[dict] = []
        if vres["timed_out"]:
            verifier_error = "Verifier timed out."
        else:
            gates, verifier_error = parse_gates(vres["_stdout"], contract["gates"])

    for item in public + [vres]:
        item.pop("_stdout", None)
    verdict, reason = decide(record["trust_violations"], public, verifier_error, gates)
    record.update(public_checks=public, verifier_run=vres, gates=gates, verdict=verdict, reason=reason)
    record["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return record


def render_markdown(record: dict, evidence_sha: str, run_url: str | None) -> str:
    icon, label, blurb = VERDICT_TEXT[record["verdict"]]
    lines = [
        COMMENT_MARKER,
        f"## {icon} ProofGate: {label}",
        "",
        f"**{record['reason']}**",
        "",
    ]
    if record.get("task_id"):
        lines.append(f"Contract: `{record['task_id']}`" + (f" ({record['title']})" if record.get("title") else ""))
        lines.append("")
    if record.get("public_checks"):
        lines += ["| Check | Result |", "|---|---|"]
        for c in record["public_checks"]:
            ok = c["exit_code"] == 0 and not c["timed_out"]
            lines.append(f"| Public: `{c['id']}` | {'✓ pass' if ok else '✗ fail'} |")
        for g in record.get("gates", []):
            mark = "✓ pass" if g["passed"] else "✗ fail"
            crit = "" if g["critical"] else " (non-critical)"
            lines.append(f"| `{g['id']}`{crit}: {g['description']} | {mark} |")
        lines.append("")
    if record.get("trust_violations"):
        lines.append("Trusted files changed in this pull request: " + ", ".join(f"`{p}`" for p in record["trust_violations"]))
        lines.append("")
    if record.get("outside_allowed_paths"):
        lines.append("Changed outside the contract's allowed paths: " + ", ".join(f"`{p}`" for p in record["outside_allowed_paths"]))
        lines.append("")
    footer = f"Head `{record['head_sha'][:7]}` · base `{record['base_sha'][:7]}` · evidence sha256 `{evidence_sha[:16]}…`"
    if run_url:
        footer += f" · [run and evidence]({run_url})"
    lines += [f"<sub>{footer}<br>Verifier and contract were read from the base commit. ProofGate by AI Evaluation Lab.</sub>"]
    return "\n".join(lines) + "\n"


def post_comment(body: str) -> str:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not (token and repo and event_path):
        return "skipped: not running in a GitHub pull request"
    event = json.loads(Path(event_path).read_text())
    number = (event.get("pull_request") or {}).get("number")
    if not number:
        return "skipped: event is not a pull request"
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "proofgate-action",
    }

    def call(method: str, url: str, payload: dict | None = None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read() or b"null")

    try:
        existing = None
        page = 1
        while existing is None:
            batch = call("GET", f"{api}/repos/{repo}/issues/{number}/comments?per_page=100&page={page}")
            if not batch:
                break
            existing = next((c for c in batch if COMMENT_MARKER in (c.get("body") or "")), None)
            page += 1
        if existing:
            call("PATCH", f"{api}/repos/{repo}/issues/comments/{existing['id']}", {"body": body})
            return "updated"
        call("POST", f"{api}/repos/{repo}/issues/{number}/comments", {"body": body})
        return "created"
    except urllib.error.HTTPError as exc:
        return f"skipped: GitHub API returned {exc.code} (forked pull requests get a read-only token)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--base", required=True, help="base commit sha or ref")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--contract", default=".proofgate/contract.json")
    ap.add_argument("--evidence", type=Path, default=Path("proofgate-evidence.json"))
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    ap.add_argument("--comment", action="store_true", help="post or update the verdict comment on the pull request")
    ap.add_argument("--fail-on", default="FALSE_GREEN,VERIFIED_FAIL,HOLD",
                    help="comma-separated verdicts that make the job fail")
    args = ap.parse_args(argv)

    repo = args.repo.resolve()
    head = git(repo, "rev-parse", args.head).strip()
    base = git(repo, "rev-parse", args.base).strip()
    record = evaluate(repo, base, head, args.contract, args.timeout)

    body = json.dumps(record, indent=2, ensure_ascii=False).encode() + b"\n"
    args.evidence.write_bytes(body)
    evidence_sha = sha256(body)

    run_url = None
    if os.environ.get("GITHUB_RUN_ID"):
        run_url = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    markdown = render_markdown(record, evidence_sha, run_url)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(markdown)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write(f"verdict={record['verdict']}\nevidence-sha256={evidence_sha}\n")

    print(markdown)
    if args.comment:
        print(f"PR comment: {post_comment(markdown)}")

    fail_on = {v.strip() for v in args.fail_on.split(",") if v.strip()}
    return 1 if record["verdict"] in fail_on else 0


if __name__ == "__main__":
    sys.exit(main())
