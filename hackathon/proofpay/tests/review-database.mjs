import assert from 'node:assert/strict';
import {test,after} from 'node:test';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {fork} from 'node:child_process';
import {build} from 'esbuild';
import {ReviewD1} from './review-d1.mjs';

// These are real SQLite state/rollback checks with synthetic integrations.
// They do not claim equivalence with hosted D1 or trusted ingress behavior.
const temp=await mkdtemp(join(tmpdir(),'proofpay-db-independent-'));
const bundle=join(temp,'core.mjs');
await build({entryPoints:['lib/proofpay/service.ts'],outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
const {ProofPayService}=await import(pathToFileURL(bundle));
const schema=await readFile('drizzle/0000_greedy_living_lightning.sql','utf8') + '\n' + await readFile('drizzle/0003_business_profiles.sql','utf8');
after(()=>rm(temp,{recursive:true,force:true}));
let serial=0;
async function fixture() {
  const db=new ReviewD1(join(temp,`db-${serial++}.sqlite`));await db.exec(schema);
  const calls={create:0,capture:0,get:0,ai:0};
  const service=new ProofPayService({db,env:{},provider:{create:async()=>{calls.create++;throw Error('provider forbidden')},capture:async()=>{calls.capture++;throw Error('provider forbidden')},get:async()=>{calls.get++;throw Error('provider forbidden')}},ai:async request=>{calls.ai++;return {sku:request.includes('design')?'design-review':'workflow-review',source:'rehearsal-rule',rationale:'Synthetic database review fixture.'}}});
  return {db,service,calls};
}
const getOp=(f,id)=>f.db.prepare('SELECT * FROM proofpay_operations WHERE id=?').bind(id).first();
async function propose(f,owner='owner-a',key='db-review-request',request='workflow review') {
  await f.service.propose(owner,{request,mode:'rehearsal',idempotencyKey:key});
  return (await f.service.state(owner)).operations.find(op=>op.request===request);
}
async function assertHealthy(db) {
  assert.equal((await db.prepare('PRAGMA integrity_check').first()).integrity_check,'ok');
  assert.deepEqual((await db.prepare('PRAGMA foreign_key_check').all()).results,[]);
}

test('database: failed proposal audit insert cannot strand an operation without provenance',async()=>{
  const f=await fixture();try {
    await f.service.start('owner-a','rehearsal');
    await f.db.exec("CREATE TEMP TRIGGER fail_proposal_event BEFORE INSERT ON proofpay_events WHEN NEW.type='PROPOSAL_CREATED' BEGIN SELECT RAISE(ABORT,'independent audit failure'); END;");
    await assert.rejects(propose(f));
    assert.equal((await f.db.prepare('SELECT COUNT(*) n FROM proofpay_operations').first()).n,0);
    assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE type='PROPOSAL_CREATED'").first()).n,0);
    await f.db.exec('DROP TRIGGER fail_proposal_event');
    const op=await propose(f);assert.equal(op.status,'PROPOSED');
    assert.equal((await f.db.prepare('SELECT COUNT(*) n FROM proofpay_operations').first()).n,1);
    assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE operation_id=? AND type='PROPOSAL_CREATED'").bind(op.id).first()).n,1);
    assert.equal((await f.service.state('owner-a')).workspace.reservedCents,0);await assertHealthy(f.db);
  }finally{f.db.close();}
});
test('database: failed approval audit insert cannot leave an unaudited reservation',async()=>{
  const f=await fixture();try {
    await f.service.start('owner-a','rehearsal');const op=await propose(f),before=await getOp(f,op.id);
    await f.db.exec("CREATE TEMP TRIGGER fail_approval_event BEFORE INSERT ON proofpay_events WHEN NEW.type='APPROVED' BEGIN SELECT RAISE(ABORT,'independent approval audit failure'); END;");
    await assert.rejects(f.service.approve('owner-a',op.id,1));
    assert.deepEqual(await getOp(f,op.id),before);
    assert.equal((await f.service.state('owner-a')).workspace.reservedCents,0);
    await f.db.exec('DROP TRIGGER fail_approval_event');await f.service.approve('owner-a',op.id,1);
    assert.equal((await f.service.state('owner-a')).workspace.reservedCents,18000);
    assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE operation_id=? AND type='APPROVED'").bind(op.id).first()).n,1);
    assert.deepEqual({create:f.calls.create,capture:f.calls.capture,get:f.calls.get},{create:0,capture:0,get:0});await assertHealthy(f.db);
  }finally{f.db.close();}
});
test('database: failed approval state write rolls back its decision event',async()=>{
  const f=await fixture();try {
    await f.service.start('owner-a','rehearsal');const op=await propose(f),before=await getOp(f,op.id);
    await f.db.exec("CREATE TEMP TRIGGER fail_approval_write BEFORE UPDATE ON proofpay_operations WHEN NEW.status='APPROVED' BEGIN SELECT RAISE(ABORT,'independent reservation failure'); END;");
    await assert.rejects(f.service.approve('owner-a',op.id,1));
    assert.deepEqual(await getOp(f,op.id),before);
    assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE type='APPROVED'").first()).n,0);
    assert.equal((await f.service.state('owner-a')).workspace.availableCents,30000);await assertHealthy(f.db);
  }finally{f.db.close();}
});
test('database: identical request keys across tenants retain distinct operations, allowances and evidence',async()=>{
  const f=await fixture();try {
    await f.service.start('owner-a','rehearsal');await f.service.start('owner-b','rehearsal');
    const a=await propose(f,'owner-a','shared-client-key','workflow review');
    const b=await propose(f,'owner-b','shared-client-key','design review');
    assert.notEqual(a.id,b.id);await f.service.approve('owner-a',a.id,1);await f.service.approve('owner-b',b.id,1);
    const sa=await f.service.state('owner-a'),sb=await f.service.state('owner-b');
    assert.notEqual(sa.workspace.id,sb.workspace.id);
    assert.equal(sa.workspace.reservedCents,18000);assert.equal(sb.workspace.reservedCents,16000);
    assert.deepEqual(sa.operations.map(x=>x.id),[a.id]);assert.deepEqual(sb.operations.map(x=>x.id),[b.id]);
    for(const event of sa.events)assert.ok(event.operationId===null||event.operationId===a.id);
    for(const event of sb.events)assert.ok(event.operationId===null||event.operationId===b.id);
    const before=await getOp(f,a.id);
    const foreignActions=[()=>f.service.approve('owner-b',a.id,1),()=>f.service.cancelBeforeDispatch('owner-b',a.id,1),()=>f.service.renewApproval('owner-b',a.id,1),()=>f.service.createOrder('owner-b',a.id,1,'https://proofpay.example'),()=>f.service.capture('owner-b',a.id,1),()=>f.service.reconcile('owner-b',a.id),()=>f.service.evidence('owner-b',a.id)];
    for(const action of foreignActions)await assert.rejects(action(),error=>error.code==='NOT_FOUND');
    assert.deepEqual(await getOp(f,a.id),before);
    assert.deepEqual({create:f.calls.create,capture:f.calls.capture,get:f.calls.get},{create:0,capture:0,get:0});await assertHealthy(f.db);
  }finally{f.db.close();}
});
test('database: workspace event cap never truncates the operation evidence export',async()=>{
  const f=await fixture();try {
    await f.service.start('owner-a','rehearsal');const op=await propose(f),stored=await getOp(f,op.id);
    const inserts=[];for(let i=0;i<105;i++)inserts.push(f.db.prepare('INSERT INTO proofpay_events(id,workspace_id,operation_id,type,detail,created_at) VALUES (?,?,?,?,?,?)').bind(`review-extra-${i}`,stored.workspace_id,op.id,'REVIEW_FIXTURE','Synthetic evidence pagination check.',Date.now()+i));
    await f.db.batch(inserts);
    const state=await f.service.state('owner-a'),evidence=await f.service.evidence('owner-a',op.id);
    assert.equal(state.events.length,100);assert.equal(evidence.events.length,106);
    assert.equal(evidence.events.filter(event=>event.type==='PROPOSAL_CREATED').length,1);await assertHealthy(f.db);
  }finally{f.db.close();}
});
test('database: a corrupted session pointer cannot make another owner workspace readable',async()=>{
  const f=await fixture();try {
    await f.service.start('owner-a','rehearsal');const op=await propose(f);
    await f.service.start('owner-b','rehearsal');const workspaceB=(await f.service.state('owner-b')).workspace;
    // Session rows are stored pointers, not authorization. The workspace owner
    // predicate must still prevent cross-tenant reads if that pointer is wrong.
    await f.db.prepare('UPDATE proofpay_sessions SET workspace_id=? WHERE owner_id=?').bind(workspaceB.id,'owner-a').run();
    assert.equal((await f.service.state('owner-a')).workspace,null);
    await assert.rejects(f.service.evidence('owner-b',op.id),error=>error.code==='NOT_FOUND');
    assert.equal((await f.service.evidence('owner-a',op.id)).operation.id,op.id);await assertHealthy(f.db);
  }finally{f.db.close();}
});
test('database: two OS processes cancelling the same reservation release once and keep one decision',{timeout:15000},async()=>{
  const f=await fixture();const children=[];
  try {
    await f.service.start('owner-a','rehearsal');const op=await propose(f);await f.service.approve('owner-a',op.id,1);
    const contender=()=>{
      const child=fork(resolve('tests/review-worker.mjs'),[f.db.filename,bundle,'owner-a',op.id,'cancel'],{stdio:['ignore','pipe','pipe','ipc']});children.push(child);
      let readyResolve,resultResolve,resultReject,stderr='';
      const ready=new Promise(resolve=>{readyResolve=resolve});
      const result=new Promise((resolve,reject)=>{resultResolve=resolve;resultReject=reject});
      child.stderr.on('data',chunk=>{stderr+=chunk});
      child.on('message',message=>{if(message.ready)readyResolve();else resultResolve(message)});
      child.on('error',resultReject);child.on('exit',code=>{if(code)resultReject(new Error(stderr))});
      return {child,ready,result};
    };
    const a=contender(),b=contender();await Promise.all([a.ready,b.ready]);a.child.send('go');b.child.send('go');
    assert.deepEqual((await Promise.all([a.result,b.result])).map(result=>result.ok),[true,true]);
    assert.equal((await getOp(f,op.id)).status,'CANCELLED');
    assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE operation_id=? AND type='REQUEST_CANCELLED'").bind(op.id).first()).n,1);
    const budget=(await f.service.state('owner-a')).workspace;assert.equal(budget.availableCents,30000);assert.equal(budget.reservedCents,0);assert.equal(budget.committedCents,0);
    await assertHealthy(f.db);
  }finally{for(const child of children)if(child.connected)child.kill();f.db.close();}
});
