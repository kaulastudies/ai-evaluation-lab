#!/usr/bin/env bash
# Run on a dedicated Ubuntu 24.04 Vultr VM after reviewing this script.
set -euo pipefail
if [ "$(id -u)" != 0 ]; then
  echo 'Run as root on the dedicated ReceiptOps VM.' >&2
  exit 1
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3-venv python3-pip docker.io nginx
systemctl enable --now docker
id receiptops >/dev/null 2>&1 || useradd --system --create-home --home-dir /var/lib/receiptops receiptops
usermod -aG docker receiptops
install -d -m 0755 /opt/receiptops
task_source="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$task_source" != /opt/receiptops ]; then
  cp -a "$task_source"/. /opt/receiptops/
fi
cd /opt/receiptops
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
docker pull python:3.12-slim
task_image_digest="$(docker image inspect python:3.12-slim --format '{{index .RepoDigests 0}}')"
install -d -o receiptops -g receiptops -m 0700 /var/lib/receiptops
if [ ! -f /etc/receiptops.env ]; then
  umask 077
  cat > /etc/receiptops.env <<EOF
VULTR_INFERENCE_API_KEY=
VULTR_MODEL=
SANDBOX_IMAGE=$task_image_digest
PUBLIC_DEMO=1
DAILY_RUN_LIMIT=60
LIFETIME_RUN_LIMIT=100
DEPLOYMENT_LABEL="Vultr Cloud Compute · dedicated ReceiptOps VM"
EOF
fi
install -m 0644 deploy/receiptops.service /etc/systemd/system/receiptops.service
install -m 0644 deploy/nginx.conf /etc/nginx/sites-available/receiptops
ln -sfn /etc/nginx/sites-available/receiptops /etc/nginx/sites-enabled/receiptops
if [ -L /etc/nginx/sites-enabled/default ]; then unlink /etc/nginx/sites-enabled/default; fi
nginx -t
systemctl daemon-reload
systemctl enable --now receiptops
systemctl restart nginx
echo 'ReceiptOps installed. Configure Vultr inference in /etc/receiptops.env, then restart receiptops.'
echo 'Before private data use, add HTTPS and authentication. The public prototype is sample-only.'
