// Explicit integration gate: requires the dedicated ProofPay Neon connection.
// Creates/drops only a fresh random schema; never calls PayPal or a model.
import assert from 'node:assert/strict';
import {test,before,after} from 'node:test';
import {randomUUID} from 'node:crypto';
import {mkdtemp,readdir,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {Pool} from 'pg';
import {build} from 'esbuild';

const source=process.env.PROOFPAY_TEST_DATABASE_URL??process.env.DATABASE_URL_UNPOOLED??process.env.DATABASE_URL;
if(!source)throw Error('Dedicated PostgreSQL connection missing; live PostgreSQL checks did not run.');
let url;try{url=new URL(source);}catch{throw Error('Invalid dedicated PostgreSQL configuration.');}
if(!['postgres:','postgresql:'].includes(url.protocol)||!url.username||!url.password)throw Error('Invalid dedicated PostgreSQL configuration.');
for(const key of ['sslmode','sslcert','sslkey','sslrootcert','sslnegotiation'])url.searchParams.delete(key);
const schema=`proofpay_test_${randomUUID().replaceAll('-','')}`;
const explicitlyLocal=process.env.PROOFPAY_TEST_ALLOW_LOCAL_DB==='1'&&['localhost','127.0.0.1','[::1]'].includes(url.hostname);
const settings={connectionString:url.toString(),ssl:explicitlyLocal?false:{rejectUnauthorized:true},connectionTimeoutMillis:15000,max:4,application_name:'proofpay-isolated-test'};
function safeDatabaseError(error){
  const safe=Error('POSTGRES_INTEGRATION_DATABASE_FAILED');
  // Keep only fixed SQLSTATEs needed by the adapter's retry/constraint checks.
  if(['40001','40P01','23505','23503','42501','42P01','28P01'].includes(error?.code))safe.code=error.code;
  return safe;
}
function safePool(options){
  let value;try{value=new Pool(options);}catch(error){throw safeDatabaseError(error);}
  value.on('error',()=>{});
  return{
    async query(...args){try{return await value.query(...args);}catch(error){throw safeDatabaseError(error);}},
    async connect(){let client;try{client=await value.connect();}catch(error){throw safeDatabaseError(error);}return{
      async query(...args){try{return await client.query(...args);}catch(error){throw safeDatabaseError(error);}},
      release(){try{client.release();}catch(error){throw safeDatabaseError(error);}},
    };},
    async end(){try{await value.end();}catch(error){throw safeDatabaseError(error);}},
  };
}
const admin=safePool(settings);const pools=[];
let directory,PostgresDatabase,ProofPayService,RehearsalProvider,claimLoginAttempt;
function pool(){const value=safePool({...settings,options:`-c search_path=${schema}`});pools.push(value);return value;}
before(async()=>{
  directory=await mkdtemp(join(tmpdir(),'proofpay-pg-live-'));const output=join(directory,'modules.mjs');
  await build({stdin:{contents:'export {PostgresDatabase} from "./lib/proofpay/postgres-database.ts";export {ProofPayService} from "./lib/proofpay/service.ts";export {RehearsalProvider} from "./lib/proofpay/provider.ts";export {claimLoginAttempt} from "./lib/proofpay/auth-rate-limit.ts";',resolveDir:process.cwd()},outfile:output,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
  ({PostgresDatabase,ProofPayService,RehearsalProvider,claimLoginAttempt}=await import(pathToFileURL(output)));
  const client=await admin.connect();
  try{await client.query('BEGIN');await client.query(`CREATE SCHEMA "${schema}"`);await client.query(`SET LOCAL search_path TO "${schema}"`);for(const name of(await readdir('db/postgres')).filter(n=>/^\d{4}_[a-z0-9_]+\.sql$/.test(n)).sort())await client.query(await readFile(join('db/postgres',name),'utf8'));await client.query('COMMIT');}
  catch(error){await client.query('ROLLBACK');throw error;}finally{client.release();}
});
after(async()=>{
  await Promise.all(pools.map(value=>value.end()));
  try{if(/^proofpay_test_[a-f0-9]{32}$/.test(schema))await admin.query(`DROP SCHEMA IF EXISTS "${schema}" CASCADE`);}finally{await admin.end();if(directory)await rm(directory,{recursive:true,force:true});}
});

test('live PG: genuinely overlapping serializable reservations cannot overspend the shared allowance',async()=>{
  const base=new PostgresDatabase(pool());const owner=`budget-${randomUUID()}`;const initial=new ProofPayService({db:base,env:{}});const state=await initial.start(owner,'rehearsal',true);
  let arrivals=0,release;const barrier=new Promise(resolve=>{release=resolve;});
  function contender(){const target=pool();let paused=false;return new PostgresDatabase({query:target.query.bind(target),async connect(){const client=await target.connect();return{release:client.release.bind(client),async query(query,...args){const answer=await client.query(query,...args);const text=typeof query==='string'?query:query.text;if(!paused&&text.includes("'APPROVED'")&&text.startsWith('INSERT INTO proofpay_events')){paused=true;arrivals++;if(arrivals===2)release();let timer;try{await Promise.race([barrier,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Concurrency barrier not reached')),10000);})]);}finally{clearTimeout(timer);}}return answer;}};}});}
  const outcomes=await Promise.allSettled(state.operations.map(operation=>new ProofPayService({db:contender(),env:{}}).approve(owner,operation.id,1)));
  assert.equal(arrivals,2);assert.equal(outcomes.filter(value=>value.status==='fulfilled').length,1);assert.equal(outcomes.filter(value=>value.status==='rejected'&&value.reason.code==='BUDGET_EXCEEDED').length,1);
  const final=await initial.state(owner);assert.ok(final.workspace.reservedCents<=30000);assert.equal(final.operations.filter(op=>op.status==='APPROVED').length,1);
  assert.equal(final.events.filter(event=>event.type==='APPROVED').length,1);
});
test('live PG: audit failure rolls back reservation and permits a clean later approval',async()=>{
  const db=new PostgresDatabase(pool()),owner=`rollback-${randomUUID()}`,service=new ProofPayService({db,env:{}});const state=await service.start(owner,'rehearsal',true),op=state.operations[0];
  const client=await db.pool.connect();
  try{await client.query(`CREATE FUNCTION reject_approval() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.type='APPROVED' THEN RAISE EXCEPTION 'synthetic audit abort'; END IF; RETURN NEW; END $$`);await client.query('CREATE TRIGGER reject_approval BEFORE INSERT ON proofpay_events FOR EACH ROW EXECUTE FUNCTION reject_approval()');await assert.rejects(service.approve(owner,op.id,1));const failed=await service.state(owner);assert.equal(failed.workspace.reservedCents,0);assert.equal(failed.operations.find(item=>item.id===op.id).status,'PROPOSED');}
  finally{await client.query('DROP TRIGGER IF EXISTS reject_approval ON proofpay_events');await client.query('DROP FUNCTION IF EXISTS reject_approval()');client.release();}
  await service.approve(owner,op.id,1);assert.ok((await service.state(owner)).workspace.reservedCents>0);
});
test('live PG: owner business profile edits preserve workspace budget and approval snapshots; history is owner-scoped',async()=>{
  const db=new PostgresDatabase(pool()),owner=`business-${randomUUID()}`,service=new ProofPayService({db,env:{}});
  assert.equal((await service.business(owner)).defaultBudgetCents,30000);
  await service.saveBusiness(owner,{businessName:'Synthetic Business',department:'Operations',defaultBudgetCents:40000,version:0});const original=await service.start(owner,'rehearsal',true);
  for(const operation of original.operations)await service.approve(owner,operation.id,1);
  const before=await service.state(owner),receipt=await service.evidence(owner,original.operations[0].id);
  const other=new ProofPayService({db:new PostgresDatabase(pool()),env:{}});
  const outcomes=await Promise.allSettled([service.saveBusiness(owner,{businessName:'Next Business',department:'Design',defaultBudgetCents:100,version:1}),other.saveBusiness(owner,{businessName:'Next Business',department:'Design',defaultBudgetCents:100,version:1})]);
  assert.equal(outcomes.filter(value=>value.status==='fulfilled').length,1);assert.equal(outcomes.find(value=>value.status==='rejected').reason.code,'BUSINESS_VERSION');
  assert.deepEqual(await service.state(owner),before);assert.deepEqual(await service.evidence(owner,original.operations[0].id),receipt);
  const next=await other.start(owner,'rehearsal');assert.equal(next.workspace.budgetCents,100);assert.equal(next.workspace.businessName,'Next Business');assert.equal(next.workspace.businessProfileVersion,2);
  const foreign=`foreign-${randomUUID()}`,foreignWorkspace=(await other.start(foreign,'rehearsal')).workspace;assert.equal((await service.business(foreign)).configured,false);
  const history=await service.workspaceHistory(owner);assert.equal(history.workspaces.length,2);assert.equal(history.workspaces.find(row=>row.id===original.workspace.id).reservedCents,34000);assert.ok(!history.workspaces.some(row=>row.id===foreignWorkspace.id));
  await assert.rejects(service.selectWorkspace(owner,foreignWorkspace.id),error=>error.code==='NOT_FOUND');await service.selectWorkspace(owner,original.workspace.id);
  await assert.rejects(other.selectWorkspace(owner,next.workspace.id),error=>error.code==='WORKSPACE_SWITCH_BLOCKED');assert.equal((await service.state(owner)).workspace.id,original.workspace.id);
});
test('live PG: overlapping history selection and approval cannot hide a newly reserved workspace',async()=>{
  const db=new PostgresDatabase(pool()),owner=`switch-${randomUUID()}`,service=new ProofPayService({db,env:{}}),target=(await service.start(owner,'rehearsal')).workspace;
  const source=await service.start(owner,'rehearsal',true);let arrivals=0,release;const barrier=new Promise(resolve=>{release=resolve;});
  function contender(marker){const targetPool=pool();let paused=false;return new PostgresDatabase({query:targetPool.query.bind(targetPool),async connect(){const client=await targetPool.connect();return{release:client.release.bind(client),async query(query,...args){const answer=await client.query(query,...args),text=typeof query==='string'?query:query.text;if(!paused&&text.startsWith('INSERT INTO proofpay_events')&&text.includes(marker)){paused=true;arrivals++;if(arrivals===2)release();let timer;try{await Promise.race([barrier,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Workspace race barrier not reached')),10000);})]);}finally{clearTimeout(timer);}}return answer;}};}});}
  const switching=new ProofPayService({db:contender("'WORKSPACE_SELECTED'"),env:{}}).selectWorkspace(owner,target.id);
  const approving=new ProofPayService({db:contender("'APPROVED'"),env:{}}).approve(owner,source.operations[0].id,1);
  const [switchResult,approvalResult]=await Promise.allSettled([switching,approving]);assert.equal(arrivals,2);
  const active=await service.state(owner),history=await service.workspaceHistory(owner),old=history.workspaces.find(row=>row.id===source.workspace.id);
  if(approvalResult.status==='fulfilled'){assert.equal(switchResult.status,'rejected');assert.equal(switchResult.reason.code,'WORKSPACE_SWITCH_BLOCKED');assert.equal(active.workspace.id,source.workspace.id);assert.equal(old.reservedCents,source.operations[0].amountCents);}
  else{assert.equal(approvalResult.reason.code,'WORKSPACE_CHANGED');assert.equal(switchResult.status,'fulfilled');assert.equal(active.workspace.id,target.id);assert.equal(old.reservedCents,0);}
  const audit=await db.prepare("SELECT type,COUNT(*) AS n FROM proofpay_events WHERE workspace_id IN (?,?) AND type IN ('APPROVED','WORKSPACE_SELECTED') GROUP BY type").bind(source.workspace.id,target.id).all();assert.equal(audit.results.length,1);assert.equal(audit.results[0].n,1);
});
test('live PG: competing capture claims invoke the synthetic provider once and persist one receipt',async()=>{
  const db=new PostgresDatabase(pool()),owner=`capture-${randomUUID()}`;let captures=0;
  let entered,release;
  const arrived=new Promise(resolve=>{entered=resolve;}),proceed=new Promise(resolve=>{release=resolve;});
  const provider=new RehearsalProvider(db,Date.now);const wrapped={create:provider.create.bind(provider),get:provider.get.bind(provider),async capture(op){captures++;entered();await proceed;return provider.capture(op);}};
  const service=new ProofPayService({db,env:{},provider:wrapped});const op=(await service.start(owner,'rehearsal',true)).operations[0];await service.approve(owner,op.id,1);await service.createOrder(owner,op.id,1,'https://proofpay.example');
  const first=service.capture(owner,op.id,1).then(value=>({value}),error=>({error}));
  let timer,outcome;
  try{
    await Promise.race([arrived,first.then(result=>{throw result.error??Error('Capture completed before the provider barrier');}),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Capture barrier not reached')),10000);})]);
    // The first durable dispatch has won and is still inside the provider call.
    // A later request must receive the specific state conflict, not dispatch.
    const contender=new ProofPayService({db:new PostgresDatabase(pool()),env:{},provider:wrapped});
    await assert.rejects(contender.capture(owner,op.id,1),error=>error.code==='CAPTURE_STATE'&&error.status===409);
    assert.equal(captures,1);
    assert.equal((await service.state(owner)).operations.find(item=>item.id===op.id).status,'CAPTURE_DISPATCHED');
  }finally{clearTimeout(timer);release();outcome=await first;}
  if(outcome.error)throw outcome.error;
  assert.equal(captures,1);const receipt=await service.evidence(owner,op.id);assert.equal(receipt.operation.status,'CONFIRMED');assert.equal(receipt.verificationRecords.length,1);
  assert.equal((await db.prepare('SELECT capture_calls FROM proofpay_rehearsal_orders WHERE operation_id=?').bind(op.id).first()).capture_calls,1);
});
test('live PG: lost response recovers through a fresh adapter without another capture; null CAS cancellation releases once',async()=>{
  const db=new PostgresDatabase(pool()),owner=`recovery-${randomUUID()}`,service=new ProofPayService({db,env:{}});const op=(await service.start(owner,'rehearsal',true)).operations[0];await service.approve(owner,op.id,1);await service.createOrder(owner,op.id,1,'https://proofpay.example');await service.capture(owner,op.id,1,'drop-response');assert.equal((await service.state(owner)).workspace.reservedCents,op.amountCents);
  const fresh=new ProofPayService({db:new PostgresDatabase(pool()),env:{}});await fresh.reconcile(owner,op.id);const evidence=await fresh.evidence(owner,op.id);assert.equal(evidence.operation.status,'CONFIRMED');assert.equal(evidence.verificationRecords.length,1);assert.equal((await db.prepare('SELECT capture_calls FROM proofpay_rehearsal_orders WHERE operation_id=?').bind(op.id).first()).capture_calls,1);
  const newOwner=`cancel-${randomUUID()}`,newOp=(await fresh.start(newOwner,'rehearsal',true)).operations[0];await fresh.approve(newOwner,newOp.id,1);await fresh.cancelBeforeDispatch(newOwner,newOp.id,1);await fresh.cancelBeforeDispatch(newOwner,newOp.id,1);assert.equal((await fresh.state(newOwner)).workspace.reservedCents,0);assert.equal((await fresh.evidence(newOwner,newOp.id)).events.filter(event=>event.type==='REQUEST_CANCELLED').length,1);
});
test('live PG: grant claims have one durable winner across workspaces and rollback preserves cap',async()=>{
  const db=new PostgresDatabase(pool());const values=[];for(let i=0;i<2;i++){const service=new ProofPayService({db,env:{}});values.push((await service.start(`grant-${randomUUID()}`,'rehearsal')).workspace.id);}
  const grant=`synthetic-${randomUUID()}`;
  const claim=async workspace=>{const other=new PostgresDatabase(pool());return other.batch([other.prepare("INSERT INTO proofpay_ai_attempts(id,workspace_id,grant_id,slot,idempotency_key,model,provider,created_at,grant_expires_at) SELECT ?,?,?,COALESCE(MAX(slot),0)+1,?,'synthetic','synthetic',1,9999999999999 FROM proofpay_ai_attempts WHERE grant_id=? HAVING COALESCE(MAX(slot),0)<1 ON CONFLICT DO NOTHING RETURNING id").bind(randomUUID(),workspace,grant,randomUUID(),grant)]);};
  const results=await Promise.all(values.map(claim));assert.equal(results.reduce((sum,value)=>sum+value[0].meta.changes,0),1);assert.equal((await db.prepare('SELECT COUNT(*) AS n FROM proofpay_ai_attempts WHERE grant_id=?').bind(grant).first()).n,1);
});
test('live PG: shared login limiter admits ten concurrent attempts and resets only in a later minute',async()=>{
  const db=new PostgresDatabase(pool()),now=1760000000000;
  const results=await Promise.all(Array.from({length:12},()=>claimLoginAttempt(db,now)));
  assert.equal(results.filter(Boolean).length,10);assert.equal(await claimLoginAttempt(db,now),false);assert.equal(await claimLoginAttempt(db,now+60000),true);
});
