import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { parseSource, ingest, resolveSource, publicIP } from '../scripts/ingest.mjs';
import { modelSelection } from '../scripts/local-model.mjs';
import { prepareFeed, buildCV } from '../web/core.mjs';

const fixture = await readFile(new URL('../web/data/jobs.json', import.meta.url), 'utf8');
const p = JSON.parse(await readFile(new URL('../web/data/profile.example.json', import.meta.url)));
const job = prepareFeed(JSON.parse(fixture)).jobs[0];
const config = { name: 'Test source', url: 'https://jobs.example.org/export.json', allowed_hosts: ['jobs.example.org'], format: 'json', synthetic: true };
const now = '2026-11-02T12:00:00Z';
test('JSON source adapter preserves rejection evidence and synthetic status', () => {
  const result = parseSource(fixture, config, now);
  assert.equal(result.jobs.length, 13); assert.equal(result.rejected.length, 1);
  assert.ok(result.normalized_jobs.every(j => j.synthetic));
});
test('an upstream synthetic source cannot be relabelled real by configuration', () => {
  const result = parseSource(fixture, { ...config, synthetic: false }, now);
  assert.ok(result.jobs.every(j => j.synthetic));
});
test('JSON-LD graph adapter reads JobPosting and keeps unstructured eligibility in review', () => {
  const value = { '@graph': [{ '@type': 'Organization', name: 'Other' }, { '@type': 'JobPosting', title: 'Records Assistant', hiringOrganization: { name: 'Sample' }, url: 'https://jobs.example.org/1', datePosted: '2026-10-30', validThrough: '2026-11-20', description: '<p>Records work</p>', jobLocation: { address: { addressLocality: 'Varanasi', addressCountry: 'IN' } } }] };
  const html = `<script type="application/ld+json">${JSON.stringify(value)}</script>`;
  const result = parseSource(html, { ...config, format: 'jsonld' }, now);
  assert.equal(result.jobs.length, 1); assert.equal(result.jobs[0].location, 'Varanasi, IN');
  assert.equal(result.jobs[0].requirements.review_required, true); assert.equal(result.jobs[0].esm, null);
});
test('unavailable sources produce explicit failure and never synthetic fallback vacancies', async () => {
  const result = await ingest([config], async () => { throw new Error('HTTP 503'); }, now);
  assert.equal(result.status, 'failed'); assert.equal(result.jobs.length, 0); assert.equal(result.failures[0].reason, 'HTTP 503');
});
test('partial ingestion retains successful sources and reports the missing coverage', async () => {
  const result = await ingest([config, { ...config, name: 'Unavailable' }], async c => { if (c.name === 'Unavailable') throw new Error('Offline'); return fixture; }, now);
  assert.equal(result.status, 'partial'); assert.equal(result.jobs.length, 13); assert.equal(result.failures.length, 1);
  assert.equal(prepareFeed(result).jobs.length, 13);
});
test('private, reserved, loopback and mapped IPs are blocked', () => {
  for (const ip of ['127.0.0.1', '10.2.3.4', '172.16.1.1', '192.168.1.1', '169.254.169.254', '100.64.0.1', '::1', '::ffff:127.0.0.1', 'fc00::1', 'fe80::1', '2001:db8::1']) assert.equal(publicIP(ip), false, ip);
  assert.equal(publicIP('8.8.8.8'), true); assert.equal(publicIP('2606:4700:4700::1111'), true);
});
test('source hosts require explicit approval and may not resolve to private IPs', async () => {
  await assert.rejects(resolveSource({ ...config, allowed_hosts: [] }));
  await assert.rejects(resolveSource({ ...config, url: 'https://localhost/x', allowed_hosts: ['localhost'] }));
  await assert.rejects(resolveSource(config, async () => [{ address: '127.0.0.1', family: 4 }]));
  await assert.rejects(resolveSource(config, async () => [{ address: '8.8.8.8', family: 4 }, { address: '10.0.0.1', family: 4 }]));
  const result = await resolveSource(config, async () => [{ address: '8.8.8.8', family: 4 }]); assert.equal(result.address.address, '8.8.8.8');
});
test('optional local model uses loopback, excludes name/contact and validates selected facts', async () => {
  const ids = p.facts.map(f => f.id).reverse(); let called = false;
  const selected = await modelSelection({ ...p, contact: 'private@example.org' }, job, { model: 'local:test', fetcher: async (url, opts) => {
    called = true; assert.equal(url.hostname, '127.0.0.1');
    const body = JSON.parse(opts.body); assert.ok(!body.prompt.includes('private@example.org')); assert.ok(!body.prompt.includes(p.name));
    assert.equal(body.stream, false);
    return new Response(JSON.stringify({ done: true, response: JSON.stringify({ fact_ids: ids }) }));
  } });
  assert.ok(called); assert.deepEqual(selected, ids); assert.equal(buildCV(p, job, selected).receipt.claims.length, ids.length);
});
test('model endpoint cannot become a remote profile-exfiltration URL', async () => {
  for (const endpoint of ['https://example.org', 'http://localhost:11434', 'http://127.0.0.1.evil.example', 'http://127.0.0.1:11434/other']) await assert.rejects(modelSelection(p, job, { model: 'test', endpoint }));
});
test('malformed, incomplete, unsupported and injected model responses fail closed', async () => {
  for (const data of [{ done: false, response: '{}' }, { done: true, response: 'not json' }, { done: true, response: '{"fact_ids":["fake_degree"]}' }, { done: true, response: JSON.stringify({ fact_ids: p.facts.map(f => f.id), summary: 'MBA graduate' }) }]) {
    await assert.rejects(modelSelection(p, job, { model: 'test', fetcher: async () => new Response(JSON.stringify(data)) }));
  }
});
