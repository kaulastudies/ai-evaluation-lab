#!/usr/bin/env node
// Offline application-record consistency only. No signatures or provider calls.
import {createHash} from 'node:crypto';
import {open} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {isDeepStrictEqual} from 'node:util';

export const MAX_RECEIPT_BYTES = 1024 * 1024;
const FIELDS = ['operationId','workspaceId','sku','title','amountCents','currency','merchantId','mode','approvalVersion','approvalExpiresAt'];
const OP_FIELDS = ['id','workspaceId','request','agentLabel','sku','title','amountCents','currency','merchantId','status','approvalVersion','approvalExpiresAt','orderId','captureId','approvalUrl','providerMode','aiSource','rationale','createdAt','updatedAt'];
const STATUSES = ['PROPOSED','BUDGET_BLOCKED','APPROVED','CANCELLED','CREATE_DISPATCHED','CREATE_UNKNOWN','ORDER_READY','CAPTURE_DISPATCHED','UNKNOWN','REVIEW','CONFIRMED'];
function check(condition, message) { if (!condition) throw new Error(message); }
function shape(value, keys, label) {
  check(value !== null && typeof value === 'object' && !Array.isArray(value), `${label}: expected an object`);
  check(isDeepStrictEqual(Object.keys(value).sort(), [...keys].sort()), `${label}: missing or unsupported fields`);
}
function string(value, label, max = 256, empty = false) {
  check(typeof value === 'string' && value.length <= max && (empty || value.length > 0) && value.isWellFormed(), `${label}: invalid string`);
}
function integer(value, label, min = 1, max = Number.MAX_SAFE_INTEGER) {
  check(Number.isSafeInteger(value) && !Object.is(value, -0) && value >= min && value <= max, `${label}: invalid integer`);
}
function timestamp(value, label) { integer(value, label, 1, 8640000000000000); }
function nullableId(value, label) { if (value !== null) string(value, label); }

/** Bounded JSON parser rejects duplicate decoded keys before JSON.parse loses them. */
export function parseReceiptJSON(input) {
  const text = typeof input === 'string' ? input : new TextDecoder('utf-8', {fatal:true}).decode(input);
  check(Buffer.byteLength(text, 'utf8') <= MAX_RECEIPT_BYTES, 'Receipt exceeds the 1 MiB limit');
  let index = 0;
  const whitespace = () => { while (/[\x20\t\r\n]/.test(text[index] ?? '') && index < text.length) index++; };
  function quoted() {
    const start = index++;
    while (index < text.length) {
      const character = text[index++];
      if (character === '\\') { index++; continue; }
      if (character === '"') {
        const result = JSON.parse(text.slice(start, index));
        string(result, 'JSON string', 65536, true);
        return result;
      }
    }
    throw new Error('Unterminated JSON string');
  }
  function value(depth) {
    check(depth <= 32, 'JSON nesting exceeds 32 levels');
    whitespace();
    if (text[index] === '"') return quoted();
    if (text[index] === '{') {
      index++; whitespace(); const result = Object.create(null), keys = new Set();
      if (text[index] === '}') { index++; return result; }
      while (index < text.length) {
        check(text[index] === '"', 'Expected a JSON object key');
        const key = quoted(); check(!keys.has(key), 'Duplicate JSON object key'); keys.add(key);
        whitespace(); check(text[index++] === ':', 'Expected a JSON colon');
        result[key] = value(depth + 1); whitespace();
        const separator = text[index++]; if (separator === '}') return result;
        check(separator === ',', 'Expected a JSON object separator'); whitespace();
      }
      throw new Error('Unterminated JSON object');
    }
    if (text[index] === '[') {
      index++; whitespace(); const result = [];
      if (text[index] === ']') { index++; return result; }
      while (index < text.length) {
        result.push(value(depth + 1)); whitespace(); const separator = text[index++];
        if (separator === ']') return result;
        check(separator === ',', 'Expected a JSON array separator');
      }
      throw new Error('Unterminated JSON array');
    }
    const token = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(index));
    check(token, 'Invalid JSON value'); index += token[0].length;
    const result = JSON.parse(token[0]);
    check(typeof result !== 'number' || (Number.isFinite(result) && !Object.is(result, -0)), 'Unsupported JSON number');
    return result;
  }
  value(0); whitespace(); check(index === text.length, 'Unexpected trailing JSON content');
  // Validation above catches ambiguity; ordinary objects keep comparisons portable.
  return JSON.parse(text);
}

function amount(value, expected, label) {
  shape(value, ['value','currency'], label);
  check(value.currency === 'USD', `${label}: unsupported currency`);
  check(typeof value.value === 'string' && /^\d{1,10}\.\d{2}$/.test(value.value), `${label}: invalid decimal amount`);
  const [whole, fraction] = value.value.split('.');
  check(Number(whole) * 100 + Number(fraction) === expected, `${label}: amount mismatch`);
}
function verification(record, op) {
  shape(record, ['schemaVersion','mode','simulated','source','checkedAt','operationId','order','capture'], 'verification record');
  check(record.schemaVersion === 1, 'Unsupported provider record version');
  check(record.mode === op.providerMode && record.simulated === (op.providerMode === 'rehearsal'), 'Provider mode mismatch');
  check(record.source === (op.providerMode === 'rehearsal' ? 'simulated-provider-lookup' : 'paypal-sandbox-orders-get'), 'Provider source mismatch');
  check(record.operationId === op.id, 'Provider operation mismatch'); timestamp(record.checkedAt, 'checkedAt');
  shape(record.order, ['id','status','referenceId','customId','payeeMerchantId','amount'], 'order');
  shape(record.capture, ['id','status','finalCapture','amount'], 'capture');
  check(record.order.id === op.orderId && record.capture.id === op.captureId, 'Provider order/capture identity mismatch');
  check(record.order.referenceId === op.id && record.order.customId === op.id, 'Provider purchase reference mismatch');
  check(record.order.payeeMerchantId === op.merchantId, 'Provider merchant mismatch');
  check(record.order.status === 'COMPLETED' && record.capture.status === 'COMPLETED' && record.capture.finalCapture === true, 'Incomplete provider confirmation');
  amount(record.order.amount, op.amountCents, 'order amount'); amount(record.capture.amount, op.amountCents, 'capture amount');
}

export function verifyReceipt(receipt) {
  shape(receipt, ['receiptSchemaVersion','operation','createRequestId','captureRequestId','approvalDigest','approvalBinding','verificationRecords','events','claim'], 'receipt');
  check(receipt.receiptSchemaVersion === 1, 'Unsupported receipt schema version; re-export older receipts');
  const op = receipt.operation; shape(op, OP_FIELDS, 'operation');
  for (const field of ['id','workspaceId','sku','merchantId']) string(op[field], field);
  string(op.title, 'title', 512); string(op.request, 'request', 8192, true);
  string(op.agentLabel, 'agentLabel', 256, true); string(op.rationale, 'rationale', 8192, true);
  check(['model','rehearsal-rule','rehearsal-seed'].includes(op.aiSource), 'Unsupported proposal source');
  check(['rehearsal','sandbox'].includes(op.providerMode), 'Unsupported payment mode');
  check(op.currency === 'USD', 'Unsupported currency: this receipt profile supports USD only');
  integer(op.amountCents, 'amountCents', 1, 999999999999); integer(op.approvalVersion, 'approvalVersion');
  check(STATUSES.includes(op.status), 'Unsupported operation status');
  timestamp(op.createdAt, 'createdAt'); timestamp(op.updatedAt, 'updatedAt');
  check(op.updatedAt >= op.createdAt, 'Operation timestamp order mismatch');
  nullableId(op.orderId, 'orderId'); nullableId(op.captureId, 'captureId');
  if (op.approvalUrl !== null) string(op.approvalUrl, 'approvalUrl', 4096);
  string(receipt.createRequestId, 'createRequestId'); string(receipt.captureRequestId, 'captureRequestId');
  check(receipt.createRequestId !== receipt.captureRequestId, 'Create and capture request IDs must differ');
  string(receipt.claim, 'claim', 2048);
  let approval = 'not-issued';
  if (receipt.approvalDigest === null) {
    check(receipt.approvalBinding === null && op.approvalExpiresAt === null && ['PROPOSED','BUDGET_BLOCKED','CANCELLED'].includes(op.status), 'Missing approval for an authorized state');
  } else {
    timestamp(op.approvalExpiresAt, 'approvalExpiresAt');
    check(typeof receipt.approvalDigest === 'string' && /^[a-f0-9]{64}$/.test(receipt.approvalDigest), 'Invalid approval digest');
    const binding = receipt.approvalBinding;
    shape(binding, ['profile','algorithm','encoding','serialization','fields','values'], 'approvalBinding');
    check(binding.profile === 'proofpay-approval-v1' && binding.algorithm === 'SHA-256' && binding.encoding === 'UTF-8' && binding.serialization === 'JSON-array', 'Unsupported approval binding profile');
    check(isDeepStrictEqual(binding.fields, FIELDS), 'Unsupported approval field order');
    const values = [op.id,op.workspaceId,op.sku,op.title,op.amountCents,op.currency,op.merchantId,op.providerMode,op.approvalVersion,op.approvalExpiresAt];
    check(isDeepStrictEqual(binding.values, values), 'Approval binding does not match the operation');
    const calculated = createHash('sha256').update(JSON.stringify(values), 'utf8').digest('hex');
    check(calculated === receipt.approvalDigest, 'Approval digest mismatch'); approval = 'matched';
  }
  check(Array.isArray(receipt.events) && receipt.events.length <= 5000, 'Unsupported event list size');
  const ids = new Set(); let previousTime = 0;
  for (const event of receipt.events) {
    shape(event, ['id','type','detail','createdAt'], 'event'); string(event.id, 'event ID');
    check(!ids.has(event.id), 'Duplicate event ID'); ids.add(event.id);
    check(typeof event.type === 'string' && /^[A-Z][A-Z0-9_]{0,63}$/.test(event.type), 'Unsupported event type encoding');
    string(event.detail, 'event detail', 16384, true); timestamp(event.createdAt, 'event createdAt');
    check(event.createdAt >= previousTime, 'Event time order mismatch'); previousTime = event.createdAt;
  }
  check(Array.isArray(receipt.verificationRecords) && receipt.verificationRecords.length <= 1, 'Unsupported provider record count');
  const verifiedEvents = receipt.events.filter(event => event.type === 'PROVIDER_VERIFIED');
  const confirmations = receipt.events.filter(event => event.type === 'PAYMENT_CONFIRMED');
  const confirmed = op.status === 'CONFIRMED';
  check(receipt.verificationRecords.length === (confirmed ? 1 : 0) && verifiedEvents.length === (confirmed ? 1 : 0) && confirmations.length === (confirmed ? 1 : 0), 'Status and confirmation evidence disagree');
  if (confirmed) {
    check(op.orderId !== null && op.captureId !== null && approval === 'matched', 'Confirmed state lacks payment identities or approval');
    const record = receipt.verificationRecords[0]; verification(record, op);
    check(isDeepStrictEqual(parseReceiptJSON(verifiedEvents[0].detail), record), 'Provider event differs from the exported record');
    check(verifiedEvents[0].createdAt === record.checkedAt && confirmations[0].createdAt === record.checkedAt, 'Confirmation observation timestamps disagree');
  } else {
    check(op.captureId === null, 'Unconfirmed operation contains a capture ID');
  }
  if (['PROPOSED','BUDGET_BLOCKED','APPROVED','CANCELLED','CREATE_DISPATCHED','CREATE_UNKNOWN'].includes(op.status)) check(op.orderId === null, 'Pre-order state contains an order ID');
  else check(op.orderId !== null, 'Post-create state lacks an order ID');
  return {
    consistent:true, receiptSchemaVersion:1, approvalDigest:approval,
    declaredMode:op.providerMode, claimedStatus:op.status, confirmedRecordConsistent:confirmed,
    limits:[
      'Unsigned application-record consistency only; an author can replace both data and digest.',
      'No provider contact, signature, identity, current authority, TIP compatibility or external authenticity verified.',
      'Request text, labels, rationale, request IDs and event prose are not covered by the approval digest.',
      'Event-list completeness and the real-world time of approval are not established.',
      'A recorded sandbox observation does not independently prove a PayPal or model execution.',
    ],
  };
}

async function main() {
  check(process.argv.length === 3, 'Usage: node scripts/verify-receipt.mjs /path/to/receipt.json');
  const file = await open(process.argv[2], 'r');
  let bytes;
  try {
    const info = await file.stat(); check(info.isFile() && info.size <= MAX_RECEIPT_BYTES, 'Expected a regular receipt file no larger than 1 MiB');
    const buffer = Buffer.alloc(MAX_RECEIPT_BYTES + 1); let total = 0;
    while (total < buffer.length) {
      const {bytesRead} = await file.read(buffer, total, buffer.length - total, total);
      if (!bytesRead) break; total += bytesRead;
    }
    check(total <= MAX_RECEIPT_BYTES, 'Receipt exceeds the 1 MiB limit'); bytes = buffer.subarray(0, total);
  } finally { await file.close(); }
  process.stdout.write(`${JSON.stringify(verifyReceipt(parseReceiptJSON(bytes)), null, 2)}\n`);
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => { process.stderr.write(`Receipt verification failed: ${error instanceof SyntaxError ? 'Malformed JSON document' : error.message}\n`); process.exitCode = 1; });
}
