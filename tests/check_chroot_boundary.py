"""Run as root on an isolated CI runner to verify the Harbor worker boundary."""
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "programs/repository-agent-reliability/runner"))
from candidate_proxy import Candidate

source = b'''import os, socket
class Probe:
    def handle(self, host_path):
        checks = [os.getuid() != 0, os.getgid() != 0, not os.path.exists(host_path),
                  "SYNTHETIC_PROVIDER_KEY" not in os.environ]
        try:
            os.setuid(0)
            checks.append(False)
        except PermissionError:
            checks.append(True)
        try:
            socket.socket()
            checks.append(False)
        except PermissionError:
            checks.append(True)
        return checks
'''

if __name__ == "__main__":
    assert os.geteuid() == 0, "This integration probe requires a root CI supervisor"
    with tempfile.NamedTemporaryFile() as host:
        os.chmod(host.name, 0o644)
        os.environ["SYNTHETIC_PROVIDER_KEY"] = "synthetic-no-secret"
        candidate = Candidate(source, "Probe", isolation="chroot")
        try:
            checks = candidate.request("call", name="handle", args=[host.name])["result"]
            assert checks == [True] * 6, checks
        finally:
            candidate.close()
    print("Chroot, privilege drop, credentials, and network boundary passed")
