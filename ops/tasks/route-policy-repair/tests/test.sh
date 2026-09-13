#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier

if python /tests/test_router.py; then
  printf '1\n' > /logs/verifier/reward.txt
else
  printf '0\n' > /logs/verifier/reward.txt
  exit 1
fi
