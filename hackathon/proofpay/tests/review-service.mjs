import assert from 'node:assert/strict';
import { test, after } from 'node:test';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { fork, spawnSync } from 'node:child_process';
import { build } from 'esbuild';
import { ReviewD1 } from './review-d1.mjs';

const temp = await mkdtemp(join(tmpdir(), 'proofpay-independent-'));
const bundle = join(temp, 'service.mjs');
const providerBundle = join(temp, 'provider.mjs');
await build({entryPoints:['lib/proofpay/service.ts'],outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
await build({entryPoints:['lib/proofpay/provider.ts'],outfile:providerBundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
const { ProofPayService } = await import(pathToFileURL(bundle));
const { RehearsalProvider } = await import(pathToFileURL(providerBundle));
const schema = await readFile('drizzle/0000_greedy_living_lightning.sql','utf8');
after(async () => { await rm(temp,{recursive:true,force:true}); });
let fixtureCount = 0;
const owner = 'independent-review-owner';
async function fixture(mode='rehearsal') {
  const filename = join(temp,`case-${fixtureCount++}.sqlite`);
  const db = new ReviewD1(filename);
  await db.exec(schema);
  let now = Date.now();
  const calls = {create:0,capture:0,get:0};
  const durable = new RehearsalProvider(db,()=>now);
  const provider = {create:async(...args)=>{calls.create++;return durable.create(...args)},capture:async(...args)=>{calls.capture++;return durable.capture(...args)},get:async(...args)=>{calls.get++;return durable.get(...args)}};
  const env = mode==='sandbox' ? {PAYPAL_CLIENT_ID:'test-client',PAYPAL_CLIENT_SECRET:'test-secret',PAYPAL_MERCHANT_ID:'test-seller',AI_API_KEY:'test-only-key',AI_BASE_URL:'https://test-model.invalid/v1',AI_MODEL:'synthetic-review-model'} : {};
  const service = new ProofPayService({db,env,provider,now:()=>now,ai:async request=>({sku:request.includes('design')?'design-review':'workflow-review',rationale:'Test stub, not actual model evidence.',source:mode==='sandbox'?'model':'rehearsal-rule'})});
  let state = await service.start(owner,mode,mode==='rehearsal');
  if(mode==='sandbox') state=await service.propose(owner,{request:'workflow review',mode,idempotencyKey:'sandbox-test-key'});
  const op=state.operations.find(o=>o.amountCents===18000);
  return {db,service,provider,durable,calls,filename,env,op,advance:ms=>{now+=ms;}};
}
async function ready(f) { await f.service.approve(owner,f.op.id,1); await f.service.createOrder(owner,f.op.id,1,'https://proofpay.example'); }
async function row(f) { return f.db.prepare('SELECT * FROM proofpay_operations WHERE id=?').bind(f.op.id).first(); }
function contender(filename,id) {
  const child=fork(resolve('tests/review-worker.mjs'),[filename,bundle,owner,id],{stdio:['ignore','pipe','pipe','ipc']});
  let resolveReady; let resolveResult; let rejectResult; let stderr='';
  const ready=new Promise(resolve=>{resolveReady=resolve});
  const result=new Promise((resolve,reject)=>{resolveResult=resolve;rejectResult=reject});
  child.stderr.on('data',data=>{stderr+=data});
  child.on('message',message=>{if(message.ready)resolveReady();else resolveResult(message)});
  child.on('error',rejectResult);
  child.on('exit',code=>{if(code)rejectResult(new Error(`Contender exited ${code}: ${stderr}`))});
  return {child,ready,result};
}

test('review: two actual processes contend at atomic reservation boundary; only one fits $300',{timeout:15000},async()=>{
  const f=await fixture();
  try {
    const ops=(await f.service.state(owner)).operations;
    const a=contender(f.filename,ops[0].id), b=contender(f.filename,ops[1].id);
    await Promise.all([a.ready,b.ready]);a.child.send('go');b.child.send('go');
    const outcomes=await Promise.all([a.result,b.result]);
    assert.equal(outcomes.filter(x=>x.ok).length,1);
    assert.equal(outcomes.find(x=>!x.ok).code,'BUDGET_EXCEEDED');
    const raw=await f.db.prepare("SELECT status,amount_cents FROM proofpay_operations").all();
    assert.equal(raw.results.filter(x=>x.status==='APPROVED').length,1);
    assert.equal(raw.results.filter(x=>x.status==='BUDGET_BLOCKED').length,1);
    const held=raw.results.filter(x=>x.status==='APPROVED').reduce((n,x)=>n+x.amount_cents,0);
    assert.ok(held===18000 || held===16000);
    assert.ok(held<=30000);
    assert.equal(f.calls.create+f.calls.capture,0);
  } finally {f.db.close();}
});

test('review: competing capture requests invoke the provider capture only once',async()=>{
  const f=await fixture();
  try {await ready(f);await Promise.allSettled([f.service.capture(owner,f.op.id,1),f.service.capture(owner,f.op.id,1)]);
    assert.equal(f.calls.capture,1);assert.equal((await row(f)).status,'CONFIRMED');
    assert.equal((await f.service.state(owner)).workspace.committedCents,18000);
    assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE type='PAYMENT_CONFIRMED'").first()).n,1);
  } finally {f.db.close();}
});

test('review: response loss survives fresh process and reconciliation makes zero capture calls',async()=>{
  const f=await fixture();let closed=false;
  try {await ready(f);await f.service.capture(owner,f.op.id,1,'drop-response');
    const before=await row(f);assert.equal(before.status,'UNKNOWN');assert.equal(f.calls.capture,1);
    assert.equal((await f.service.state(owner)).workspace.reservedCents,18000);
    f.db.close();closed=true;
    const code=`import {ReviewD1} from ${JSON.stringify(pathToFileURL(resolve('tests/review-d1.mjs')).href)};import {ProofPayService} from ${JSON.stringify(pathToFileURL(bundle).href)};import {RehearsalProvider} from ${JSON.stringify(pathToFileURL(providerBundle).href)};const db=new ReviewD1(${JSON.stringify(f.filename)});const p=new RehearsalProvider(db,Date.now);let captures=0;const provider={get:p.get.bind(p),create:()=>{throw Error('forbidden create')},capture:()=>{captures++;throw Error('forbidden capture')}};const service=new ProofPayService({db,env:{},provider});await service.reconcile(${JSON.stringify(owner)},${JSON.stringify(f.op.id)});await service.reconcile(${JSON.stringify(owner)},${JSON.stringify(f.op.id)});console.log(JSON.stringify({state:await service.state(${JSON.stringify(owner)}),captures}));db.close();`;
    const restarted=spawnSync(process.execPath,['--input-type=module','-e',code],{encoding:'utf8'});
    assert.equal(restarted.status,0,restarted.stderr);
    const result=JSON.parse(restarted.stdout.trim());assert.equal(result.captures,0);
    assert.equal(result.state.workspace.committedCents,18000);assert.equal(result.state.workspace.reservedCents,0);
    const reopened=new ReviewD1(f.filename);try {
      const after=await reopened.prepare('SELECT * FROM proofpay_operations WHERE id=?').bind(f.op.id).first();
      assert.equal(after.capture_request_id,before.capture_request_id);assert.equal(after.order_id,before.order_id);assert.equal(after.status,'CONFIRMED');
      assert.equal((await reopened.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE type='PAYMENT_CONFIRMED'").first()).n,1);
      assert.equal((await reopened.prepare('SELECT capture_calls FROM proofpay_rehearsal_orders WHERE operation_id=?').bind(f.op.id).first()).capture_calls,1);
    } finally {reopened.close();}
  } finally {if(!closed)f.db.close();}
});

test('review: expired execution authority forbids capture but does not erase reserved funds',async()=>{
  const f=await fixture();try {await ready(f);f.advance(16*60*1000);
    await assert.rejects(f.service.capture(owner,f.op.id,1),e=>e.code==='APPROVAL_EXPIRED');
    assert.equal(f.calls.capture,0);assert.equal((await f.service.state(owner)).workspace.reservedCents,18000);
  } finally {f.db.close();}
});
test('review: reconciliation remains allowed after approval expiry for already dispatched work',async()=>{
  const f=await fixture();try {await ready(f);await f.service.capture(owner,f.op.id,1,'drop-response');f.advance(16*60*1000);await f.service.reconcile(owner,f.op.id);assert.equal((await row(f)).status,'CONFIRMED');assert.equal(f.calls.capture,1);}finally{f.db.close();}
});
test('review: mutation of an approved amount is caught before any provider create',async()=>{
  const f=await fixture();try {await f.service.approve(owner,f.op.id,1);await f.db.prepare('UPDATE proofpay_operations SET amount_cents=1 WHERE id=?').bind(f.op.id).run();await assert.rejects(f.service.createOrder(owner,f.op.id,1,'https://proofpay.example'),e=>e.code==='APPROVAL_MISMATCH');assert.equal(f.calls.create,0);}finally{f.db.close();}
});
test('review: wrong approval version and foreign owner cause no provider call or foreign evidence',async()=>{
  const f=await fixture();try {
    await assert.rejects(f.service.approve(owner,f.op.id,999),e=>e.code==='APPROVAL_VERSION');
    for(const action of [()=>f.service.approve('foreign',f.op.id,1),()=>f.service.evidence('foreign',f.op.id),()=>f.service.reconcile('foreign',f.op.id)])await assert.rejects(action(),e=>e.code==='NOT_FOUND');
    assert.deepEqual(f.calls,{create:0,capture:0,get:0});
  }finally{f.db.close();}
});
test('review: unavailable lookup retains unknown state and never retries capture',async()=>{
  const f=await fixture();try {await ready(f);await f.service.capture(owner,f.op.id,1,'drop-response');f.provider.get=async()=>{throw Error('lookup unavailable')};
    await assert.rejects(f.service.reconcile(owner,f.op.id),e=>e.code==='VERIFICATION_UNAVAILABLE');
    await assert.rejects(f.service.capture(owner,f.op.id,1),e=>e.code==='CAPTURE_STATE');
    const state=await f.service.state(owner);assert.equal(state.workspace.reservedCents,18000);assert.equal(state.workspace.committedCents,0);assert.equal((await row(f)).status,'UNKNOWN');assert.equal(f.calls.capture,1);
  }finally{f.db.close();}
});
test('review: mismatched provider evidence never confirms and never releases funds',async()=>{
  const f=await fixture();try {await ready(f);await f.service.capture(owner,f.op.id,1,'drop-response');f.provider.get=async op=>{const record=await f.durable.get(op);record.purchase_units[0].payee.merchant_id='foreign-seller';return record;};
    await assert.rejects(f.service.reconcile(owner,f.op.id),e=>e.code==='VERIFICATION_REVIEW');
    assert.equal((await row(f)).status,'REVIEW');assert.equal((await f.service.state(owner)).workspace.reservedCents,18000);assert.equal(f.calls.capture,1);
  }finally{f.db.close();}
});
test('review: sandbox without configuration cannot silently start rehearsal',async()=>{
  const f=await fixture();try {const before=await f.service.state(owner);await assert.rejects(f.service.start(owner,'sandbox'),e=>e.code==='PAYPAL_NOT_CONFIGURED');assert.equal((await f.service.state(owner)).workspace.id,before.workspace.id);assert.deepEqual(f.calls,{create:0,capture:0,get:0});}finally{f.db.close();}
});
test('review: duplicate proposal key is bound to original request and yields one operation',async()=>{
  const f=await fixture();try {await f.service.propose(owner,{mode:'rehearsal',request:'workflow review',idempotencyKey:'review-duplicate-key'});await f.service.propose(owner,{mode:'rehearsal',request:'workflow review',idempotencyKey:'review-duplicate-key'});await assert.rejects(f.service.propose(owner,{mode:'rehearsal',request:'design review',idempotencyKey:'review-duplicate-key'}),e=>e.code==='KEY_REUSED');assert.equal((await f.db.prepare('SELECT COUNT(*) n FROM proofpay_operations WHERE idempotency_key=?').bind('review-duplicate-key').first()).n,1);}finally{f.db.close();}
});
test('review: reset cannot hide a sandbox operation with held funds',async()=>{
  const f=await fixture('sandbox');try {await ready(f);await f.service.capture(owner,f.op.id,1,'drop-response');const before=await f.service.state(owner);
    await assert.rejects(f.service.start(owner,'rehearsal',true));
    const after=await f.service.state(owner);assert.equal(after.workspace.id,before.workspace.id);assert.equal(after.workspace.reservedCents,18000);assert.equal(after.operations[0].status,'UNKNOWN');
  }finally{f.db.close();}
});
test('review: missing native buyer approval prevents capture dispatch',async()=>{
  const f=await fixture();try {await ready(f);f.provider.get=async op=>{const data=await f.durable.get(op);data.status='CREATED';return data;};
    await assert.rejects(f.service.capture(owner,f.op.id,1),error=>error.code==='BUYER_APPROVAL_REQUIRED');
    assert.equal(f.calls.capture,0);assert.equal((await row(f)).status,'ORDER_READY');assert.equal((await f.service.state(owner)).workspace.reservedCents,18000);
  }finally{f.db.close();}
});
test('review: lost order-create response holds funds and cannot automatically create again',async()=>{
  const f=await fixture();try {await f.service.approve(owner,f.op.id,1);f.provider.create=async()=>{f.calls.create++;throw Error('response lost')};
    await assert.rejects(f.service.createOrder(owner,f.op.id,1,'https://proofpay.example'),error=>error.code==='CREATE_UNKNOWN');
    await assert.rejects(f.service.createOrder(owner,f.op.id,1,'https://proofpay.example'),error=>error.code==='ORDER_STATE');
    assert.equal(f.calls.create,1);assert.equal((await row(f)).status,'CREATE_UNKNOWN');assert.equal((await f.service.state(owner)).workspace.reservedCents,18000);
  }finally{f.db.close();}
});
test('review: provider pending result cannot produce confirmation or release reservation',async()=>{
  const f=await fixture();try {await ready(f);await f.service.capture(owner,f.op.id,1,'drop-response');f.provider.get=async op=>{const data=await f.durable.get(op);data.purchase_units[0].payments.captures[0].status='PENDING';return data;};
    await f.service.reconcile(owner,f.op.id);assert.equal((await row(f)).status,'UNKNOWN');assert.equal((await f.service.state(owner)).workspace.reservedCents,18000);assert.equal(f.calls.capture,1);
  }finally{f.db.close();}
});
for(const mode of ['rehearsal','sandbox'])test(`review: ${mode} receipt retains matched fields once and excludes unrelated provider secrets`,async()=>{
  const f=await fixture(mode);try {
    await ready(f);
    f.provider.get=async op=>{
      const data=await f.durable.get(op);
      data.access_token='SECRET_PROVIDER_ACCESS_TOKEN';
      data.payer={email_address:'PRIVATE_PAYER_EMAIL',address:{address_line_1:'PRIVATE_STREET'}};
      data.purchase_units[0].payee.email_address='PRIVATE_SELLER_EMAIL';
      data.links=[{href:'https://example.invalid/?client_secret=SECRET_QUERY',rel:'self'}];
      if(data.purchase_units[0].payments) data.purchase_units[0].payments.captures[0].internal={authorization:'SECRET_AUTHORIZATION'};
      return data;
    };
    await f.service.capture(owner,f.op.id,1);
    await f.service.reconcile(owner,f.op.id);
    const receipt=await f.service.evidence(owner,f.op.id);
    assert.equal(receipt.verificationRecords.length,1);
    const record=receipt.verificationRecords[0];
    assert.deepEqual(Object.keys(record).sort(),['schemaVersion','mode','simulated','source','checkedAt','operationId','order','capture'].sort());
    assert.equal(record.mode,mode);assert.equal(record.simulated,mode==='rehearsal');
    assert.equal(record.source,mode==='rehearsal'?'simulated-provider-lookup':'paypal-sandbox-orders-get');
    assert.equal(record.schemaVersion,1);assert.equal(typeof record.checkedAt,'number');assert.equal(record.operationId,f.op.id);
    const stored=await row(f);
    assert.deepEqual(record.order,{id:stored.order_id,status:'COMPLETED',referenceId:f.op.id,customId:f.op.id,payeeMerchantId:stored.merchant_id,amount:{value:'180.00',currency:'USD'}});
    assert.deepEqual(record.capture,{id:stored.capture_id,status:'COMPLETED',finalCapture:true,amount:{value:'180.00',currency:'USD'}});
    const text=JSON.stringify(receipt);
    for(const forbidden of ['SECRET_PROVIDER_ACCESS_TOKEN','PRIVATE_PAYER_EMAIL','PRIVATE_STREET','PRIVATE_SELLER_EMAIL','SECRET_QUERY','SECRET_AUTHORIZATION'])assert.ok(!text.includes(forbidden),forbidden);
    assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE operation_id=? AND type='PROVIDER_VERIFIED'").bind(f.op.id).first()).n,1);
  }finally{f.db.close();}
});
test('review: duplicate provider capture binding rolls back receipt and confirmation atomically',async()=>{
  const f=await fixture();try {
    await ready(f);await f.service.capture(owner,f.op.id,1);
    const first=await row(f);
    const secondService=new ProofPayService({db:f.db,env:{},provider:f.provider,ai:async()=>({sku:'starter-review',rationale:'Synthetic smaller item.',source:'rehearsal-rule'})});
    await secondService.propose(owner,{mode:'rehearsal',request:'smaller starter review',idempotencyKey:'atomic-rollback-key'});
    const second=(await secondService.state(owner)).operations.find(op=>op.sku==='starter-review');
    await secondService.approve(owner,second.id,1);await secondService.createOrder(owner,second.id,1,'https://proofpay.example');
    await secondService.capture(owner,second.id,1,'drop-response');
    f.provider.get=async op=>{const data=await f.durable.get(op);data.purchase_units[0].payments.captures[0].id=first.capture_id;return data;};
    await assert.rejects(secondService.reconcile(owner,second.id),error=>error.code==='VERIFICATION_UNAVAILABLE');
    const secondRow=await f.db.prepare('SELECT * FROM proofpay_operations WHERE id=?').bind(second.id).first();
    assert.equal(secondRow.status,'UNKNOWN');assert.equal(secondRow.capture_id,null);
    assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE operation_id=? AND type IN ('PROVIDER_VERIFIED','PAYMENT_CONFIRMED')").bind(second.id).first()).n,0);
    const state=await secondService.state(owner);assert.equal(state.workspace.committedCents,18000);assert.equal(state.workspace.reservedCents,9000);
  }finally{f.db.close();}
});

// Renewal is a new owner decision over the same held purchase, never a retry
// permission for a dispatched request. These fixtures remain synthetic.
const renewalCount = f => f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE operation_id=? AND type='APPROVAL_RENEWED'").bind(f.op.id).first();
function unchangedPurchase(before, after) {
  for(const key of ['id','workspace_id','sku','title','amount_cents','currency','merchant_id','mode','status','order_id','capture_id','create_request_id','capture_request_id','approval_url']) assert.equal(after[key],before[key],key);
}
for(const status of ['APPROVED','ORDER_READY'])test(`review: expired ${status} renewal preserves purchase and allowance, then executes only the new version`,async()=>{
  const f=await fixture('sandbox');try {
    await f.service.approve(owner,f.op.id,1);
    if(status==='ORDER_READY') await f.service.createOrder(owner,f.op.id,1,'https://proofpay.example');
    const before=await row(f), budgetBefore=(await f.service.state(owner)).workspace;
    const callsBefore={...f.calls};f.advance(16*60*1000);
    await f.service.renewApproval(owner,f.op.id,1);
    const renewed=await row(f), budgetAfter=(await f.service.state(owner)).workspace;
    unchangedPurchase(before,renewed);
    assert.deepEqual(budgetAfter,budgetBefore);assert.deepEqual(f.calls,callsBefore);
    assert.equal(renewed.approval_version,2);assert.notEqual(renewed.approval_digest,before.approval_digest);
    assert.ok(renewed.approval_expires_at>before.approval_expires_at);
    assert.equal((await renewalCount(f)).n,1);
    await assert.rejects(f.service.renewApproval(owner,f.op.id,1),e=>e.code==='APPROVAL_VERSION');
    if(status==='APPROVED') {
      await assert.rejects(f.service.createOrder(owner,f.op.id,1,'https://proofpay.example'),e=>e.code==='APPROVAL_VERSION');
      assert.deepEqual(f.calls,callsBefore);
      await f.service.createOrder(owner,f.op.id,2,'https://proofpay.example');
    }
    await assert.rejects(f.service.capture(owner,f.op.id,1),e=>e.code==='APPROVAL_VERSION');
    assert.equal(f.calls.capture,0);
    await f.service.capture(owner,f.op.id,2);
    const final=await row(f);
    assert.equal(final.status,'CONFIRMED');assert.equal(f.calls.create,1);assert.equal(f.calls.capture,1);
    assert.equal(final.create_request_id,before.create_request_id);assert.equal(final.capture_request_id,before.capture_request_id);
    if(status==='ORDER_READY')assert.equal(final.order_id,before.order_id);
    const budget=(await f.service.state(owner)).workspace;
    assert.equal(budget.committedCents,18000);assert.equal(budget.reservedCents,0);assert.equal(budget.availableCents,12000);
  }finally{f.db.close();}
});
test('review: renewal before expiry and by a foreign owner cannot change authority',async()=>{
  const f=await fixture('sandbox');try {
    await ready(f);const before=await row(f),callsBefore={...f.calls};
    await assert.rejects(f.service.renewApproval(owner,f.op.id,1),e=>e.code==='APPROVAL_NOT_EXPIRED');
    f.advance(16*60*1000);
    await assert.rejects(f.service.renewApproval('foreign-owner',f.op.id,1),e=>e.code==='NOT_FOUND');
    assert.deepEqual(await row(f),before);assert.deepEqual(f.calls,callsBefore);assert.equal((await renewalCount(f)).n,0);
  }finally{f.db.close();}
});
for(const status of ['PROPOSED','BUDGET_BLOCKED','CREATE_DISPATCHED','CREATE_UNKNOWN','CAPTURE_DISPATCHED','UNKNOWN','REVIEW','CONFIRMED'])test(`review: renewal rejects ${status} without creating new authority or provider calls`,async()=>{
  const f=await fixture('sandbox');try {
    await ready(f);f.advance(16*60*1000);
    await f.db.prepare('UPDATE proofpay_operations SET status=? WHERE id=?').bind(status,f.op.id).run();
    const before=await row(f),budgetBefore=(await f.service.state(owner)).workspace,callsBefore={...f.calls};
    await assert.rejects(f.service.renewApproval(owner,f.op.id,1),e=>e.code==='RENEWAL_STATE');
    assert.deepEqual(await row(f),before);assert.deepEqual((await f.service.state(owner)).workspace,budgetBefore);
    assert.deepEqual(f.calls,callsBefore);assert.equal((await renewalCount(f)).n,0);
  }finally{f.db.close();}
});
test('review: renewal does not legitimize a mutated purchase or a changed sandbox merchant',async()=>{
  const f=await fixture('sandbox');try {
    await ready(f);f.advance(16*60*1000);const callsBefore={...f.calls};
    await f.db.prepare('UPDATE proofpay_operations SET amount_cents=1 WHERE id=?').bind(f.op.id).run();
    await assert.rejects(f.service.renewApproval(owner,f.op.id,1),e=>e.code==='APPROVAL_MISMATCH');
    await f.db.prepare('UPDATE proofpay_operations SET amount_cents=18000 WHERE id=?').bind(f.op.id).run();
    f.env.PAYPAL_MERCHANT_ID='changed-test-seller';
    await assert.rejects(f.service.renewApproval(owner,f.op.id,1),e=>e.code==='MERCHANT_CHANGED');
    assert.equal((await row(f)).approval_version,1);assert.deepEqual(f.calls,callsBefore);assert.equal((await renewalCount(f)).n,0);
  }finally{f.db.close();}
});
test('review: renewal cannot reactivate a purchase in an inactive rehearsal workspace',async()=>{
  const f=await fixture();try {
    await ready(f);f.advance(16*60*1000);const before=await row(f),callsBefore={...f.calls};
    await f.service.start(owner,'rehearsal',true);
    await assert.rejects(f.service.renewApproval(owner,f.op.id,1),e=>e.code==='WORKSPACE_CHANGED');
    assert.deepEqual(await row(f),before);assert.deepEqual(f.calls,callsBefore);assert.equal((await renewalCount(f)).n,0);
  }finally{f.db.close();}
});
test('review: competing renewals advance the version once and record one owner decision',async()=>{
  const f=await fixture('sandbox');try {
    await ready(f);f.advance(16*60*1000);const before=await row(f),callsBefore={...f.calls};
    // D1 serializes atomic batches. Queue them here because this adapter shares
    // one synchronous SQLite connection; both service calls still read version1.
    const batch=f.db.batch.bind(f.db);let queued=Promise.resolve();
    f.db.batch=statements=>{const result=queued.then(()=>batch(statements));queued=result.catch(()=>{});return result};
    const results=await Promise.allSettled([f.service.renewApproval(owner,f.op.id,1),f.service.renewApproval(owner,f.op.id,1)]);
    assert.equal(results.filter(x=>x.status==='fulfilled').length,1);
    assert.ok(['APPROVAL_CHANGED','APPROVAL_VERSION'].includes(results.find(x=>x.status==='rejected').reason.code));
    const after=await row(f);unchangedPurchase(before,after);assert.equal(after.approval_version,2);
    assert.deepEqual(f.calls,callsBefore);assert.equal((await renewalCount(f)).n,1);
    assert.equal((await f.service.state(owner)).workspace.reservedCents,18000);
  }finally{f.db.close();}
});
test('review: renewal invalidates a capture suspended at the provider buyer-approval lookup',{timeout:5000},async()=>{
  const f=await fixture('sandbox');let release;
  try {
    await ready(f);let entered;const arrived=new Promise(resolve=>{entered=resolve});const gate=new Promise(resolve=>{release=resolve});
    const get=f.provider.get;f.provider.get=async op=>{entered();await gate;return get(op)};
    const stale=f.service.capture(owner,f.op.id,1);const staleResult=Promise.allSettled([stale]);
    await arrived;f.advance(16*60*1000);await f.service.renewApproval(owner,f.op.id,1);
    release();await staleResult;
    assert.equal(f.calls.capture,0);assert.equal((await row(f)).status,'ORDER_READY');assert.equal((await row(f)).approval_version,2);
    f.provider.get=get;await f.service.capture(owner,f.op.id,2);
    assert.equal(f.calls.capture,1);assert.equal((await row(f)).status,'CONFIRMED');
  }finally{release?.();f.db.close();}
});
test('review: renewal invalidates a create suspended just before its durable dispatch claim',{timeout:5000},async()=>{
  const f=await fixture('sandbox');let release;const originalPrepare=f.db.prepare.bind(f.db);
  try {
    await f.service.approve(owner,f.op.id,1);
    let entered;const arrived=new Promise(resolve=>{entered=resolve});const gate=new Promise(resolve=>{release=resolve});
    f.db.prepare=sql=>{
      const statement=originalPrepare(sql);
      if(sql.includes("SET status = 'CREATE_DISPATCHED'")) {
        const originalBind=statement.bind.bind(statement);
        statement.bind=(...args)=>{const bound=originalBind(...args);const first=bound.first.bind(bound);bound.first=async(...parameters)=>{entered();await gate;return first(...parameters)};return bound};
      }
      return statement;
    };
    const stale=f.service.createOrder(owner,f.op.id,1,'https://proofpay.example');const staleResult=Promise.allSettled([stale]);
    await arrived;f.advance(16*60*1000);await f.service.renewApproval(owner,f.op.id,1);
    release();await staleResult;
    assert.equal(f.calls.create,0);assert.equal((await row(f)).status,'APPROVED');assert.equal((await row(f)).approval_version,2);
    f.db.prepare=originalPrepare;await f.service.createOrder(owner,f.op.id,2,'https://proofpay.example');
    assert.equal(f.calls.create,1);assert.equal((await row(f)).status,'ORDER_READY');
  }finally{release?.();f.db.prepare=originalPrepare;f.db.close();}
});
test('review: a dispatch claim winning after renewal pre-read prevents renewal and its event',{timeout:5000},async()=>{
  const f=await fixture('sandbox');let release;const batch=f.db.batch.bind(f.db);
  try {
    await ready(f);f.advance(16*60*1000);const before=await row(f),callsBefore={...f.calls};
    let entered;const arrived=new Promise(resolve=>{entered=resolve});const gate=new Promise(resolve=>{release=resolve});
    f.db.batch=async statements=>{entered();await gate;return batch(statements)};
    const renewal=f.service.renewApproval(owner,f.op.id,1);const outcome=Promise.allSettled([renewal]);
    await arrived;
    // A separate dispatcher wins the status CAS while renewal holds a stale read.
    await f.db.prepare("UPDATE proofpay_operations SET status='CAPTURE_DISPATCHED' WHERE id=? AND status='ORDER_READY'").bind(f.op.id).run();
    release();const [result]=await outcome;
    assert.equal(result.status,'rejected');assert.equal(result.reason.code,'APPROVAL_CHANGED');
    const after=await row(f);assert.equal(after.status,'CAPTURE_DISPATCHED');assert.equal(after.approval_version,before.approval_version);assert.equal(after.approval_digest,before.approval_digest);
    assert.equal((await renewalCount(f)).n,0);assert.deepEqual(f.calls,callsBefore);assert.equal((await f.service.state(owner)).workspace.reservedCents,18000);
  }finally{release?.();f.db.batch=batch;f.db.close();}
});
