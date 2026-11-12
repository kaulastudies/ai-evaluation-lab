#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
PYTHONPATH=. python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 revocation_demo.py > evidence.json
printf '\nReceipt evidence written to evidence.json\n'
  
