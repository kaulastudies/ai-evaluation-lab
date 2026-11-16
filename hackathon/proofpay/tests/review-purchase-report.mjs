import assert from 'node:assert/strict';
import {before, after, test} from 'node:test';
import {mkdtemp, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {build} from 'esbuild';

let root, csvCell, purchaseCsv;
before(async () => {
  root = await mkdtemp(join(tmpdir(), 'proofpay-report-'));
  const output = join(root, 'report.mjs');
  await build({entryPoints: ['components/proofpay/purchase-report.ts'], outfile: output, bundle: true, platform: 'node', format: 'esm', logLevel: 'silent'});
  ({csvCell, purchaseCsv} = await import(pathToFileURL(output)));
});
after(async () => { if (root) await rm(root, {recursive: true, force: true}); });

// Independent CSV reader to verify boundaries around commas, quotes and newlines.
function readCsv(text) {
  const rows = []; let row = [], cell = '', quoted = false;
  for (let i = text.startsWith('\uFEFF') ? 1 : 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      if (quoted && text[i + 1] === '"') { cell += '"'; i++; }
      else quoted = !quoted;
    } else if (c === ',' && !quoted) { row.push(cell); cell = ''; }
    else if (c === '\r' && text[i + 1] === '\n' && !quoted) { row.push(cell); rows.push(row); row = []; cell = ''; i++; }
    else cell += c;
  }
  assert.equal(quoted, false, 'every quoted cell is closed');
  assert.equal(cell, ''); assert.deepEqual(row, []);
  return rows;
}

test('CSV neutralizes formula prefixes after whitespace, BOM and control characters', () => {
  for (const value of ['=1+1', '+SUM(1,2)', '-1+2', '@SUM(1,2)', '  =1', '\t=1', '\r=1', '\n=1', '\uFEFF=1', '\u00a0+1', '\u0000@SUM(A1)', '\tordinary']) {
    const [[cell]] = readCsv(csvCell(value) + '\r\n');
    assert.equal(cell, "'" + value, JSON.stringify(value));
  }
});

test('CSV preserves quoted text, embedded lines and Unicode without creating extra cells', () => {
  const fields = ['Rama, "review"', 'first line\r\nsecond line', 'कार्य विभाग', 'ordinary', 180, null];
  assert.deepEqual(readCsv(fields.map(csvCell).join(',') + '\r\n'), [[...fields.slice(0, 4), '180', '']]);
});

test('purchase report contains the supplied workspace snapshot and current records only', () => {
  const workspace = {id: 'workspace-synthetic', mode: 'sandbox', profile: 'diagnostic', currency: 'USD', budgetCents: 45000, businessName: '=Injected name', department: 'Operations'};
  const operation = {id: 'operation-synthetic', title: 'Workflow review', sku: 'workflow-review', request: 'Review, "please"\nwith notes', aiSource: 'sandbox-diagnostic', status: 'UNKNOWN', amountCents: 18000, currency: 'USD', merchantId: 'synthetic-seller', providerMode: 'sandbox', approvalVersion: 2, approvalExpiresAt: null, orderId: 'synthetic-order', captureId: null, createdAt: 1760000000000, updatedAt: 1760000010000};
  const [headers, cells, ...extra] = readCsv(purchaseCsv(workspace, [operation], '2026-11-08T00:00:00.000Z'));
  assert.deepEqual(extra, []); assert.equal(headers.length, 24); assert.equal(cells.length, headers.length);
  const row = Object.fromEntries(headers.map((key, index) => [key, cells[index]]));
  assert.equal(row.business_name, "'=Injected name"); assert.equal(row.workspace_allowance, '450.00');
  assert.equal(row.workspace_mode, 'sandbox'); assert.equal(row.workspace_profile, 'diagnostic');
  assert.equal(row.proposal_source, 'sandbox-diagnostic'); assert.equal(row.status, 'UNKNOWN');
  assert.equal(row.capture_id, ''); assert.equal(row.approval_expires_at, '');
  assert.equal(row.request, operation.request); assert.equal(row.amount, '180.00');
  assert.equal(row.operation_id, operation.id); assert.equal(row.provider_order_id, operation.orderId);
});

test('empty report has headers only and invents no purchase rows', () => {
  const rows = readCsv(purchaseCsv({id: 'empty', mode: 'rehearsal', currency: 'USD', budgetCents: 30000}, [], '2026-11-08T00:00:00.000Z'));
  assert.equal(rows.length, 1); assert.ok(rows[0].includes('proposal_source'));
});
