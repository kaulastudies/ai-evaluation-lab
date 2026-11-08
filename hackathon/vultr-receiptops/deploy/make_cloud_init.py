#!/usr/bin/env python3
"""Generate private cloud-init data for a dedicated ReceiptOps Vultr VM."""
import argparse
import json
import os
import re
from pathlib import Path


def build(commit: str, model: str, key: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Use the full reviewed Git commit SHA.")
    if not model.strip() or len(model) > 200 or any(c in model for c in "\n\r\x00"):
        raise ValueError("Use an exact model ID from Vultr's model list.")
    if not key.strip() or any(c in key for c in "\n\r\x00"):
        raise ValueError("The key must be one nonempty line.")
    config = json.dumps({"key": key.strip(), "model": model})
    bootstrap = f'''#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git ca-certificates
install -d -m 0700 /root/receiptops-source
cd /root/receiptops-source
git init
git remote add origin https://github.com/kaulastudies/ai-evaluation-lab.git
git config core.sparseCheckout true
printf '%s\\n' 'hackathon/vultr-receiptops/' > .git/info/sparse-checkout
git fetch --depth=1 origin {commit}
git checkout --detach FETCH_HEAD
test "$(git rev-parse HEAD)" = '{commit}'
bash hackathon/vultr-receiptops/deploy/install.sh
python3 - <<'CONFIGURE'
import json, os
from pathlib import Path
p = Path('/etc/receiptops.env')
cfg = json.loads(Path('/root/receiptops-inference.json').read_text())
lines = [line for line in p.read_text().splitlines() if not line.startswith(('VULTR_INFERENCE_API_KEY=', 'VULTR_MODEL='))]
lines += ['VULTR_INFERENCE_API_KEY=' + json.dumps(cfg['key']), 'VULTR_MODEL=' + json.dumps(cfg['model'])]
p.write_text('\\n'.join(lines) + '\\n')
os.chmod(p, 0o600)
Path('/root/receiptops-inference.json').unlink()
CONFIGURE
systemctl restart receiptops
'''
    # JSON scalars are valid YAML and avoid shell interpolation of credentials.
    return "\n".join([
        "#cloud-config", "write_files:",
        "  - path: /root/receiptops-inference.json", "    permissions: '0600'", "    owner: root:root",
        "    content: " + json.dumps(config),
        "  - path: /root/receiptops-bootstrap.sh", "    permissions: '0700'", "    owner: root:root",
        "    content: " + json.dumps(bootstrap),
        "runcmd:", "  - [bash, /root/receiptops-bootstrap.sh]", "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--key-file', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    content = build(args.commit, args.model, args.key_file.read_text())
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(content)
    print('Created private cloud-init file. It contains a credential; do not commit or publish it.')

if __name__ == '__main__':
    main()
