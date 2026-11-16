import assert from 'node:assert/strict';
import { test, after } from 'node:test';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'esbuild';

const dir = await mkdtemp(join(tmpdir(), 'proofpay-review-provider-'));
const bundle = join(dir, 'provider.mjs');
await build({ entryPoints: ['lib/proofpay/provider.ts'], outfile: bundle, bundle: true, platform: 'node', format: 'esm', logLevel: 'silent' });
const { verifyOrder, completedCapture, approvalLink, PayPalSandboxProvider } = await import(pathToFileURL(bundle));
after(async () => { await rm(dir, { recursive: true, force: true }); });

const op = { id: 'operation-A', order_id: 'order-A', capture_id: null, merchant_id: 'seller-A', currency: 'USD', amount_cents: 18000, create_request_id: 'create-A', capture_request_id: 'capture-A' };
function good() { return { id: 'order-A', status: 'COMPLETED', purchase_units: [{ reference_id: 'operation-A', custom_id: 'operation-A', payee: { merchant_id: 'seller-A' }, amount: { currency_code: 'USD', value: '180.00' }, payments: { captures: [{ id: 'capture-A', status: 'COMPLETED', amount: { currency_code: 'USD', value: '180.00' }, final_capture: true }] } }] }; }

test('review: independently matching provider evidence confirms the expected capture', () => {
  assert.doesNotThrow(() => verifyOrder(op, good()));
  assert.equal(completedCapture(op, good()), 'capture-A');
});

const mutations = [
  ['wrong order', order => { order.id = 'order-B'; }],
  ['wrong operation reference', order => { order.purchase_units[0].reference_id = 'operation-B'; }],
  ['wrong custom ID', order => { order.purchase_units[0].custom_id = 'operation-B'; }],
  ['wrong seller', order => { order.purchase_units[0].payee.merchant_id = 'seller-B'; }],
  ['wrong order currency', order => { order.purchase_units[0].amount.currency_code = 'EUR'; }],
  ['wrong order amount', order => { order.purchase_units[0].amount.value = '160.00'; }],
  ['wrong capture currency', order => { order.purchase_units[0].payments.captures[0].amount.currency_code = 'EUR'; }],
  ['wrong capture amount', order => { order.purchase_units[0].payments.captures[0].amount.value = '160.00'; }],
  ['missing capture ID', order => { delete order.purchase_units[0].payments.captures[0].id; }],
  ['failed capture', order => { order.purchase_units[0].payments.captures[0].status = 'DECLINED'; }],
  ['inconsistent order status', order => { order.status = 'APPROVED'; }],
  ['non-final capture', order => { order.purchase_units[0].payments.captures[0].final_capture = false; }],
  ['duplicate capture', order => { order.purchase_units[0].payments.captures.push(structuredClone(order.purchase_units[0].payments.captures[0])); }],
  ['duplicate purchase unit', order => { order.purchase_units.push(structuredClone(order.purchase_units[0])); }],
  ['refund activity', order => { order.purchase_units[0].payments.refunds = [{ id: 'refund-A' }]; }],
  ['noncanonical monetary encoding', order => { order.purchase_units[0].amount.value = '1.8e2'; }],
];
for (const [name, mutation] of mutations) test(`review: provider mutation rejected: ${name}`, () => {
  const evidence = good(); mutation(evidence);
  assert.throws(() => completedCapture(op, evidence));
});

test('review: pending or absent capture is not confirmed', () => {
  const pending = good(); pending.purchase_units[0].payments.captures[0].status = 'PENDING';
  assert.equal(completedCapture(op, pending), null);
  delete pending.purchase_units[0].payments;
  assert.equal(completedCapture(op, pending), null);
});
test('review: previously bound capture cannot be silently replaced', () => {
  assert.throws(() => completedCapture({ ...op, capture_id: 'other-capture' }, good()));
});
test('review: approval links are restricted to sandbox PayPal and reject embedded credentials', () => {
  assert.equal(approvalLink({links:[{rel:'approve',href:'https://www.sandbox.paypal.com/checkoutnow?token=x'}]}), 'https://www.sandbox.paypal.com/checkoutnow?token=x');
  for (const href of ['https://www.paypal.com/checkout', 'https://www.sandbox.paypal.com.evil.invalid/', 'javascript:alert(1)', 'https://evil@www.sandbox.paypal.com/']) {
    assert.throws(() => approvalLink({links:[{rel:'approve',href}]}));
  }
});
test('review: missing sandbox credentials fail closed', () => {
  assert.throws(() => new PayPalSandboxProvider({}), error => error.code === 'PAYPAL_NOT_CONFIGURED');
});
test('review: sandbox adapter uses sandbox endpoints and persisted request IDs without hidden retry', async () => {
  const calls = [];
  const original = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    return String(url).endsWith('/v1/oauth2/token') ? Response.json({access_token:'test-only-token'}) : Response.json(good());
  };
  try {
    const provider = new PayPalSandboxProvider({PAYPAL_CLIENT_ID:'test-client',PAYPAL_CLIENT_SECRET:'test-secret',PAYPAL_MERCHANT_ID:'seller-A'});
    await provider.create(op, 'https://proofpay.example');
    await provider.capture(op);
    await provider.get(op);
    assert.equal(calls.length, 4);
    assert.ok(calls.every(call => call.url.startsWith('https://api-m.sandbox.paypal.com/')));
    assert.equal(calls[1].options.headers['PayPal-Request-Id'], 'create-A');
    assert.equal(calls[2].options.headers['PayPal-Request-Id'], 'capture-A');
    assert.equal(calls[3].options.method, 'GET');
    assert.equal(calls[3].options.headers['PayPal-Request-Id'], undefined);
    const payload = JSON.parse(calls[1].options.body);
    assert.equal(payload.purchase_units[0].amount.value, '180.00');
    assert.equal(payload.purchase_units[0].payee.merchant_id, 'seller-A');
    assert.equal(payload.purchase_units[0].custom_id, 'operation-A');
  } finally { globalThis.fetch = original; }
});
test('review: transport failure propagates uncertainty with no fake completion or second request', async () => {
  const calls = [];
  const original = globalThis.fetch;
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    return String(url).endsWith('/v1/oauth2/token') ? Response.json({access_token:'test-only-token'}) : new Response('unavailable', {status:503});
  };
  try {
    const provider = new PayPalSandboxProvider({PAYPAL_CLIENT_ID:'test-client',PAYPAL_CLIENT_SECRET:'test-secret',PAYPAL_MERCHANT_ID:'seller-A'});
    await assert.rejects(provider.capture(op), error => error.code === 'PAYPAL_UNCERTAIN');
    assert.equal(calls.length,2);
  } finally { globalThis.fetch = original; }
});
