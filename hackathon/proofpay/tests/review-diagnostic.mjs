import assert from 'node:assert/strict';
import { test, after } from 'node:test';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'esbuild';
import { ReviewD1 } from './review-d1.mjs';
import {ownerConfig,ownerCookie} from './owner-fixture.mjs';

const dir=await mkdtemp(join(tmpdir(),'proofpay-diagnostic-'));
const env=ownerConfig({OWNER_ID:'diagnostic-owner'});globalThis.__proofpayDiagnosticEnv=env;
const bundle=join(dir,'diagnostic.mjs');
await build({stdin:{contents:'export {ProofPayService} from "./lib/proofpay/service.ts"; export {handle} from "./lib/proofpay/http.ts";',resolveDir:process.cwd()},outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent',plugins:[{name:'diagnostic-env',setup(b){b.onResolve({filter:/^\.\/runtime$/},()=>({path:'env',namespace:'diagnostic'}));b.onLoad({filter:/.*/,namespace:'diagnostic'},()=>({contents:'const env=globalThis.__proofpayDiagnosticEnv;export function getRuntimeConfiguration(){return env;} export function getDatabase(){return env.DB;} export async function getRequestConfiguration(config){return config;}'}));}}]});
const {ProofPayService,handle}=await import(pathToFileURL(bundle));
const schema=await readFile('drizzle/0000_greedy_living_lightning.sql','utf8');
const config={PAYPAL_CLIENT_ID:'synthetic-client',PAYPAL_CLIENT_SECRET:'synthetic-secret',PAYPAL_MERCHANT_ID:'synthetic-seller'};
const owner='diagnostic-owner';
after(async()=>{delete globalThis.__proofpayDiagnosticEnv;await rm(dir,{recursive:true,force:true});});
async function fixture(options={}){const db=new ReviewD1(':memory:');await db.exec(schema);return {db,service:new ProofPayService({db,env:config,...options})};}
const code=expected=>error=>error.code===expected;

test('diagnostic: fixed sandbox proposal is durable, unapproved and explicitly has no model provenance or calls',async()=>{
  let aiCalls=0;const f=await fixture({ai:async()=>{aiCalls++;throw Error('AI must not run');}});const original=globalThis.fetch;
  globalThis.fetch=async()=>{throw Error('No provider request belongs in diagnostic creation');};
  try {
    const state=await f.service.startSandboxDiagnostic(owner);
    assert.equal(aiCalls,0);assert.equal(state.workspace.mode,'sandbox');assert.equal(state.workspace.profile,'sandbox-diagnostic');assert.equal(state.capabilities.aiReady,false);assert.equal(state.workspace.reservedCents,0);
    assert.equal(state.operations.length,1);const op=state.operations[0];
    assert.equal(op.sku,'workflow-review');assert.equal(op.amountCents,18000);assert.equal(op.currency,'USD');assert.equal(op.merchantId,config.PAYPAL_MERCHANT_ID);assert.equal(op.providerMode,'sandbox');assert.equal(op.aiSource,'sandbox-diagnostic');assert.equal(op.status,'PROPOSED');assert.equal(op.orderId,null);assert.equal(op.captureId,null);
    const receipt=await f.service.evidence(owner,op.id);const source=JSON.parse(receipt.events.find(event=>event.type==='PROPOSAL_CREATED').detail);
    assert.equal(source.source,'sandbox-diagnostic');assert.equal(source.manual,true);assert.equal(source.aiCalled,false);assert.equal(source.diagnosticProfile,'paypal-sandbox-v1');assert.equal(source.provenance,undefined);assert.equal(receipt.approvalDigest,null);assert.match(receipt.claim,/No AI model was called/);
    const fresh=new ProofPayService({db:f.db,env:config});assert.equal((await fresh.state(owner)).workspace.profile,'sandbox-diagnostic');
    assert.equal((await f.db.prepare('SELECT COUNT(*) n FROM proofpay_rehearsal_orders').first()).n,0);
  } finally {globalThis.fetch=original;f.db.close();}
});
test('diagnostic: missing owner or PayPal config cannot create a workspace or silently switch to rehearsal',async()=>{
  for(const [options,actor,expected] of [[{},'', 'AUTH_REQUIRED'],[{env:{}},owner,'PAYPAL_NOT_CONFIGURED']]){
    const f=await fixture(options);try{await assert.rejects(f.service.startSandboxDiagnostic(actor),code(expected));assert.equal((await f.db.prepare('SELECT COUNT(*) n FROM proofpay_workspaces').first()).n,0);}finally{f.db.close();}
  }
});
test('diagnostic: ordinary AI proposals still require a model and diagnostic workspaces cannot call one',async()=>{
  const f=await fixture();try {
    await f.service.start(owner,'sandbox');
    await assert.rejects(f.service.propose(owner,{request:'Review our workflow',mode:'sandbox',idempotencyKey:'normal-ai-key'}),code('AI_NOT_CONFIGURED'));
    assert.equal((await f.service.state(owner)).operations.length,0);
    await f.service.startSandboxDiagnostic(owner);
    const modelCapable=new ProofPayService({db:f.db,env:{...config,AI_API_KEY:'synthetic-key',AI_BASE_URL:'https://synthetic.invalid',AI_MODEL:'synthetic-model'},ai:async()=>{throw Error('Must not call model');}});
    await assert.rejects(modelCapable.propose(owner,{request:'Create another item',mode:'sandbox',idempotencyKey:'diagnostic-ai-key'}),code('DIAGNOSTIC_FIXED_CATALOGUE'));
    assert.equal((await modelCapable.state(owner)).operations.length,1);
  }finally{f.db.close();}
});
test('diagnostic: proposal provenance failure rolls back workspace, proposal and active session together',async()=>{
  const f=await fixture();try{
    const prior=await f.service.start(owner,'rehearsal',true);
    await f.db.exec("CREATE TRIGGER reject_diagnostic_source BEFORE INSERT ON proofpay_events WHEN NEW.type = 'PROPOSAL_CREATED' BEGIN SELECT RAISE(ABORT, 'synthetic event failure'); END;");
    await assert.rejects(f.service.startSandboxDiagnostic(owner));
    assert.equal((await f.service.state(owner)).workspace.id,prior.workspace.id);
    assert.equal((await f.db.prepare('SELECT COUNT(*) n FROM proofpay_workspaces').first()).n,1);
    assert.equal((await f.db.prepare("SELECT COUNT(*) n FROM proofpay_operations WHERE ai_source='sandbox-diagnostic'").first()).n,0);
  }finally{f.db.close();}
});
test('diagnostic: existing financial protections retain buyer preflight, unknown hold and read-only recovery',async()=>{
  let current,createCalls=0,captureCalls=0,getCalls=0;
  const provider={
    async create(op){createCalls++;current={id:'synthetic-sandbox-order',status:'PAYER_ACTION_REQUIRED',purchase_units:[{reference_id:op.id,custom_id:op.id,payee:{merchant_id:op.merchant_id},amount:{currency_code:'USD',value:'180.00'}}],links:[{rel:'payer-action',href:'https://www.sandbox.paypal.com/checkoutnow?token=synthetic'}]};return structuredClone(current);},
    async get(){getCalls++;return structuredClone(current);},
    async capture(){captureCalls++;current.status='COMPLETED';current.purchase_units[0].payments={captures:[{id:'synthetic-capture',status:'COMPLETED',final_capture:true,amount:{currency_code:'USD',value:'180.00'}}]};return structuredClone(current);},
  };
  const f=await fixture({provider});try{
    const state=await f.service.startSandboxDiagnostic(owner);const op=state.operations[0];
    await assert.rejects(f.service.createOrder(owner,op.id,1,'https://proofpay.example'),code('ORDER_STATE'));assert.equal(createCalls,0);
    await assert.rejects(f.service.approve('other-owner',op.id,1),code('NOT_FOUND'));
    await f.service.approve(owner,op.id,1);await f.service.createOrder(owner,op.id,1,'https://proofpay.example');assert.equal(createCalls,1);
    await assert.rejects(f.service.capture(owner,op.id,1),code('BUYER_APPROVAL_REQUIRED'));assert.equal(captureCalls,0);
    current.status='APPROVED';await f.service.capture(owner,op.id,1,'drop-response');assert.equal(captureCalls,1);
    const unknown=await f.service.state(owner);assert.equal(unknown.operations[0].status,'UNKNOWN');assert.equal(unknown.workspace.reservedCents,18000);
    await assert.rejects(f.service.startSandboxDiagnostic(owner),code('SANDBOX_WORKSPACE_HELD'));
    await assert.rejects(f.service.start(owner,'rehearsal',true),code('SANDBOX_WORKSPACE_HELD'));
    assert.equal((await f.service.state(owner)).workspace.id,state.workspace.id);
    const fresh=new ProofPayService({db:f.db,env:config,provider});const reads=getCalls;
    const recovered=await fresh.reconcile(owner,op.id);assert.equal(getCalls,reads+1);assert.equal(captureCalls,1);assert.equal(createCalls,1);assert.equal(recovered.operations[0].status,'CONFIRMED');assert.equal(recovered.workspace.committedCents,18000);assert.equal(recovered.workspace.reservedCents,0);
    assert.match((await fresh.evidence(owner,op.id)).claim,/No AI model was called/);
  }finally{f.db.close();}
});
test('diagnostic: HTTP action requires trusted owner, same origin and empty fixed-catalogue body',async()=>{
  const f=await fixture();Object.assign(env,config,{DB:f.db});
  const req=(body={},headers={},method='POST')=>new Request('https://proofpay.example/api/sandbox/diagnostic/start',{method,headers:{'content-type':'application/json',origin:'https://proofpay.example',cookie:ownerCookie(env),...headers},...(method==='POST'?{body:JSON.stringify(body)}:{})});
  try{
    for(const [request,status] of [[req({}, {cookie:'','oai-authenticated-user-id':owner}),401],[req({}, {origin:'https://attacker.invalid'}),403],[req({sku:'starter-review',amountCents:1}),400],[req({}, {}, 'GET'),405]])assert.equal((await handle(request,'start-diagnostic')).status,status);
    assert.equal((await f.db.prepare('SELECT COUNT(*) n FROM proofpay_workspaces').first()).n,0);
    const response=await handle(req(),'start-diagnostic');assert.equal(response.status,200);assert.equal((await response.json()).state.operations[0].aiSource,'sandbox-diagnostic');
  }finally{for(const key of Object.keys(env))delete env[key];f.db.close();}
});

// Synthetic SQLite/transport fixtures only. This suite verifies diagnostic
// isolation and policy reuse, not a real PayPal account or external transaction.
