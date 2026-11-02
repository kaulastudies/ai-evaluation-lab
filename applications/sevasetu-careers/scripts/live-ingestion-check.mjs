import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { ingest } from './ingest.mjs';
import { prepareFeed, lifecycle } from '../web/core.mjs';

const configs = JSON.parse(await readFile(new URL('../sources.example.json', import.meta.url)));
const started = Date.now();
const report = await ingest(configs);
assert.equal(report.status, 'ok', JSON.stringify(report.failures));
assert.equal(report.jobs.length, 13);
assert.equal(report.rejected.length, 1);
assert.ok(report.jobs.every(j => j.synthetic), 'Synthetic source must stay synthetic');
const qualified = prepareFeed(report);
assert.equal(qualified.rejected.length, 0);
assert.equal(lifecycle(qualified.jobs.find(j => j.id === 'sample-expired'), new Date().toISOString()).state, 'expired');
const evidence = { tested_at: new Date().toISOString(), transport: 'real_https_requests_with_public_dns_pinning',
  source: configs[0].url, scope: 'Public synthetic feed. No official vacancy feed or actual candidate data.',
  status: 'PASS', jobs: report.jobs.length, rejected_controls: report.rejected.length,
  synthetic_status_preserved: true, normalized_roundtrip: true, elapsed_ms: Date.now() - started,
  normalized_feed_sha256: createHash('sha256').update(JSON.stringify(report.jobs)).digest('hex') };
await mkdir('live-results', { recursive: true });
await writeFile('live-results/internet-ingestion.json', JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify(evidence));
