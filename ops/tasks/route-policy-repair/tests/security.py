"""Boundaries shared by scoring and evidence readers. Fail closed by default."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import time

MAX_BYTES = 1024 * 1024
TASK_IDS = frozenset(f"AP-{i:03}" for i in range(1, 6))


def component(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}", value):
        raise ValueError("Invalid evidence path component")
    return value


def task_id(value: str) -> str:
    if value not in TASK_IDS:
        raise ValueError("Unknown task ID")
    return value


def read_confined(root: Path, relative: str | Path, limit: int = MAX_BYTES) -> bytes:
    """Open every component without following links, then read one frozen inode."""
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(p in (".", "..") for p in parts):
        raise ValueError("Path escapes evidence root")
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(leaf, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError("Evidence must be a regular file")
            data = handle.read(limit + 1)
            if len(data) > limit:
                raise ValueError("Evidence exceeds byte budget")
            return data
    finally:
        os.close(fd)


def record_digest(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "record_hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def validate_record(record: dict | None) -> None:
    if record is not None and record_digest(record) != record.get("record_hash"):
        raise ValueError("Evaluation record body does not match record_hash")


def clean_env() -> dict[str, str]:
    return {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONHASHSEED": "0"}


def kill_tree(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def bounded_run(command, *, cwd=None, env=None, timeout=30, max_output=MAX_BYTES):
    """Bound both pipes while running; communicate(timeout) alone is unbounded."""
    process = subprocess.Popen(command, cwd=cwd, env=clean_env() if env is None else env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    outputs = {process.stdout: bytearray(), process.stderr: bytearray()}
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            for stream in outputs:
                selector.register(stream, selectors.EVENT_READ)
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise RuntimeError("Child exceeded wall-time budget")
                for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                    else:
                        outputs[key.fileobj].extend(data)
                        if sum(map(len, outputs.values())) > max_output:
                            raise RuntimeError("Child exceeded output budget")
            rc = process.wait(timeout=max(0.01, deadline - time.monotonic()))
        return subprocess.CompletedProcess(command, rc, outputs[process.stdout].decode("utf-8", "replace"),
                                           outputs[process.stderr].decode("utf-8", "replace"))
    finally:
        # Also removes descendants that closed their inherited pipes.
        kill_tree(process)
        process.stdout.close()
        process.stderr.close()
