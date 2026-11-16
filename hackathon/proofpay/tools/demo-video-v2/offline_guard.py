"""Restrict this inference process before native imports; never relax host policy.

Linux/libseccomp only. All new threads/processes inherit the additional filter.
No networking is needed after the explicitly separate model download step.
"""
import ctypes as C
import errno
import json
import os
from pathlib import Path
import platform
import stat


def lock_network():
    if platform.system() != 'Linux':
        raise RuntimeError('Offline inference requires the reviewed Linux network guard')
    if len(list(Path('/proc/self/task').iterdir())) != 1:
        raise RuntimeError('Install the filter before any inference thread starts')
    libc=C.CDLL(None,use_errno=True)
    sec=C.CDLL('libseccomp.so.2',use_errno=True)
    sec.seccomp_init.argtypes=[C.c_uint32];sec.seccomp_init.restype=C.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes=[C.c_char_p];sec.seccomp_syscall_resolve_name.restype=C.c_int
    sec.seccomp_rule_add.argtypes=[C.c_void_p,C.c_uint32,C.c_int,C.c_uint];sec.seccomp_rule_add.restype=C.c_int
    sec.seccomp_load.argtypes=[C.c_void_p];sec.seccomp_load.restype=C.c_int
    sec.seccomp_release.argtypes=[C.c_void_p];sec.seccomp_release.restype=None
    # Inference has no legitimate use for inherited descriptors beyond stdio.
    for fd in (0,1,2):
        if stat.S_ISSOCK(os.fstat(fd).st_mode):
            raise RuntimeError('Refusing a network-backed standard stream')
    for name in os.listdir('/proc/self/fd'):
        fd=int(name)
        if fd > 2:
            try: os.close(fd)
            except OSError as error:
                if error.errno != errno.EBADF: raise
    # PR_SET_NO_NEW_PRIVS; constants from installed Linux prctl/seccomp headers.
    if libc.prctl(38,1,0,0,0) != 0:
        raise OSError(C.get_errno(),'Cannot prevent privilege escalation')
    context=sec.seccomp_init(0x7fff0000)
    if not context: raise RuntimeError('Cannot allocate additional seccomp filter')
    blocked=[]
    try:
        for name in ('socket','socketpair','socketcall','connect','bind','listen','accept','accept4','sendto','sendmsg','sendmmsg','recvfrom','recvmsg','recvmmsg','io_uring_setup','io_uring_enter','io_uring_register'):
            number=sec.seccomp_syscall_resolve_name(name.encode())
            if number < 0: continue
            result=sec.seccomp_rule_add(context,0x00050000|errno.EPERM,number,0)
            if result != 0: raise RuntimeError(f'Cannot deny {name}: {result}')
            blocked.append(name)
        if not {'socket','socketpair','connect','sendto','sendmsg'}.issubset(blocked):
            raise RuntimeError('Required network syscall coverage unavailable')
        result=sec.seccomp_load(context)
        if result != 0: raise RuntimeError(f'Cannot load additional filter: {result}')
    finally:
        sec.seccomp_release(context)
    # Direct native calls must be blocked by the kernel, not a Python shim.
    for family in (1,2,10):
        C.set_errno(0)
        fd=libc.socket(family,1,0)
        if fd != -1 or C.get_errno() != errno.EPERM:
            if fd >= 0: os.close(fd)
            raise RuntimeError('Native socket-denial self-test failed')
    C.set_errno(0)
    if libc.connect(-1,None,0) != -1 or C.get_errno() != errno.EPERM:
        raise RuntimeError('Native connect-denial self-test failed')
    result={'network_guard':'additional per-process Linux seccomp filter','no_new_privileges':True,'inherited_non_stdio_descriptors_closed':True,'native_socket_connect_tests':'EPERM','blocked_syscalls':blocked}
    print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':
    lock_network()
