import assert from 'node:assert/strict';
import {test, before, after} from 'node:test';
import {mkdtemp, readFile, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {build} from 'esbuild';
import {ReviewD1} from './review-d1.mjs';
import {MAX_RECEIPT_BYTES, parseReceiptJSON, verifyReceipt} from '../scripts/verify-receipt.mjs';

// Actual local service + SQLite + rehearsal provider exports. No model/PayPal calls.
let temp, service, db, samples;
before(async () => {
  temp = await mkdtemp(join(tmpdir(), 'proofpay-receipt-review-'));
  const bundle = join(temp, 'service.mjs');
  await build({entryPoints:['lib/proofpay/service.ts'],outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
  const {ProofPayService} = await import(pathToFileURL(bundle));
  db = new ReviewD1(join(temp, 'receipt.sqlite'));
  await db.exec(await readFile('drizzle/0000_greedy_living_lightning.sql', 'utf8'));
  service = new ProofPayService({db,env:{},now:()=>1760000000000,ai:async()=>({sku:'workflow-review',rationale:'Local rehearsal fixture.',source:'rehearsal-rule'})});
  await service.start('receipt-owner', 'rehearsal');
  await service.propose('receipt-owner',{request:'Review our workflow',mode:'rehearsal',idempotencyKey:'receipt-review'});
  const op = (await service.state('receipt-owner')).operations[0];
  samples = {proposed:await service.evidence('receipt-owner',op.id)};
  await service.approve('receipt-owner',op.id,1);
  samples.approved = await service.evidence('receipt-owner',op.id);
  await service.createOrder('receipt-owner',op.id,1,'https://proofpay.example');
  samples.ready = await service.evidence('receipt-owner',op.id);
  await service.capture('receipt-owner',op.id,1,'drop-response');
  samples.unknown = await service.evidence('receipt-owner',op.id);
  await service.reconcile('receipt-owner',op.id);
  samples.confirmed = await service.evidence('receipt-owner',op.id);
});
after(async () => { db?.close(); if (temp) await rm(temp,{recursive:true,force:true}); });
const copy = () => structuredClone(samples.confirmed);
const serialize = receipt => parseReceiptJSON(JSON.stringify(receipt));
const reject = mutate => { const receipt = copy(); mutate(receipt); assert.throws(()=>verifyReceipt(serialize(receipt))); };
const replaceObservation = receipt => { receipt.events.find(event=>event.type==='PROVIDER_VERIFIED').detail=JSON.stringify(receipt.verificationRecords[0]); };

test('receipt: actual local service exports verify across proposed, approved, ready, unknown and confirmed states', () => {
  for (const [stage, receipt] of Object.entries(samples)) {
    const result = verifyReceipt(serialize(receipt));
    assert.equal(result.consistent,true,stage); assert.equal(result.declaredMode,'rehearsal');
    assert.equal(result.confirmedRecordConsistent,stage==='confirmed');
    assert.equal(result.approvalDigest,stage==='proposed'?'not-issued':'matched');
  }
});
test('receipt: approval digest from service Web Crypto matches independent Node verifier without changing its algorithm', () => {
  const receipt = samples.confirmed;
  assert.equal(receipt.approvalBinding.values[1], receipt.operation.workspaceId);
  assert.equal(receipt.approvalBinding.profile, 'proofpay-approval-v1');
  assert.equal(createHash('sha256').update(JSON.stringify(receipt.approvalBinding.values),'utf8').digest('hex'),receipt.approvalDigest);
});
for (const [field,index,replacement] of [
  ['id',0,'another-operation'], ['workspaceId',1,'another-workspace'], ['sku',2,'another-sku'],
  ['title',3,'Changed title'], ['amountCents',4,18001], ['currency',5,'EUR'], ['merchantId',6,'another-seller'],
  ['providerMode',7,'sandbox'], ['approvalVersion',8,2], ['approvalExpiresAt',9,1760000900001],
]) {
  test(`receipt: changing ${field} alone or with the binding cannot preserve the digest`, () => {
    reject(receipt=>{ receipt.operation[field]=replacement; });
    reject(receipt=>{ receipt.operation[field]=replacement; receipt.approvalBinding.values[index]=replacement; });
  });
}
test('receipt: profile metadata, field order, legacy schema and extensions fail closed', () => {
  for (const mutate of [
    receipt=>{receipt.receiptSchemaVersion=2;}, receipt=>{delete receipt.receiptSchemaVersion;},
    receipt=>{receipt.approvalBinding.algorithm='SHAKE-256';}, receipt=>{receipt.approvalBinding.profile='CNA';},
    receipt=>{receipt.approvalBinding.fields.reverse();}, receipt=>{receipt.approvalBinding.signature='unverified';},
    receipt=>{receipt.operation.extraAuthority=true;}, receipt=>{receipt.newUnsupportedField=true;},
  ]) reject(mutate);
});
test('receipt: invalid approval field types, numeric bounds, encodings and missing binding are rejected', () => {
  for (const mutate of [
    receipt=>{receipt.operation.amountCents='18000';}, receipt=>{receipt.operation.amountCents=-18000;},
    receipt=>{receipt.operation.amountCents=1.25;}, receipt=>{receipt.operation.amountCents=1000000000000;},
    receipt=>{receipt.operation.approvalVersion=Number.MAX_SAFE_INTEGER+1;},
    receipt=>{receipt.operation.approvalExpiresAt=null;}, receipt=>{receipt.operation.workspaceId='';},
    receipt=>{receipt.operation.title='\ud800';}, receipt=>{receipt.approvalBinding=null;},
    receipt=>{receipt.approvalDigest=null;receipt.approvalBinding=null;receipt.operation.approvalExpiresAt=null;},
  ]) reject(mutate);
});
test('receipt: missing, repeated or contradictory confirmation cannot pass', () => {
  for (const mutate of [
    receipt=>{receipt.verificationRecords=[];}, receipt=>{receipt.verificationRecords.push(receipt.verificationRecords[0]);},
    receipt=>{receipt.events=receipt.events.filter(event=>event.type!=='PROVIDER_VERIFIED');},
    receipt=>{receipt.events=receipt.events.filter(event=>event.type!=='PAYMENT_CONFIRMED');},
    receipt=>{receipt.operation.status='UNKNOWN';}, receipt=>{receipt.operation.captureId=null;},
    receipt=>{receipt.operation.orderId='wrong-order';}, receipt=>{receipt.operation.captureId='wrong-capture';},
  ]) reject(mutate);
});
test('receipt: provider identity, amount, merchant, currency and completion checks survive matching event rewrites', () => {
  for (const mutate of [
    record=>{record.operationId='wrong';}, record=>{record.order.referenceId='wrong';}, record=>{record.order.customId='wrong';},
    record=>{record.order.payeeMerchantId='wrong';}, record=>{record.order.id='wrong';}, record=>{record.capture.id='wrong';},
    record=>{record.order.amount.value='180.01';}, record=>{record.capture.amount.value='179.99';},
    record=>{record.order.amount.currency='EUR';}, record=>{record.capture.amount.currency='EUR';},
    record=>{record.capture.status='PENDING';}, record=>{record.order.status='APPROVED';},
    record=>{record.capture.finalCapture=false;}, record=>{record.capture.finalCapture='true';},
    record=>{record.source='paypal-sandbox-orders-get';}, record=>{record.simulated=false;},
    record=>{record.schemaVersion=2;}, record=>{record.order.amount.value='1.8e2';},
  ]) reject(receipt=>{mutate(receipt.verificationRecords[0]);replaceObservation(receipt);});
});
test('receipt: provider event data and observation timestamps must agree with the exported snapshot', () => {
  reject(receipt=>{receipt.verificationRecords[0].checkedAt++;});
  reject(receipt=>{receipt.events.find(event=>event.type==='PROVIDER_VERIFIED').detail='{}';});
  reject(receipt=>{receipt.events.find(event=>event.type==='PAYMENT_CONFIRMED').createdAt++;});
  reject(receipt=>{receipt.events[1].id=receipt.events[0].id;});
});
test('receipt: JSON parser rejects duplicate decoded keys, malformed UTF-8, trailing content and negative zero', () => {
  for (const json of ['{"a":1,"a":2}','{"a":1,"\\u0061":2}','{"outer":{"a":1,"a":2}}','{} true','{"a":-0}','{"a":1e999}','{"a":"\\ud800"}','{"a":1,}','[1,]']) assert.throws(()=>parseReceiptJSON(json));
  assert.throws(()=>parseReceiptJSON(Buffer.from([0xc3,0x28])));
  assert.deepEqual(parseReceiptJSON('{"a":"quoted \\" value", "list":[null,true,false,1]}'),{a:'quoted " value',list:[null,true,false,1]});
});
test('receipt: file, nesting and event-list limits fail explicitly', () => {
  assert.throws(()=>parseReceiptJSON(' '.repeat(MAX_RECEIPT_BYTES+1)),/1 MiB/);
  assert.throws(()=>parseReceiptJSON('['.repeat(34)+'0'+']'.repeat(34)),/nesting/);
  reject(receipt=>{receipt.events=Array(5001).fill(receipt.events[0]);});
});
test('receipt: formatted JSON preserves the existing ordered-array digest', () => {
  assert.deepEqual(verifyReceipt(parseReceiptJSON(JSON.stringify(samples.confirmed,null,2))),verifyReceipt(serialize(samples.confirmed)));
});
test('receipt: current approval expiry is not checked as permission to execute an old receipt', () => {
  assert.ok(samples.confirmed.operation.approvalExpiresAt < Date.now());
  assert.equal(verifyReceipt(serialize(samples.confirmed)).consistent,true);
});
test('receipt: whole-record reauthoring can pass consistency but never establishes external authenticity', () => {
  const receipt = copy();
  receipt.operation.merchantId='rewritten-seller'; receipt.approvalBinding.values[6]='rewritten-seller';
  receipt.approvalDigest=createHash('sha256').update(JSON.stringify(receipt.approvalBinding.values)).digest('hex');
  receipt.verificationRecords[0].order.payeeMerchantId='rewritten-seller'; replaceObservation(receipt);
  const result=verifyReceipt(serialize(receipt)); assert.equal(result.consistent,true);
  assert.match(result.limits.join(' '),/replace both data and digest/);
  assert.match(result.limits.join(' '),/No provider contact, signature/);
});
test('receipt: CLI exits zero for local rehearsal and nonzero for a mutated record without printing receipt text', async () => {
  const path=join(temp,'receipt.json'); await writeFile(path,JSON.stringify(samples.confirmed));
  const success=spawnSync(process.execPath,[resolve('scripts/verify-receipt.mjs'),path],{encoding:'utf8'});
  assert.equal(success.status,0,success.stderr);assert.equal(JSON.parse(success.stdout).declaredMode,'rehearsal');
  const bad=copy();bad.operation.amountCents++;await writeFile(path,JSON.stringify(bad));
  const failure=spawnSync(process.execPath,[resolve('scripts/verify-receipt.mjs'),path],{encoding:'utf8'});
  assert.equal(failure.status,1);assert.equal(failure.stdout,'');assert.match(failure.stderr,/does not match/);
  const usage=spawnSync(process.execPath,[resolve('scripts/verify-receipt.mjs')],{encoding:'utf8'});
  assert.equal(usage.status,1);assert.match(usage.stderr,/Usage:/);
});
