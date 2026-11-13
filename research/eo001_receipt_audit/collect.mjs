/** Original Lab instrumentation of a separately supplied, pinned Forge module.
 * No upstream source is vendored. This is a trusted synthetic recorder, not a
 * sandbox for untrusted agents or an authenticated real provider connection.
 */
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const lock = JSON.parse(readFileSync(new URL('./source_lock.json', import.meta.url)));
const sourcePath = resolve(process.argv[2] || '');
const sha = value => createHash('sha256').update(value).digest('hex');
if (sha(readFileSync(sourcePath)) !== lock.forge.sha256) {
  throw new Error('Upstream source digest mismatch; refusing execution');
}
const { SyntheticProvider, decideSyntheticFulfillment } = await import(pathToFileURL(sourcePath).href);
const copy = value => JSON.parse(JSON.stringify(value));
const request = { orderId: 'DEMO-1001', cents: 4200, currency: 'USD' };

function episode(lane, fault) {
  const caseId = `${lane}__${fault}`;
  const runId = `EO001-RECEIPT/${caseId}`;
  const provider = new SyntheticProvider({
    loseFirstAck: lane !== 'execute',
    lookupUnavailable: ['retry', 'unresolved'].includes(lane),
  });
  const calls = [];
  for (const op of ['execute', 'lookup']) {
    const original = provider[op].bind(provider);
    provider[op] = (...args) => {
      const call = {
        seq: calls.length + 1, op,
        request: op === 'execute' ? copy(args[0]) : null,
        idempotency_key: op === 'execute' ? args[1] : args[0],
        outcome: 'error', error: null, provider_receipt: null,
        delivered_receipt: null, receipt_origin_run_id: null,
      };
      // Capture the provider return before injecting into a copied response.
      // Never mutate the provider Map or a receipt shared with that Map.
      let raw;
      try { raw = original(...args); }
      catch (error) {
        call.error = error.message;
        calls.push(call);
        throw error;
      }
      call.outcome = 'returned';
      call.provider_receipt = copy(raw);
      let delivered = copy(raw);
      let origin = runId;
      if (fault === 'wrong_order') delivered.orderId = 'DEMO-9999';
      if (fault === 'unsettled') delivered.settled = false;
      if (fault === 'truthy_status') delivered.settled = 'true';
      if (fault === 'forged_id') delivered.id = 'SYNTHETIC-RECEIPT-FORGED';
      if (fault === 'cross_run_replay') {
        // A previous provider issues the SAME receipt bytes for the same order.
        // The controller knows its origin; the workflow receives only the bytes.
        const earlier = new SyntheticProvider();
        delivered = copy(earlier.execute(request, call.idempotency_key));
        origin = 'EO001-RECEIPT/previous-run';
      }
      call.delivered_receipt = copy(delivered);
      call.receipt_origin_run_id = origin;
      calls.push(call);
      return delivered;
    };
  }
  const result = decideSyntheticFulfillment(provider, request, { retryAfterLookupFailure: lane === 'retry' });
  return {
    case_id: caseId, run_id: runId, lane, fault, request: copy(request),
    provider_lane: {
      run_id: runId, complete: true, effects: provider.effects,
      attempts: provider.attempts, lookups: provider.lookups,
      receipts: Array.from(provider.receipts, ([key, state]) => ({
        idempotency_key: key, checksum: state.checksum, receipt: copy(state.receipt),
      })),
    },
    calls, workflow: copy(result),
  };
}

const episodes = [];
for (const lane of ['execute', 'lookup', 'retry']) {
  for (const fault of ['none', 'wrong_order', 'unsettled', 'truthy_status', 'forged_id', 'cross_run_replay']) {
    episodes.push(episode(lane, fault));
  }
}
episodes.push(episode('unresolved', 'none'));
process.stdout.write(JSON.stringify({
  schema_version: 1, protocol: 'EO-001-RECEIPT-AUDIT/0.1.0',
  upstream_sha256: lock.forge.sha256, episodes,
}, null, 2) + '\n');
