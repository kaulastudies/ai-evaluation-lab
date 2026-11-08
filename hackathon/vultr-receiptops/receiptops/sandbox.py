"""Disposable Docker execution. There is deliberately no host-execution fallback."""
import os
import selectors
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.12-slim")
POLICY = {"network": "none", "read_only_root": True, "user": "65534:65534",
          "capabilities": "all dropped", "no_new_privileges": True,
          "memory_mib": 128, "cpu": "0.5", "pids": 32,
          "timeout_seconds": 8, "output_bytes": 65536, "tmpfs_mib": 16}

def available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        result = subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True, timeout=4)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False

def command(name: str, folder: Path) -> list[str]:
    return ["docker", "run", "--name", name, "--pull=never", "--network=none", "--read-only",
            "--user=65534:65534", "--cap-drop=ALL", "--security-opt=no-new-privileges",
            "--memory=128m", "--memory-swap=128m", "--cpus=0.5", "--pids-limit=32",
            "--ulimit", "nofile=64:64", "--ulimit", "fsize=1048576:1048576",
            "--log-driver=none", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
            "--mount", f"type=bind,source={folder},target=/work,readonly",
            "--workdir=/work", IMAGE, "python", "-I", "-B", "/work/task.py"]

def execute(code: str, content: str, timeout: float = 8) -> dict:
    if not available():
        raise RuntimeError("Docker sandbox is unavailable; execution is blocked.")
    if len(code.encode()) > 16384:
        raise ValueError("Generated program exceeds 16 KiB.")
    name = "receiptops-" + uuid.uuid4().hex
    started = time.monotonic()
    output = bytearray()
    timed_out = output_limited = False
    cleanup_ok = False
    with tempfile.TemporaryDirectory(prefix="receiptops-") as directory:
        folder = Path(directory)
        folder.chmod(0o755)
        (folder / "input.csv").write_text(content)
        (folder / "task.py").write_text(code)
        for path in folder.iterdir():
            path.chmod(0o444)
        proc = None
        selector = selectors.DefaultSelector()
        try:
            proc = subprocess.Popen(command(name, folder), stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            selector.register(proc.stdout, selectors.EVENT_READ)
            while True:
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    timed_out = True
                    break
                events = selector.select(min(remaining, 0.1))
                if events:
                    chunk = os.read(proc.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    output.extend(chunk)
                    if len(output) > POLICY["output_bytes"]:
                        output_limited = True
                        del output[POLICY["output_bytes"]:]
                        break
                elif proc.poll() is not None:
                    continue
            if timed_out or output_limited:
                # Detach the Docker client before removing the container. A full
                # stdout pipe can otherwise block daemon shutdown while no one
                # is draining the attached stream. The finally block force-
                # removes the container even when this client is interrupted.
                proc.kill()
                proc.wait(timeout=3)
                proc.stdout.close()
            try:
                exit_code = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                exit_code = proc.wait(timeout=3)
        finally:
            selector.close()
            if proc and proc.poll() is None:
                proc.kill()
                proc.wait(timeout=3)
            if proc and proc.stdout:
                proc.stdout.close()
            try:
                removed = subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=5)
                cleanup_ok = removed.returncode == 0
            except subprocess.TimeoutExpired:
                cleanup_ok = False
    return {"stdout": output.decode("utf-8", errors="replace"), "exit_code": exit_code,
            "timed_out": timed_out, "output_limited": output_limited,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "container_removed": cleanup_ok, "policy": POLICY, "image": IMAGE}

PROBE = '''import errno, json, os, socket
result = {}
try:
    socket.create_connection(("1.1.1.1", 443), timeout=1).close()
    result["network_blocked"] = False
except OSError:
    result["network_blocked"] = True
try:
    open("/work/input.csv", "w").write("modified")
    result["input_read_only"] = False
except OSError:
    result["input_read_only"] = True
try:
    open("/var/tmp/receiptops-probe", "w").write("modified")
    result["root_read_only"] = False
except OSError as error:
    result["root_read_only"] = error.errno == errno.EROFS
result["non_root"] = os.getuid() == 65534
result["inference_key_absent"] = "VULTR_INFERENCE_API_KEY" not in os.environ
result["docker_socket_absent"] = not os.path.exists("/var/run/docker.sock")
print(json.dumps(result))
'''
