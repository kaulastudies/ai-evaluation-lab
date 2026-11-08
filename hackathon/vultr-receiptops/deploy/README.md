# Dedicated Vultr deployment

Deploy both the workbench and API on one Ubuntu 24.04 LTS Vultr VM.
The reviewed selection is 1 vCPU, 1 GB RAM, 25 GB storage, public IPv4,
Atlanta, with automatic backups ($6/month as displayed in the account).
No VM or inference subscription has been created yet.

1. Create the `receiptops-agent-rush` Serverless Inference subscription.
2. Read the exact language-model ID from the Vultr model list. Prefer a low-cost
   coding-capable model. Do not derive an ID from the human-readable label.
3. Keep the API key in a private local file, not a chat message or repository.
4. Generate cloud-init using the current reviewed source commit:

```bash
python3 deploy/make_cloud_init.py \
  --commit FULL_REVIEWED_COMMIT_SHA \
  --model EXACT_VULTR_MODEL_ID \
  --key-file /private/path/inference-key.txt \
  --output /private/path/receiptops-cloud-init.yaml
```

5. Paste that private file into Vultr's Cloud-Init User Data field and deploy.
   Vultr retains cloud-init data in its control plane, so this credential must
   be scoped to this demo and protected as account data. The generated file
   never places the key in the repository or sandbox.
6. After cloud-init finishes, open the VM's public address. `/api/status` must
   show both `sandbox_ready` and `inference_ready` as true. These flags show
   configuration/readiness, not proof of a successful model call.
7. Run the invoice audit and containment probes. Save the actual downloaded
   bundles and separately publish the public verification key. Run the offline
   verifier before recording a successful demo.
8. Capture the live workflow for the demo video, including a blocked network
   attempt and receipt tampering. Update README evidence only from these runs.

## Troubleshooting on the dedicated VM

```bash
cloud-init status --long
systemctl status receiptops nginx docker --no-pager
journalctl -u receiptops -n 60 --no-pager
curl --fail http://127.0.0.1:8000/api/status
```

Do not publish cloud-init logs or the environment file. Keep the service on one
worker because its execution lock is process-local. Public mode is sample-only.
Configure TLS and authentication before handling real customer records.

## Usage and lifecycle

The application enforces 60 runs/day and 100 runs across the lifetime of its
SQLite database, including failures. Each audit permits two inference calls
with 2,200 output tokens each. Do not reset the database to evade the limit.
The limits govern this application, not external API-key use or VM charges.
The VM and backups continue to bill until removed in Vultr. Powering it off
does not necessarily stop charges. Keep it available for judging and review
its lifecycle before the promotional credits expire.
