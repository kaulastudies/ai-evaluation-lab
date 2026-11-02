import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

test('CLI CV output bytes match the downloadable evidence hash', async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'sevasetu-cv-'));
  const root = fileURLToPath(new URL('../', import.meta.url));
  const output = path.join(dir, 'candidate.txt');
  try {
    execFileSync(process.execPath, ['scripts/cv.mjs', 'web/data/profile.example.json', 'web/data/jobs.json', 'sample-warehouse', output], { cwd: root });
    const receipt = JSON.parse(await readFile(output + '.receipt.json', 'utf8'));
    assert.equal(createHash('sha256').update(await readFile(output)).digest('hex'), receipt.cv_sha256);
  } finally { await rm(dir, { recursive: true, force: true }); }
});
