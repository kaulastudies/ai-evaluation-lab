"""Execution wrapper for authenticated historical evidence only.

Historical verifiers have a weaker in-process boundary, so callers must pin the
entire evidence package before invoking this wrapper. No new packages qualify.
"""
from pathlib import Path
import shutil
import subprocess

from security import bounded_run, clean_env


def run_historical(command, *, source_root, writable_root, cwd, env=None, extra_readonly=()):
    if not shutil.which("bwrap") or not shutil.which("prlimit"):
        raise RuntimeError("Historical replay requires bubblewrap and prlimit")
    source_root = Path(source_root).resolve()
    writable_root = Path(writable_root).resolve()
    if source_root.parent != writable_root:
        raise ValueError("Historical output must be in the private replay directory")
    head = subprocess.run(["git", "rev-parse", "HEAD"],
                            cwd=source_root, env=clean_env(), capture_output=True, text=True, check=True, timeout=5).stdout.strip()
    # Historical runners only need their HEAD identity and hash-object. Never
    # mount the operator's .git directory: its config may contain access tokens.
    metadata = writable_root / "git-identity"
    metadata.mkdir()
    (metadata / "objects").mkdir()
    (metadata / "refs").mkdir()
    (metadata / "HEAD").write_text(head + "\n")
    (metadata / "config").write_text("[core]\nrepositoryformatversion = 0\nbare = true\n")
    sandbox = ["prlimit", "--cpu=45", "--as=1073741824", "--fsize=10485760", "--nofile=128",
               "bwrap", "--unshare-all", "--die-with-parent", "--new-session", "--clearenv", "--cap-drop", "ALL",
               "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib"]
    if Path("/lib64").exists():
        sandbox += ["--ro-bind", "/lib64", "/lib64"]
    sandbox += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                "--bind", str(writable_root), str(writable_root),
                "--ro-bind", str(source_root), str(source_root),
                "--ro-bind", str(metadata), str(metadata)]
    for path in extra_readonly:
        sandbox += ["--ro-bind", str(path), str(path)]
    for key, value in (env or clean_env()).items():
        if key not in {"PATH", "LANG", "PYTHONHASHSEED", "PYTHONPATH"}:
            raise ValueError("Unexpected historical environment variable")
        sandbox += ["--setenv", key, value]
    sandbox += ["--setenv", "GIT_DIR", str(metadata), "--setenv", "GIT_CONFIG_NOSYSTEM", "1"]
    sandbox += ["--chdir", str(cwd), "/usr/bin/python3", *command[1:]]
    return bounded_run(sandbox, cwd=cwd, timeout=60)
