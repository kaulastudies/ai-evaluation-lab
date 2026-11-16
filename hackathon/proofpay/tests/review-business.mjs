import assert from 'node:assert/strict';
import {test,after} from 'node:test';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {build} from 'esbuild';
import {ReviewD1} from './review-d1.mjs';
import {ownerConfig,ownerCookie} from './owner-fixture.mjs';

const directory=await mkdtemp(join(tmpdir(),'proofpay-business-'));
const env=ownerConfig({OWNER_ID:'business-owner'});globalThis.__proofpayBusinessEnv=env;
const bundle=join(directory,'business.mjs');
await build({stdin:{contents:'export {ProofPayService} from "./lib/proofpay/service.ts";export {handle} from "./lib/proofpay/http.ts";',resolveDir:process.cwd()},outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent',plugins:[{name:'business-env',setup(b){b.onResolve({filter:/^\.\/runtime$/},()=>({path:'env',namespace:'business-env'}));b.onLoad({filter:/.*/,namespace:'business-env'},()=>({contents:'const env=globalThis.__proofpayBusinessEnv;export function getRuntimeConfiguration(){return env;}export function getDatabase(){return env.DB;}export async function getRequestConfiguration(config){return config;}'}));}}]});
const {ProofPayService,handle}=await import(pathToFileURL(bundle));
const base=await readFile('drizzle/0000_greedy_living_lightning.sql','utf8');
const migration=await readFile('drizzle/0003_business_profiles.sql','utf8');
const owner='business-owner';
const settings={businessName:'Rama Studio',department:'Operations',defaultBudgetCents:40000,version:0};
const code=expected=>error=>error.code===expected;
after(async()=>{delete globalThis.__proofpayBusinessEnv;await rm(directory,{recursive:true,force:true});});
async function fixture(){const db=new ReviewD1(':memory:');await db.exec(base);await db.exec(migration);let externalCalls=0;const forbidden=async()=>{externalCalls++;throw Error('External service forbidden in business operations');};const service=new ProofPayService({db,env:{},provider:{create:forbidden,capture:forbidden,get:forbidden},ai:forbidden});return{db,service,calls:()=>externalCalls};}
function pauseBatch(db,pattern){const original=db.batch.bind(db);let reached,release;const paused=new Promise(resolve=>{reached=resolve;}),resume=new Promise(resolve=>{release=resolve;});let used=false;db.batch=async statements=>{if(!used&&statements.some(statement=>pattern.test(statement.sql))){used=true;reached();await resume;}return original(statements);};return{paused,release};}

test('business: unconfigured owner retains $300 default; migration preserves old workspace accounting and unknown identity',async()=>{
  const db=new ReviewD1(':memory:');await db.exec(base);await db.prepare("INSERT INTO proofpay_workspaces(id,owner_id,mode,currency,budget_cents,created_at) VALUES ('old',?,'rehearsal','USD',30000,1)").bind(owner).run();await db.prepare("INSERT INTO proofpay_sessions(owner_id,workspace_id) VALUES (?,'old')").bind(owner).run();await db.exec(migration);
  try{const service=new ProofPayService({db,env:{}});assert.deepEqual(await service.business(owner),{businessName:'',department:'',defaultBudgetCents:30000,currency:'USD',version:0,updatedAt:null,configured:false});const old=(await service.state(owner)).workspace;assert.equal(old.budgetCents,30000);assert.equal(old.businessName,null);assert.equal(old.businessProfileVersion,null);const next=await service.start(owner,'rehearsal');assert.equal(next.workspace.budgetCents,30000);assert.equal(next.workspace.department,null);}finally{db.close();}
});
test('business: owner settings persist, competing profile edits use exact version and foreign owners remain isolated',async()=>{
  const f=await fixture();try{
    const saved=await f.service.saveBusiness(owner,{...settings,businessName:'  Rama Studio  '});assert.equal(saved.businessName,'Rama Studio');assert.equal(saved.version,1);assert.equal(saved.currency,'USD');assert.equal(saved.configured,true);
    const fresh=new ProofPayService({db:f.db,env:{}});assert.deepEqual(await fresh.business(owner),saved);assert.equal((await fresh.business('another-owner')).configured,false);
    const results=await Promise.allSettled([fresh.saveBusiness(owner,{...settings,version:1,department:'Design'}),f.service.saveBusiness(owner,{...settings,version:1,department:'Engineering'})]);assert.equal(results.filter(result=>result.status==='fulfilled').length,1);assert.equal(results.find(result=>result.status==='rejected').reason.code,'BUSINESS_VERSION');assert.equal((await fresh.business(owner)).version,2);
    await assert.rejects(fresh.saveBusiness('another-owner',{...settings,version:1}),code('BUSINESS_VERSION'));assert.equal((await fresh.business('another-owner')).configured,false);assert.equal(f.calls(),0);
  }finally{f.db.close();}
});
test('business: validation rejects unsafe limits, controls, missing version and unauthenticated use',async()=>{
  const f=await fixture();try{
    for(const invalid of [{businessName:''},{businessName:' '.repeat(5)},{businessName:'x'.repeat(121)},{businessName:'Company\nInjected'},{department:'x'.repeat(81)},{department:'\u0000'},{defaultBudgetCents:99},{defaultBudgetCents:100000001},{defaultBudgetCents:1.5},{defaultBudgetCents:'30000'},{version:undefined},{version:-1},{version:2147483647}])await assert.rejects(f.service.saveBusiness(owner,{...settings,...invalid}),code('INVALID_BUSINESS'));
    for(const action of [()=>f.service.business(''),()=>f.service.saveBusiness('',settings),()=>f.service.workspaceHistory(''),()=>f.service.selectWorkspace('',crypto.randomUUID())])await assert.rejects(action(),code('AUTH_REQUIRED'));
    assert.equal((await f.service.business(owner)).configured,false);assert.equal(f.calls(),0);
  }finally{f.db.close();}
});
test('business: saved profile is snapshotted; edits cannot change old budget, approvals, IDs or evidence',async()=>{
  const f=await fixture();try{
    await f.service.saveBusiness(owner,settings);const original=await f.service.start(owner,'rehearsal',true);assert.equal(original.workspace.budgetCents,40000);assert.equal(original.workspace.businessName,settings.businessName);assert.equal(original.workspace.businessProfileVersion,1);
    for(const op of original.operations)await f.service.approve(owner,op.id,1);const approved=await f.service.state(owner),receipts=await Promise.all(original.operations.map(op=>f.service.evidence(owner,op.id)));assert.equal(approved.workspace.reservedCents,34000);
    await f.service.saveBusiness(owner,{businessName:'Changed Company',department:'Support',defaultBudgetCents:100,version:1});assert.deepEqual(await f.service.state(owner),approved);assert.deepEqual(await Promise.all(original.operations.map(op=>f.service.evidence(owner,op.id))),receipts);
    // The explicitly simulated rehearsal reset is retained. History still makes
    // the prior workspace and reservations discoverable, without releasing them.
    const next=await f.service.start(owner,'rehearsal',true);assert.equal(next.workspace.budgetCents,100);assert.equal(next.workspace.businessName,'Changed Company');assert.equal(next.workspace.businessProfileVersion,2);await assert.rejects(f.service.approve(owner,next.operations[0].id,1),code('BUDGET_EXCEEDED'));
    const history=await f.service.workspaceHistory(owner);assert.equal(history.workspaces.length,2);assert.equal(history.workspaces.find(workspace=>workspace.id===original.workspace.id).reservedCents,34000);const selected=await f.service.selectWorkspace(owner,original.workspace.id);assert.equal(selected.workspace.budgetCents,40000);assert.equal(selected.workspace.reservedCents,34000);assert.equal(f.calls(),0);
  }finally{f.db.close();}
});
test('business: history and selection expose only owned workspaces, preserve archived operations and record selection once',async()=>{
  const f=await fixture();try{
    const first=await f.service.start(owner,'rehearsal',true),second=await f.service.start(owner,'rehearsal'),foreign=await f.service.start('foreign-owner','rehearsal');const history=await f.service.workspaceHistory(owner);assert.equal(history.activeWorkspaceId,second.workspace.id);assert.equal(history.switchBlockedReason,null);assert.equal(history.workspaces.length,2);assert.ok(history.workspaces.every(row=>row.canSelect));assert.ok(!history.workspaces.some(row=>row.id===foreign.workspace.id));
    await assert.rejects(f.service.selectWorkspace(owner,foreign.workspace.id),code('NOT_FOUND'));await assert.rejects(f.service.selectWorkspace(owner,crypto.randomUUID()),code('NOT_FOUND'));await assert.rejects(f.service.selectWorkspace(owner,'../foreign'),code('INVALID_WORKSPACE'));
    const selected=await f.service.selectWorkspace(owner,first.workspace.id);assert.deepEqual(selected.operations,first.operations);await f.service.selectWorkspace(owner,first.workspace.id);assert.equal((await f.service.state(owner)).events.filter(event=>event.type==='WORKSPACE_SELECTED').length,1);assert.equal(f.calls(),0);
  }finally{f.db.close();}
});
for(const status of ['APPROVED','CREATE_DISPATCHED','CREATE_UNKNOWN','ORDER_READY','CAPTURE_DISPATCHED','UNKNOWN','REVIEW'])test(`business: ${status} blocks history switching in both modes without releasing reservations`,async()=>{
  for(const mode of ['rehearsal','sandbox']){const f=await fixture();try{
    const destination=await f.service.start(owner,'rehearsal');const active=await f.service.start(owner,'rehearsal',true);await f.db.prepare('UPDATE proofpay_workspaces SET mode=? WHERE id=?').bind(mode,active.workspace.id).run();await f.db.prepare('UPDATE proofpay_operations SET status=?,mode=? WHERE id=?').bind(status,mode,active.operations[0].id).run();const before=await f.service.state(owner);
    const history=await f.service.workspaceHistory(owner);assert.ok(history.switchBlockedReason);assert.equal(history.workspaces.find(row=>row.id===destination.workspace.id).canSelect,false);assert.equal(history.workspaces.find(row=>row.id===active.workspace.id).canSelect,true);await assert.rejects(f.service.selectWorkspace(owner,destination.workspace.id),code('WORKSPACE_SWITCH_BLOCKED'));assert.deepEqual(await f.service.selectWorkspace(owner,active.workspace.id),before);assert.deepEqual(await f.service.state(owner),before);assert.equal(f.calls(),0);
  }finally{f.db.close();}}
});
test('business: confirmed purchase can remain in history without blocking selection or changing committed accounting',async()=>{
  const f=await fixture();try{const target=await f.service.start(owner,'rehearsal'),source=await f.service.start(owner,'rehearsal',true);await f.db.prepare("UPDATE proofpay_operations SET status='CONFIRMED' WHERE id=?").bind(source.operations[0].id).run();assert.equal((await f.service.workspaceHistory(owner)).switchBlockedReason,null);await f.service.selectWorkspace(owner,target.workspace.id);assert.equal((await f.service.workspaceHistory(owner)).workspaces.find(row=>row.id===source.workspace.id).committedCents,source.operations[0].amountCents);}finally{f.db.close();}
});
test('business: approval winning before selection transaction blocks the switch and its audit',async()=>{
  const f=await fixture();try{const target=await f.service.start(owner,'rehearsal'),source=await f.service.start(owner,'rehearsal',true),barrier=pauseBatch(f.db,/'WORKSPACE_SELECTED'/);const switching=f.service.selectWorkspace(owner,target.workspace.id);await barrier.paused;await f.service.approve(owner,source.operations[0].id,1);barrier.release();await assert.rejects(switching,code('WORKSPACE_SWITCH_BLOCKED'));assert.equal((await f.service.state(owner)).workspace.id,source.workspace.id);assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE type='WORKSPACE_SELECTED'").first()).n,0);}finally{f.db.close();}
});
test('business: selection winning before approval transaction prevents approval in the departed workspace',async()=>{
  const f=await fixture();try{const target=await f.service.start(owner,'rehearsal'),source=await f.service.start(owner,'rehearsal',true),barrier=pauseBatch(f.db,/'APPROVED'/);const approving=f.service.approve(owner,source.operations[0].id,1);await barrier.paused;await f.service.selectWorkspace(owner,target.workspace.id);barrier.release();await assert.rejects(approving,code('WORKSPACE_CHANGED'));const old=(await f.service.workspaceHistory(owner)).workspaces.find(row=>row.id===source.workspace.id);assert.equal(old.reservedCents,0);assert.equal((await f.db.prepare('SELECT status FROM proofpay_operations WHERE id=?').bind(source.operations[0].id).first()).status,'PROPOSED');}finally{f.db.close();}
});
test('business: failed session switch rolls back its audit event and retains active workspace',async()=>{
  const f=await fixture();try{const target=await f.service.start(owner,'rehearsal'),source=await f.service.start(owner,'rehearsal');await f.db.exec("CREATE TEMP TRIGGER reject_switch BEFORE UPDATE ON proofpay_sessions BEGIN SELECT RAISE(ABORT,'synthetic switch failure'); END;");await assert.rejects(f.service.selectWorkspace(owner,target.workspace.id));assert.equal((await f.service.state(owner)).workspace.id,source.workspace.id);assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_events WHERE type='WORKSPACE_SELECTED'").first()).n,0);}finally{f.db.close();}
});
test('business: HTTP routes retain signed-owner authentication, exact origin, strict fields and no-store responses',async()=>{
  const f=await fixture();env.DB=f.db;try{
    const request=(method,body,headers={})=>new Request('https://proofpay.example/api/business',{method,headers:{cookie:ownerCookie(env),origin:'https://proofpay.example','content-type':'application/json',...headers},...(method==='GET'?{}:{body:JSON.stringify(body??{})})});
    for(const action of ['business','workspace-history']){const response=await handle(request('GET',null,{cookie:''}),action);assert.equal(response.status,401);assert.equal(response.headers.get('cache-control'),'no-store');}
    assert.equal((await handle(request('POST',settings,{origin:'https://attacker.invalid'}),'save-business')).status,403);assert.equal((await handle(request('POST',{...settings,currency:'EUR'}),'save-business')).status,400);assert.equal((await handle(request('POST',{...settings,ownerId:'foreign'}),'save-business')).status,400);assert.equal((await handle(request('GET'),'save-business')).status,405);assert.equal((await handle(request('POST',{}),'workspace-history')).status,405);
    const saved=await handle(request('POST',settings),'save-business');assert.equal(saved.status,200);assert.equal((await saved.json()).business.version,1);assert.equal(saved.headers.get('cache-control'),'no-store');const business=await handle(request('GET'),'business');assert.equal((await business.json()).business.businessName,settings.businessName);
    const first=await f.service.start(owner,'rehearsal');await f.service.start(owner,'rehearsal');const history=await handle(request('GET'),'workspace-history');assert.equal((await history.json()).workspaces.length,2);assert.equal((await handle(request('POST',{workspaceId:first.workspace.id,amountCents:1}),'select-workspace')).status,400);const selected=await handle(request('POST',{workspaceId:first.workspace.id}),'select-workspace');assert.equal(selected.status,200);assert.equal((await selected.json()).state.workspace.id,first.workspace.id);assert.equal(f.calls(),0);
  }finally{delete env.DB;f.db.close();}
});
