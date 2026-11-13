"""Fail if the browser source manifest differs from the actual Python sources."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'web' / 'sources.json').read_text())
expected_paths = {'receiver.py', 'baseline/revocation_demo.py', 'web/engine.py'}
if set(manifest['files']) != expected_paths:
    raise SystemExit('Unexpected source set in browser manifest')
for name, expected in manifest['files'].items():
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
        raise SystemExit(f'Browser source hash mismatch: {name}')
print('PASS: browser engine and receiver source hashes match')
