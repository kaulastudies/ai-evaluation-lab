import assert from 'node:assert/strict';
import {test,after} from 'node:test';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHmac} from 'node:crypto';
import {build} from 'esbuild';
import {ReviewD1} from './review-d1.mjs';
import {ownerConfig,ownerCookie} from './owner-fixture.mjs';

const directory=await mkdtemp(join(tmpdir(),'proofpay-judge-'));
const config={...ownerConfig(),JUDGE_DEMO_ONLY:'true',JUDGE_SESSION_SECRET:'j'.repeat(43)};
globalThis.__proofpayJudgeEnv=config;
const bundle=join(directory,'judge.mjs');
await build({stdin:{contents:'export * from "./lib/proofpay/judge-http.ts";export * from "./lib/proofpay/judge-auth.ts";export * from "./lib/proofpay/judge-limits.ts";export {handle} from "./lib/proofpay/http.ts";export {ownerLogin} from "./lib/proofpay/login.ts";export {ProofPayService} from "./lib/proofpay/service.ts";',resolveDir:process.cwd()},outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent',plugins:[{name:'judge-env',setup(b){b.onResolve({filter:/^\.\/runtime$/},()=>({path:'env',namespace:'judge-env'}));b.onLoad({filter:/.*/,namespace:'judge-env'},()=>({contents:'const env=globalThis.__proofpayJudgeEnv;export function getRuntimeConfiguration(){return env;}export function getJudgeRuntimeConfiguration(){return {JUDGE_DEMO_ONLY:env.JUDGE_DEMO_ONLY,JUDGE_SESSION_SECRET:env.JUDGE_SESSION_SECRET,APP_ORIGIN:env.APP_ORIGIN,NODE_ENV:env.NODE_ENV};}export function getDatabase(){return env.DB;}export async function getRequestConfiguration(){throw Error("Judge must not request production config or OIDC");}'}));}}]});
const {handleJudge,authenticateJudgeRequest,issueJudgeSession,claimJudgeSession,claimJudgeMutation,handle,ownerLogin,ProofPayService}=await import(pathToFileURL(bundle));
const schema=(await Promise.all(['0000_greedy_living_lightning.sql','0001_owner_auth_limits.sql','0002_ai_funding.sql','0003_business_profiles.sql'].map(name=>readFile(`drizzle/${name}`,'utf8')))).join('\n');
after(async()=>{delete globalThis.__proofpayJudgeEnv;await rm(directory,{recursive:true,force:true});});
async function fixture(){const db=new ReviewD1(':memory:');await db.exec(schema);config.DB=db;return db;}
function request(path,method='GET',body,cookie='',headers={}){return new Request(`https://proofpay.example/api/judge/${path}`,{method,headers:{origin:'https://proofpay.example','content-type':'application/json',cookie,...headers},...(method==='GET'||method==='HEAD'?{}:{body:JSON.stringify(body??{})})});}
async function call(path,method='GET',body,cookie='',headers={}){const response=await handleJudge(request(path,method,body,cookie,headers),path.split('/'));return{response,result:await response.json()};}
async function session(){const response=await call('session','POST',{});assert.equal(response.response.status,200);return{cookie:response.response.headers.get('set-cookie').split(';')[0],...response};}
function signed(payload){const encoded=Buffer.from(JSON.stringify(payload)).toString('base64url');return `__Host-proofpay-judge=${encoded}.${createHmac('sha256',config.JUDGE_SESSION_SECRET).update(`proofpay-judge-v1.${encoded}`).digest('base64url')}`;}
const code=expected=>error=>error.code===expected;

test('judge: each visitor receives a distinct signed isolated rehearsal, strict secure cookie and no owner authority',async()=>{
  const db=await fixture();try{
    const a=await session(),b=await session();assert.notEqual(a.cookie,b.cookie);assert.notEqual(a.result.state.workspace.id,b.result.state.workspace.id);assert.ok(a.response.headers.get('set-cookie').includes('HttpOnly; Secure; SameSite=Strict; Max-Age=7200'));assert.equal(a.result.state.workspace.mode,'rehearsal');assert.equal(a.result.state.workspace.budgetCents,30000);assert.equal(a.result.state.operations.length,2);assert.deepEqual(a.result.state.capabilities,{sandboxReady:false,aiReady:false});assert.equal(a.result.judge.simulated,true);assert.equal(a.result.judge.resetLimit,10);assert.equal(a.result.judge.mutationLimit,100);assert.ok(a.result.judge.expiresAt>Date.now());
    const identity=authenticateJudgeRequest(request('state','GET',undefined,a.cookie),config);assert.match(identity.owner,/^judge:/);assert.notEqual(identity.owner,config.OWNER_ID);
    const reused=await call('session','POST',{},a.cookie);assert.equal(reused.result.state.workspace.id,a.result.state.workspace.id);assert.equal(reused.response.headers.get('set-cookie'),null);assert.equal(reused.result.judge.expiresAt,a.result.judge.expiresAt);assert.equal((await db.prepare('SELECT COUNT(*) n FROM proofpay_workspaces').first()).n,2);
  }finally{db.close();delete config.DB;}
});
test('judge: forged, duplicate, expired, wrong-audience and owner-shaped cookies cannot authenticate',async()=>{
  const db=await fixture();try{const a=await session(),identity=authenticateJudgeRequest(request('state','GET',undefined,a.cookie),config),now=Math.floor(Date.now()/1000),payload={v:1,kind:'judge-rehearsal',sub:identity.owner,aud:config.APP_ORIGIN,iat:now,exp:now+7200};
    const invalid=['',ownerCookie(config),a.cookie+'x',`${a.cookie}; ${a.cookie}`,signed({...payload,sub:config.OWNER_ID}),signed({...payload,aud:'https://other.example'}),signed({...payload,kind:'owner'}),signed({...payload,iat:now-7201,exp:now-1}),signed({...payload,iat:now+100,exp:now+7300}),signed({...payload,exp:now+99999})];
    for(const cookie of invalid){assert.throws(()=>authenticateJudgeRequest(request('state','GET',undefined,cookie),config),code('JUDGE_AUTH_REQUIRED'));const result=await call('state','GET',undefined,cookie);assert.equal(result.response.status,401);assert.equal(result.result.state,undefined);assert.ok(result.response.headers.get('set-cookie').includes('Max-Age=0'));}
    const token=issueJudgeSession(config,100000);assert.throws(()=>authenticateJudgeRequest(request('state','GET',undefined,`__Host-proofpay-judge=${token.token}`),config,7300000),code('JUDGE_AUTH_REQUIRED'));
    const anotherSecret={...config,JUDGE_SESSION_SECRET:'k'.repeat(43)};assert.throws(()=>authenticateJudgeRequest(request('state','GET',undefined,a.cookie),anotherSecret),code('JUDGE_AUTH_REQUIRED'));
  }finally{db.close();delete config.DB;}
});
test('judge: guest records and evidence remain private across guests and configured owner records',async()=>{
  const db=await fixture();try{const ownerService=new ProofPayService({db,env:{}}),ownerState=await ownerService.start(config.OWNER_ID,'rehearsal',true),a=await session(),b=await session();const before=await ownerService.state(config.OWNER_ID);
    for(const operation of [b.result.state.operations[0],ownerState.operations[0]])for(const action of ['evidence','approve','cancel','renew-approval','create-order','capture','reconcile']){const result=await call(`operations/${operation.id}/${action}`,action==='evidence'?'GET':'POST',action==='reconcile'?{}:{approvalVersion:1},a.cookie);assert.equal(result.response.status,404);assert.equal(result.result.code,'NOT_FOUND');assert.ok(!JSON.stringify(result.result).includes(operation.id));}
    const own=await call(`operations/${a.result.state.operations[0].id}/evidence`,'GET',undefined,a.cookie);assert.equal(own.response.status,200);assert.equal(own.result.operation.providerMode,'rehearsal');assert.deepEqual(await ownerService.state(config.OWNER_ID),before);
    for(const path of ['business','workspaces/history','workspaces/select'])assert.equal((await call(path,'POST',{},a.cookie)).response.status,404);
  }finally{db.close();delete config.DB;}
});
test('judge: deployment guards disable every owner action and owner login even with a valid owner cookie',async()=>{
  const db=await fixture();try{for(const action of ['state','business','save-business','workspace-history','select-workspace','start-rehearsal','start-diagnostic','start','propose','approve','cancel','renew-approval','create-order','capture','reconcile','evidence']){const result=await handle(request('state','POST',{},ownerCookie(config)),action,crypto.randomUUID());assert.equal(result.status,404);assert.equal((await result.json()).state,undefined);}
    for(const logout of [false,true])assert.equal((await ownerLogin(request('session','POST',{},ownerCookie(config)),logout)).status,404);
    config.JUDGE_DEMO_ONLY=undefined;try{assert.equal((await call('session','POST',{})).response.status,404);assert.equal((await call('state')).response.status,404);}finally{config.JUDGE_DEMO_ONLY='true';}
    assert.equal((await db.prepare('SELECT COUNT(*) n FROM proofpay_workspaces').first()).n,0);
  }finally{db.close();delete config.DB;}
});
test('judge: exact origin, JSON, methods and strict action fields reject sandbox or model authority before writes',async()=>{
  const db=await fixture();try{for(const headers of [{origin:'https://attacker.invalid'},{origin:''},{'content-type':'text/plain'},{'sec-fetch-site':'cross-site'}])assert.ok([403,415].includes((await call('session','POST',{},'',headers)).response.status));assert.equal((await call('session','GET')).response.status,405);
    for(const body of [{ownerId:'attacker'},{mode:'sandbox'},{JUDGE_DEMO_ONLY:true}])assert.equal((await call('session','POST',body)).response.status,400);
    const a=await session();for(const path of ['sandbox/diagnostic/start','workspaces','workspaces/start','auth/login'])assert.equal((await call(path,'POST',{mode:'sandbox'},a.cookie)).response.status,404);
    for(const body of [{request:'workflow',mode:'sandbox',idempotencyKey:'forbidden-sandbox'},{request:'workflow',mode:'rehearsal',idempotencyKey:'forbidden-source',source:'model'},{request:'workflow',mode:'rehearsal',idempotencyKey:'forbidden-price',amountCents:1}])assert.ok([400,403].includes((await call('proposals','POST',body,a.cookie)).response.status));
    assert.equal((await db.prepare('SELECT COUNT(*) n FROM proofpay_operations').first()).n,2);assert.equal((await db.prepare('SELECT COUNT(*) n FROM proofpay_ai_attempts').first()).n,0);
    for(const result of [await call('state','GET',undefined,a.cookie),await call('session','POST',{bad:true},a.cookie)]){assert.equal(result.response.headers.get('cache-control'),'no-store');assert.equal(result.response.headers.get('x-content-type-options'),'nosniff');}
  }finally{db.close();delete config.DB;}
});
test('judge: missing secret or HTTPS origin fails closed without creating records',async()=>{
  const db=await fixture();try{const secret=config.JUDGE_SESSION_SECRET,origin=config.APP_ORIGIN;for(const mutation of [{JUDGE_SESSION_SECRET:undefined},{JUDGE_SESSION_SECRET:'short'},{APP_ORIGIN:'http://localhost:3000'},{APP_ORIGIN:'https://proofpay.example/path'}]){Object.assign(config,mutation);assert.equal((await call('session','POST',{})).response.status,503);config.JUDGE_SESSION_SECRET=secret;config.APP_ORIGIN=origin;}assert.equal((await db.prepare('SELECT COUNT(*) n FROM proofpay_workspaces').first()).n,0);}finally{db.close();delete config.DB;}
});
test('judge: repeatable budget, lost acknowledgement and reconciliation use one simulated capture and zero network calls',async()=>{
  const db=await fixture(),originalFetch=globalThis.fetch;let networkCalls=0;globalThis.fetch=async()=>{networkCalls++;throw Error('Network forbidden');};Object.assign(config,{PAYPAL_CLIENT_ID:'synthetic-present',PAYPAL_CLIENT_SECRET:'synthetic-present',PAYPAL_MERCHANT_ID:'synthetic-present',AI_API_KEY:'synthetic-present',AI_FUNDING_MODE:'vercel-free-credit',VERCEL_OIDC_TOKEN:'synthetic-present'});
  try{const a=await session(),op=a.result.state.operations.find(item=>item.amountCents===18000),second=a.result.state.operations.find(item=>item.id!==op.id);const mutate=(action,body={approvalVersion:1})=>call(`operations/${op.id}/${action}`,'POST',body,a.cookie);
    assert.equal((await mutate('approve')).response.status,200);const blocked=await call(`operations/${second.id}/approve`,'POST',{approvalVersion:1},a.cookie);assert.equal(blocked.result.code,'BUDGET_EXCEEDED');assert.equal((await mutate('create-order')).response.status,200);
    const lost=await mutate('capture',{approvalVersion:1,fault:'drop-response'});assert.equal(lost.response.status,202);assert.equal(lost.result.state.operations.find(item=>item.id===op.id).status,'UNKNOWN');assert.equal(lost.result.state.workspace.reservedCents,18000);
    assert.equal((await mutate('reconcile',{})).response.status,200);await mutate('reconcile',{});const evidence=await call(`operations/${op.id}/evidence`,'GET',undefined,a.cookie);assert.equal(evidence.result.operation.status,'CONFIRMED');assert.equal(evidence.result.verificationRecords.length,1);assert.equal(evidence.result.verificationRecords[0].simulated,true);assert.equal((await db.prepare('SELECT capture_calls FROM proofpay_rehearsal_orders WHERE operation_id=?').bind(op.id).first()).capture_calls,1);
    const proposal=await call('proposals','POST',{request:'Find a cheaper starter review',mode:'rehearsal',idempotencyKey:'judge-manual-proposal'},a.cookie);assert.equal(proposal.response.status,200);assert.equal(proposal.result.state.operations.find(item=>item.request==='Find a cheaper starter review').aiSource,'rehearsal-rule');assert.equal(networkCalls,0);assert.equal((await db.prepare('SELECT COUNT(*) n FROM proofpay_ai_attempts').first()).n,0);
  }finally{globalThis.fetch=originalFetch;for(const key of ['PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','PAYPAL_MERCHANT_ID','AI_API_KEY','AI_FUNDING_MODE','VERCEL_OIDC_TOKEN'])delete config[key];db.close();delete config.DB;}
});
test('judge: resets append new own workspaces, retain old evidence and cannot reset any AI grant',async()=>{
  const db=await fixture();try{const ownerService=new ProofPayService({db,env:{}}),reserved=(await ownerService.start(config.OWNER_ID,'rehearsal')).workspace;await db.prepare("INSERT INTO proofpay_ai_attempts(id,workspace_id,grant_id,slot,idempotency_key,model,provider,created_at,grant_expires_at) VALUES (?,?,?,1,'existing-key','synthetic','synthetic',1,2)").bind(crypto.randomUUID(),reserved.id,'already-consumed-grant').run();const funding=(await db.prepare('SELECT * FROM proofpay_ai_attempts').all()).results;
    const a=await session(),op=a.result.state.operations[0];await call(`operations/${op.id}/approve`,'POST',{approvalVersion:1},a.cookie);const receipt=await call(`operations/${op.id}/evidence`,'GET',undefined,a.cookie);
    const reset=await call('rehearsal/start','POST',{},a.cookie);assert.equal(reset.response.status,200);assert.notEqual(reset.result.state.workspace.id,a.result.state.workspace.id);assert.equal(reset.result.state.workspace.budgetCents,30000);assert.equal(reset.result.state.workspace.reservedCents,0);assert.equal(reset.result.state.operations.length,2);assert.deepEqual((await call(`operations/${op.id}/evidence`,'GET',undefined,a.cookie)).result,receipt.result);assert.deepEqual((await db.prepare('SELECT * FROM proofpay_ai_attempts').all()).results,funding);
  }finally{db.close();delete config.DB;}
});
test('judge: durable session, action and reset ceilings block excess writes without renewing a token',async()=>{
  const db=await fixture();try{const a=await session(),identity=authenticateJudgeRequest(request('state','GET',undefined,a.cookie),config);await db.prepare('INSERT INTO proofpay_auth_limits(id,window_start,attempts) VALUES (?,0,10)').bind(`judge-resets:${identity.owner}`).run();assert.equal((await call('rehearsal/start','POST',{},a.cookie)).result.code,'JUDGE_RESET_LIMIT');assert.equal((await db.prepare('SELECT COUNT(*) n FROM proofpay_workspaces').first()).n,1);
    await db.prepare('UPDATE proofpay_auth_limits SET attempts=100 WHERE id=?').bind(`judge-mutations:${identity.owner}`).run();assert.equal((await call('proposals','POST',{request:'workflow',mode:'rehearsal',idempotencyKey:'beyond-limit'},a.cookie)).result.code,'JUDGE_MUTATION_LIMIT');assert.equal((await call('state','GET',undefined,a.cookie)).response.status,200);
    await db.prepare("UPDATE proofpay_auth_limits SET attempts=60 WHERE id='judge-new-hour'").run();assert.equal((await call('session','POST',{})).result.code,'JUDGE_SESSION_LIMIT');await db.prepare("UPDATE proofpay_auth_limits SET attempts=0 WHERE id='judge-new-hour'").run();await db.prepare("UPDATE proofpay_auth_limits SET attempts=300 WHERE id='judge-new-total'").run();assert.equal((await call('session','POST',{})).result.code,'JUDGE_SESSION_LIMIT');assert.equal((await db.prepare('SELECT COUNT(*) n FROM proofpay_workspaces').first()).n,1);
    const repeated=await call('session','POST',{},a.cookie);assert.equal(repeated.response.status,200);assert.equal(repeated.result.judge.expiresAt,a.result.judge.expiresAt);
  }finally{db.close();delete config.DB;}
});
test('judge: concurrent quota claims never exceed the final durable session or action slot',async()=>{
  const db=await fixture();try{await db.prepare("INSERT INTO proofpay_auth_limits(id,window_start,attempts) VALUES ('judge-new-total',0,299)").run();const sessions=await Promise.allSettled([claimJudgeSession(db),claimJudgeSession(db)]);assert.equal(sessions.filter(value=>value.status==='fulfilled').length,1);assert.equal(sessions.find(value=>value.status==='rejected').reason.code,'JUDGE_SESSION_LIMIT');assert.equal((await db.prepare("SELECT attempts FROM proofpay_auth_limits WHERE id='judge-new-total'").first()).attempts,300);
    await db.prepare("INSERT INTO proofpay_auth_limits(id,window_start,attempts) VALUES ('judge-mutations:synthetic',0,99)").run();const actions=await Promise.allSettled([claimJudgeMutation(db,'synthetic'),claimJudgeMutation(db,'synthetic')]);assert.equal(actions.filter(value=>value.status==='fulfilled').length,1);assert.equal(actions.find(value=>value.status==='rejected').reason.code,'JUDGE_MUTATION_LIMIT');
  }finally{db.close();delete config.DB;}
});
test('judge: a corrupted non-rehearsal guest record cannot dispatch or return a misleading rehearsal receipt',async()=>{
  const db=await fixture();try{const a=await session(),op=a.result.state.operations[0];await db.prepare("UPDATE proofpay_operations SET mode='sandbox' WHERE id=?").bind(op.id).run();for(const action of ['evidence','approve','create-order','capture','reconcile']){const response=await call(`operations/${op.id}/${action}`,action==='evidence'?'GET':'POST',action==='reconcile'?{}:{approvalVersion:1},a.cookie);assert.equal(response.response.status,403);assert.equal(response.result.code,'JUDGE_REHEARSAL_ONLY');assert.equal(response.result.state,undefined);}assert.equal((await db.prepare('SELECT COUNT(*) n FROM proofpay_rehearsal_orders').first()).n,0);}finally{db.close();delete config.DB;}
});
