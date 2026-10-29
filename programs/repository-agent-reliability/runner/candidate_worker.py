"""Untrusted worker. It returns observations only; it never scores a candidate."""
import ctypes
import ctypes.util
import errno
import importlib.util
import json
import os
import resource
import socket  # Load the runtime module before chroot; seccomp denies socket syscalls.
import sys


def restrict():
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    lib = ctypes.CDLL(ctypes.util.find_library("seccomp") or "libseccomp.so.2", use_errno=True)
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7fff0000)  # ALLOW, with irreversible deny rules below.
    if not ctx:
        raise RuntimeError("seccomp initialization failed")
    try:
        for name in ("clone", "clone3", "fork", "vfork", "execve", "execveat", "socket", "socketpair",
                     "ptrace", "process_vm_writev", "mount", "unshare", "setns"):
            number = lib.seccomp_syscall_resolve_name(name.encode())
            if number >= 0 and lib.seccomp_rule_add(ctx, 0x50000 | errno.EPERM, number, 0):
                raise RuntimeError("seccomp rule failed")
        if lib.seccomp_load(ctx):
            raise RuntimeError("seccomp activation failed")
    finally:
        lib.seccomp_release(ctx)


restrict()
if len(sys.argv) == 3 and sys.argv[1] == "--chroot":
    # Separate Harbor verifier containers retain CAP_SYS_CHROOT but may forbid
    # nested user namespaces. Load the trusted runtime, then enter an empty root
    # and irrevocably drop root before importing any candidate bytes.
    if os.geteuid() != 0:
        raise RuntimeError("chroot worker requires a privileged trusted supervisor")
    os.chroot(sys.argv[2])
    os.chdir("/")
    os.setgroups([])
    os.setresgid(65534, 65534, 65534)
    os.setresuid(65534, 65534, 65534)
    if os.getuid() == 0 or os.getgid() == 0:
        raise RuntimeError("Failed to drop worker privileges")
spec = importlib.util.spec_from_file_location("candidate", "/candidate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
obj = None
callbacks = {}
for line in sys.stdin:
    request = json.loads(line)
    operation = request["op"]
    if operation == "new":
        obj = getattr(module, request["class"])()
        value = None
    elif operation == "get":
        value = getattr(obj, request["name"])
    elif operation == "select":
        registrations = []
        def fetch(resource_name, callback):
            key = str(request["id"]) + ":" + str(len(registrations))
            callbacks[key] = callback
            registrations.append([resource_name, key])
        obj.select_resource(request["resource"], fetch)
        value = registrations
    elif operation == "resolve":
        callbacks.pop(request["key"])(request["value"])
        value = None
    elif operation == "call":
        args = request["args"]
        target = module if obj is None else obj
        value = {"result": getattr(target, request["name"])(*args), "args": args}
    else:
        raise ValueError("Unknown operation")
    print(json.dumps({"id": request["id"], "value": value}, allow_nan=False), flush=True)
