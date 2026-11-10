import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { after, test } from 'node:test';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'esbuild';
import { createPreviewBinding } from '../scripts/connector-preview/host-binding.mjs';
import { driverMessageSchema, grantsSchema, invocationSchema, sessionOptionsSchema } from '../scripts/connector-preview/protocol.mjs';

const dir = await mkdtemp(join(tmpdir(), 'proofpay-connectors-'));
const entry = join(dir, 'connector-errors.mjs');
await build({ entryPoints: ['lib/connector-errors.mts'], outfile: entry, bundle: true, platform: 'node', format: 'esm', logLevel: 'silent' });
const { connectorResponse } = await import(pathToFileURL(entry));
after(() => rm(dir, { recursive: true, force: true }));

const grant = { connectorId: 'synthetic-connector', actionName: 'read_records', readOnly: true };
const invocation = { connectorId: grant.connectorId, actionName: grant.actionName, arguments: {} };
const request = value => new Request('http://preview/invoke', { method: 'POST', body: JSON.stringify(value) });
async function withBinding(invoke, run, options = {}) {
  const binding = createPreviewBinding({ tools: [{ ...grant, invoke }], ...options });
  try { await run(binding); } finally { binding.close(); }
}
function countedArray(length) {
  let reads = 0;
  const content = Array.from({ length }, () => Object.defineProperty({}, 'type', { enumerable: true, get() { reads++; return 'text'; } }));
  return { content, reads: () => reads };
}

test('connector: record migration preserves JSON arguments through the actual preview binding', async () => {
  for (const args of [{}, { query: 'records', nested: { values: [null, false, 0, ''], active: true } }]) {
    let calls = 0;
    await withBinding(async value => {
      calls++;
      assert.deepEqual(value, args);
      return { content: [], structuredContent: value };
    }, async binding => {
      const response = await binding.fetch(request({ ...invocation, arguments: args }));
      assert.deepEqual(await response.json(), { status: 'success', result: { content: [], structuredContent: args } });
      assert.equal(calls, 1);
      assert.equal(response.headers.get('cache-control'), 'no-store');
    });
  }
});

test('connector: extra authority fields and malformed argument containers never dispatch', async () => {
  let calls = 0;
  await withBinding(async () => { calls++; return { content: [] }; }, async binding => {
    const malformed = [
      { ...invocation, accountId: 'other-account' },
      { ...invocation, nativeTool: 'write_record' },
      { ...invocation, arguments: [] },
      { ...invocation, arguments: null },
      { ...invocation, arguments: 'record' },
      { connectorId: grant.connectorId, actionName: grant.actionName },
    ];
    for (const value of malformed) assert.equal((await (await binding.fetch(request(value))).json()).status, 'invalid_request');
    assert.equal((await (await binding.fetch(request({ ...invocation, actionName: 'write_records' }))).json()).status, 'tool_not_allowed');
    assert.equal(calls, 0);
  });
  assert.equal(invocationSchema.safeParse(invocation).success, true);
});

test('connector: read-only grants and session limits retain their authority boundary', async () => {
  assert.throws(() => createPreviewBinding({ tools: [{ ...grant, readOnly: false, invoke() {} }] }));
  assert.throws(() => createPreviewBinding({ tools: [{ ...grant, invoke() {} }, { ...grant, invoke() {} }] }));
  assert.deepEqual(sessionOptionsSchema.parse({}), { timeoutMs: 120000, maxConcurrent: 64 });
  for (const value of [0, -1, 1.5, Number.MAX_SAFE_INTEGER + 1]) {
    assert.equal(sessionOptionsSchema.safeParse({ maxConcurrent: value }).success, false);
    assert.equal(sessionOptionsSchema.safeParse({ maxCalls: value }).success, false);
  }
  assert.equal(sessionOptionsSchema.safeParse({ timeoutMs: 2 ** 31 }).success, false);
  let calls = 0;
  await withBinding(async () => { calls++; return { content: [] }; }, async binding => {
    assert.equal((await (await binding.fetch(request(invocation))).json()).status, 'success');
    assert.equal((await (await binding.fetch(request(invocation))).json()).status, 'tool_not_allowed');
    binding.close();
    assert.equal((await (await binding.fetch(request(invocation))).json()).status, 'binding_unavailable');
    assert.equal(calls, 1);
  }, { maxCalls: 1 });
});

test('connector: JSON-RPC record results and real UUIDs remain compatible without accepting ambiguous envelopes', () => {
  const id = randomUUID();
  for (const result of [{}, { content: [], structuredContent: { values: [null, false, 0] } }]) {
    const message = { jsonrpc: '2.0', id, result };
    assert.deepEqual(driverMessageSchema.parse(message), message);
  }
  assert.deepEqual(driverMessageSchema.parse({ jsonrpc: '2.0', method: 'stop' }), { jsonrpc: '2.0', method: 'stop' });
  for (const message of [
    { jsonrpc: '2.0', id, result: [] },
    { jsonrpc: '2.0', id, result: {}, error: { code: 1, message: 'ambiguous' } },
    { jsonrpc: '2.0', id: 'not-a-uuid', result: {} },
    { jsonrpc: '2.0', id, error: { code: 1.5, message: 'invalid code' } },
  ]) assert.equal(driverMessageSchema.safeParse(message).success, false);
});

test('connector: oversized grant list is rejected before any grant is inspected', () => {
  let reads = 0;
  const grants = Array.from({ length: 257 }, () => Object.defineProperty({ actionName: grant.actionName, readOnly: true }, 'connectorId', { enumerable: true, get() { reads++; return grant.connectorId; } }));
  const result = grantsSchema.safeParse(grants);
  assert.equal(result.success, false);
  assert.equal(reads, 0);
  assert.equal(result.error.issues.length, 1);
  assert.equal(result.error.issues[0].code, 'too_big');
  assert.equal(grantsSchema.safeParse(Array.from({ length: 256 }, () => ({ ...grant }))).success, true);
});

test('connector: oversized preview result is rejected before any content block is inspected', async () => {
  const counted = countedArray(1025);
  await withBinding(async () => ({ content: counted.content }), async binding => {
    const result = await (await binding.fetch(request(invocation))).json();
    assert.equal(result.status, 'upstream_error');
    assert.equal('result' in result, false);
    assert.equal(counted.reads(), 0);
  });
});

test('connector: oversized deployed result is rejected before any content block is inspected', async () => {
  const counted = countedArray(1025);
  const response = connectorResponse({ status: 'success', result: { content: counted.content } });
  assert.equal(response.status, 502);
  assert.equal((await response.json()).status, 'upstream_error');
  assert.equal(counted.reads(), 0);
});

test('connector: result cap is inclusive and valid payload projection preserves falsy JSON values', async () => {
  const content = Array.from({ length: 1024 }, () => ({ type: 'text', text: 'synthetic' }));
  for (const structuredContent of [null, false, 0, '', []]) {
    await withBinding(async () => ({ content, structuredContent, requestId: 'synthetic:request-1', privateField: 'omit' }), async binding => {
      const local = await (await binding.fetch(request(invocation))).json();
      assert.deepEqual(local, { status: 'success', result: { content, structuredContent }, requestId: 'synthetic:request-1' });
      const response = connectorResponse({ ...local, privateField: 'omit' });
      assert.equal(response.status, 200);
      assert.equal(response.headers.get('cache-control'), 'private, no-store');
      assert.deepEqual(await response.json(), local);
    });
  }
});

test('connector: provider-authored status and invalid block types cannot become success', async () => {
  for (const result of [
    { status: 'success', content: [] },
    { error: 'hidden-failure', content: [] },
    { content: [{ type: 7 }] },
    { content: [{ type: 'text', value: Number.POSITIVE_INFINITY }] },
  ]) {
    await withBinding(async () => result, async binding => {
      const response = await (await binding.fetch(request(invocation))).json();
      assert.equal(response.status, 'upstream_error');
      assert.equal('result' in response, false);
    });
  }
  for (const result of [
    { status: 'success', result: { content: [] }, error: 'hidden-failure' },
    { status: 'success', result: { content: [], isError: true } },
    { status: 'success', result: { content: [] }, retryAfterMs: 1000 },
  ]) assert.equal(connectorResponse(result).status, 502);
});

test('connector: rate limits and invalid argument failures retain meaning across preview and response validation', async () => {
  for (const [structuredContent, expected] of [
    [{ error_code: 'RATE_LIMITED', retry_after_seconds: 2 }, 'rate_limited'],
    [{ error_code: 'INVALID_ARGUMENT', error_data: { type: 'invalid_action_arguments', failure_stage: 'argument_binding' } }, 'invalid_request'],
    [{ error_code: 'OTHER' }, 'tool_error'],
  ]) {
    await withBinding(async () => ({ isError: true, content: [], structuredContent, requestId: 'synthetic:request-2' }), async binding => {
      const local = await (await binding.fetch(request(invocation))).json();
      assert.equal(local.status, expected);
      if (expected === 'rate_limited') assert.equal(local.retryAfterMs, 2000);
      const response = connectorResponse(local);
      assert.equal(response.status, 200);
      assert.deepEqual(await response.json(), local);
    });
  }
});

// Synthetic connector fixtures only. No real connector tool or network call is
// made. These are compatibility and resource-bound checks, not ingress evidence.
