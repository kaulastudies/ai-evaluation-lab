"""Trusted JSON supervisor; Linux bubblewrap + seccomp are mandatory.

Only source bytes and the transport worker are mounted in the candidate sandbox.
No tests, expected answers, credentials, verifier state, or repository are mounted.
"""
from __future__ import annotations

import atexit
import importlib.util
import io
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
import weakref
from functools import lru_cache

from security import clean_env, kill_tree, read_confined, task_id

SOURCES = {"AP-001": ("resource_view", "ResourceView"), "AP-002": ("workspace_policy", "WorkspacePolicy"),
           "AP-003": ("event_processor", "EventProcessor"), "AP-004": ("user_response", "UserResponseBuilder"),
           "AP-005": ("record_transformer", "RecordTransformer")}
SESSIONS = weakref.WeakSet()


class Candidate:
    def __init__(self, source: bytes, class_name=None, *, isolation="bubblewrap"):
        if isolation not in {"bubblewrap", "chroot"}:
            raise ValueError("Unsupported isolation backend")
        if isolation == "chroot" and os.geteuid() != 0:
            raise RuntimeError("chroot isolation requires a root supervisor")
        if isolation == "bubblewrap" and (not shutil.which("bwrap") or not Path("/usr/bin/python3").exists()):
            raise RuntimeError("HOLD: Linux bubblewrap isolation is required")
        self.temp = tempfile.TemporaryDirectory(prefix="rarb-candidate-")
        source_file = Path(self.temp.name) / "candidate.py"
        source_file.write_bytes(source)
        command = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session", "--clearenv",
                   "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib"]
        if Path("/lib64").exists():
            command += ["--ro-bind", "/lib64", "/lib64"]
        command += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                    "--ro-bind", str(source_file), "/candidate.py",
                    "--ro-bind", str(Path(__file__).with_name("candidate_worker.py")), "/worker.py",
                    "--chdir", "/tmp", "/usr/bin/python3", "-I", "-S", "/worker.py"]
        if isolation == "chroot":
            # No unsafe native fallback: worker must chroot AND drop uid/gid AND
            # install seccomp successfully before it can load the candidate.
            os.chmod(self.temp.name, 0o755)
            os.chmod(source_file, 0o444)
            command = [sys.executable, "-I", "-S", str(Path(__file__).with_name("candidate_worker.py")),
                       "--chroot", self.temp.name]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, start_new_session=True, env=clean_env())
        os.set_blocking(self.process.stdin.fileno(), False)
        self.buffer = bytearray()
        self.sequence = 0
        self.bytes_read = 0
        self.deadline = time.monotonic() + 15
        SESSIONS.add(self)
        if class_name:
            self.request("new", **{"class": class_name})

    def request(self, op, **args):
        self.sequence += 1
        request = json.dumps(dict(op=op, id=self.sequence, **args), allow_nan=False).encode() + b"\n"
        if len(request) > 65536 or self.sequence > 256:
            raise RuntimeError("Candidate request budget exceeded")
        try:
            with selectors.DefaultSelector() as writer:
                writer.register(self.process.stdin, selectors.EVENT_WRITE)
                while request:
                    if time.monotonic() >= self.deadline:
                        raise RuntimeError("Candidate input time budget exceeded")
                    if writer.select(0.1):
                        try:
                            written = os.write(self.process.stdin.fileno(), request)
                            request = request[written:]
                        except BlockingIOError:
                            pass
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdout, selectors.EVENT_READ)
                selector.register(self.process.stderr, selectors.EVENT_READ)
                while b"\n" not in self.buffer:
                    if time.monotonic() >= self.deadline:
                        raise RuntimeError("Candidate time budget exceeded")
                    for key, _ in selector.select(0.1):
                        data = os.read(key.fileobj.fileno(), 4096)
                        if not data:
                            raise RuntimeError("Candidate terminated without completing observation")
                        self.bytes_read += len(data)
                        if self.bytes_read > 65536:
                            raise RuntimeError("Candidate output budget exceeded")
                        if key.fileobj is self.process.stdout:
                            self.buffer.extend(data)
                line, _, rest = self.buffer.partition(b"\n")
                self.buffer = bytearray(rest)
            response = json.loads(line)
            if type(response) is not dict or set(response) != {"id", "value"} or response["id"] != self.sequence:
                raise RuntimeError("Invalid candidate observation protocol")
            return response["value"]
        except BaseException:
            self.close()
            raise

    def close(self):
        if getattr(self, "process", None) is not None:
            kill_tree(self.process)
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                try:
                    stream.close()
                except BrokenPipeError:
                    pass
            self.process = None
        if getattr(self, "temp", None):
            self.temp.cleanup()

    def __del__(self):
        self.close()


def close_all():
    for candidate in list(SESSIONS):
        candidate.close()


atexit.register(close_all)


def remote_class(root: Path, task: str):
    name, class_name = SOURCES[task_id(task)]
    source = read_confined(root, f"app/{name}.py")

    class Remote:
        def __init__(self):
            self._candidate = Candidate(source, class_name)

        def select_resource(self, resource, fetch):
            registrations = self._candidate.request("select", resource=resource)
            if type(registrations) is not list or len(registrations) != 1 or registrations[0][0] != resource:
                raise RuntimeError("Candidate must register the selected resource exactly once")
            key = registrations[0][1]
            fetch(resource, lambda value: self._candidate.request("resolve", key=key, value=value))

        def __getattr__(self, name):
            if name in ("total", "current_resource", "value"):
                return self._candidate.request("get", name=name)
            if name not in ("can_update", "handle", "build", "transform"):
                raise AttributeError(name)
            def invoke(*args):
                response = self._candidate.request("call", name=name, args=args)
                if type(response) is not dict or set(response) != {"result", "args"} or len(response["args"]) != len(args):
                    raise RuntimeError("Invalid candidate call observation")
                for original, observed in zip(args, response["args"]):
                    if isinstance(original, dict):
                        original.clear()
                        original.update(observed)
                    elif isinstance(original, list):
                        original[:] = observed
                return response["result"]
            return invoke

    return Remote


def public_validation(task_root: Path, candidate_root: Path, task: str):
    """Trusted public assertions operate on a remote object, never an import."""
    name, class_name = SOURCES[task_id(task)]
    module_name = f"app.{name}"
    module = types.ModuleType(module_name)
    setattr(module, class_name, remote_class(candidate_root, task))
    previous = {key: sys.modules.get(key) for key in ("app", module_name)}
    app = types.ModuleType("app")
    app.__path__ = []
    setattr(app, name, module)
    sys.modules.update({"app": app, module_name: module})
    try:
        path = task_root / "fixture" / "tests" / "public" / f"test_{name}.py"
        spec = importlib.util.spec_from_file_location(f"trusted_public_{task}", path)
        tests = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tests)
        suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
        result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        passed = result.testsRun > 0 and result.wasSuccessful() and not result.skipped
        return subprocess.CompletedProcess([], 0 if passed else 1, "", "")
    finally:
        close_all()
        for key, value in previous.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


def verify(task_root, candidate_root):
    path = task_root / "verifier" / "acceptance.py"
    spec = importlib.util.spec_from_file_location("trusted_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.evaluate(candidate_root)
    except Exception as exc:
        return {"task_id": task_root.name, "task_version": "0.1.0", "verifier_version": module.VERIFIER_VERSION,
                "candidate": "workspace", "gates": [], "status": "HOLD", "error": str(exc)}
    finally:
        close_all()


def sandbox_available():
    try:
        candidate = Candidate(b"class Probe:\n    pass\n", "Probe")
        candidate.close()
        return True
    except (OSError, RuntimeError):
        return False


@lru_cache(maxsize=5)
def qualify_current(task_root):
    """Requalify the new controller against all controls; preserve old archives."""
    mutations = sorted((task_root / "controls" / "mutations").iterdir())
    controls = [(task_root / "controls" / "reference", "VERIFIED_PASS"),
                (task_root / "controls" / "known_bad", "VERIFIED_FAIL")]
    controls += [(path, "VERIFIED_FAIL") for path in mutations if path.is_dir()]
    observed = [(verify(task_root, path)["status"], expected) for path, expected in controls]
    return {"status": "QUALIFIED" if all(a == b for a, b in observed) else "HOLD",
            "verifier_version": "0.2.0", "critical_mutations_total": len(controls) - 2,
            "critical_mutations_rejected": sum(a == "VERIFIED_FAIL" for a, _ in observed[2:])}
