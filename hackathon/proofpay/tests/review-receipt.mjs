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
let temp, service, db, samples, diagnostics;
before(async () => {
  temp = await mkdtemp(join(tmpdir(), 'proofpay-receipt-review-'));
  const bundle = join(temp, 'service.mjs');
  await build({entryPoints:['lib/proofpay/service.ts'],outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
  const {ProofPayService} = await import(pathToFileURL(bundle));
  db = new ReviewD1(join(temp, 'receipt.sqlite'));
  await db.exec(await readFile('drizzle/0000_greedy_living_lightning.sql', 'utf8'));await db.exec(await readFile('drizzle/0003_business_profiles.sql','utf8'));
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
  // This exercises diagnostic exports with synthetic provider responses only.
  // It does not establish a PayPal sandbox run or AI execution.
  let syntheticOrder;
  const calls={ai:0,create:0,capture:0,get:0};
  const diagnosticService = new ProofPayService({db,env:{PAYPAL_CLIENT_ID:'test-only-client',PAYPAL_CLIENT_SECRET:'test-only-secret',PAYPAL_MERCHANT_ID:'synthetic-diagnostic-seller'},now:()=>1760000000000,
    ai:async()=>{calls.ai++;throw Error('The diagnostic must not call a model');},
    provider:{
      create:async operation=>{
        calls.create++;
        syntheticOrder={id:'SYNTHETIC-DIAGNOSTIC-ORDER',status:'APPROVED',purchase_units:[{reference_id:operation.id,custom_id:operation.id,payee:{merchant_id:operation.merchant_id},amount:{currency_code:'USD',value:'180.00'}}]};
        return structuredClone(syntheticOrder);
      },
      capture:async()=>{
        calls.capture++;syntheticOrder.status='COMPLETED';
        syntheticOrder.purchase_units[0].payments={captures:[{id:'SYNTHETIC-DIAGNOSTIC-CAPTURE',status:'COMPLETED',final_capture:true,amount:{currency_code:'USD',value:'180.00'}}]};
        return structuredClone(syntheticOrder);
      },
      get:async()=>{calls.get++;return structuredClone(syntheticOrder);},
    },
  });
  const diagnosticOp=(await diagnosticService.startSandboxDiagnostic('diagnostic-owner')).operations[0];
  diagnostics={proposed:await diagnosticService.evidence('diagnostic-owner',diagnosticOp.id),calls};
  await diagnosticService.approve('diagnostic-owner',diagnosticOp.id,1);
  await diagnosticService.createOrder('diagnostic-owner',diagnosticOp.id,1,'https://proofpay.example');
  await diagnosticService.capture('diagnostic-owner',diagnosticOp.id,1);
  diagnostics.confirmed=await diagnosticService.evidence('diagnostic-owner',diagnosticOp.id);
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
test('receipt: actual diagnostic service export with synthetic provider remains explicitly manual/no-AI', () => {
  for (const receipt of [diagnostics.proposed,diagnostics.confirmed]) {
    const result=verifyReceipt(serialize(receipt));
    assert.equal(result.consistent,true);assert.equal(result.declaredMode,'sandbox');
    assert.equal(result.declaredProposalSource,'sandbox-diagnostic');
    assert.equal(result.proposalInterpretation,'Manual PayPal sandbox diagnostic; no AI proposal is claimed.');
    assert.equal(result.confirmedRecordConsistent,receipt.operation.status==='CONFIRMED');
  }
  // One lookup checks buyer approval before capture; another confirms its result.
  assert.deepEqual(diagnostics.calls,{ai:0,create:1,capture:1,get:2});
});
test('receipt: diagnostic source is forbidden in rehearsal and for unknown source spellings', () => {
  reject(receipt=>{receipt.operation.aiSource='sandbox-diagnostic';});
  for (const source of ['manual','sandbox_diagnostic','SANDBOX-DIAGNOSTIC']) {
    const receipt=structuredClone(diagnostics.proposed);receipt.operation.aiSource=source;
    assert.throws(()=>verifyReceipt(serialize(receipt)),/Unsupported proposal source/);
  }
});
test('receipt: diagnostic metadata cannot claim AI execution, omit provenance boundaries or change the fixed item', () => {
  for (const mutate of [
    proposal=>{proposal.aiCalled=true;},proposal=>{proposal.manual=false;},
    proposal=>{proposal.source='model';},proposal=>{proposal.diagnosticProfile='unknown-v2';},
    proposal=>{proposal.schemaVersion=2;},proposal=>{delete proposal.aiCalled;},
    proposal=>{proposal.provenance={requestedModel:'pretend-model'};},
    proposal=>{proposal.sku='design-review';},proposal=>{proposal.rationale='different explanation';},
  ]) {
    const receipt=structuredClone(diagnostics.confirmed);
    const event=receipt.events.find(item=>item.type==='PROPOSAL_CREATED');
    const proposal=JSON.parse(event.detail);mutate(proposal);event.detail=JSON.stringify(proposal);
    assert.throws(()=>verifyReceipt(serialize(receipt)));
  }
  for (const mutate of [
    receipt=>{receipt.events=receipt.events.filter(event=>event.type!=='PROPOSAL_CREATED');},
    receipt=>{receipt.operation.amountCents=16000;},receipt=>{receipt.operation.sku='design-review';},
  ]) {
    const receipt=structuredClone(diagnostics.proposed);mutate(receipt);
    assert.throws(()=>verifyReceipt(serialize(receipt)));
  }
});
test('receipt: accepting diagnostic proposals does not relax approval or provider consistency', () => {
  for (const mutate of [
    receipt=>{receipt.operation.merchantId='other-seller';},receipt=>{receipt.approvalDigest='0'.repeat(64);},
    receipt=>{receipt.verificationRecords[0].capture.amount.value='179.99';replaceObservation(receipt);},
    receipt=>{receipt.verificationRecords[0].simulated=true;replaceObservation(receipt);},
    receipt=>{receipt.verificationRecords=[];},
  ]) {
    const receipt=structuredClone(diagnostics.confirmed);mutate(receipt);
    assert.throws(()=>verifyReceipt(serialize(receipt)));
  }
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
