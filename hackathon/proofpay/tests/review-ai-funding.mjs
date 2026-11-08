import assert from 'node:assert/strict';
import {test,after} from 'node:test';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {fork} from 'node:child_process';
import {build} from 'esbuild';
import {ReviewD1} from './review-d1.mjs';
import {fundedAiConfig} from './ai-fixture.mjs';

const temp=await mkdtemp(join(tmpdir(),'proofpay-funding-review-'));
const serviceBundle=join(temp,'service.mjs'),aiBundle=join(temp,'ai.mjs');
await build({entryPoints:['lib/proofpay/service.ts'],outfile:serviceBundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
await build({entryPoints:['lib/proofpay/ai.ts'],outfile:aiBundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
const {ProofPayService}=await import(pathToFileURL(serviceBundle));
const {propose}=await import(pathToFileURL(aiBundle));
const base=await readFile('drizzle/0000_greedy_living_lightning.sql','utf8') + '\n' + await readFile('drizzle/0003_business_profiles.sql','utf8');
const migration=await readFile('drizzle/0002_ai_funding.sql','utf8');
after(()=>rm(temp,{recursive:true,force:true}));
const payPal={PAYPAL_CLIENT_ID:'synthetic-client',PAYPAL_CLIENT_SECRET:'synthetic-secret',PAYPAL_MERCHANT_ID:'synthetic-seller'};
const input=(key='funding-review-key')=>({mode:'sandbox',request:'Workflow review',idempotencyKey:key});
const choice=()=>({sku:'workflow-review',rationale:'Synthetic model response.',source:'model'});
const response=()=>Response.json({id:'synthetic-generation',model:'gpt-4.1-mini',choices:[{message:{content:JSON.stringify({sku:'workflow-review',rationale:'Fits the review.'})}}]});
let serial=0;
async function fixture(overrides={},ai) {
  const filename=join(temp,`case-${serial++}.sqlite`),db=new ReviewD1(filename);
  await db.exec(base);await db.exec(migration);
  const config={...payPal,...fundedAiConfig(overrides)};
  const service=new ProofPayService({db,env:config,...(ai?{ai}:{})});
  await service.start('funding-owner','sandbox');return{filename,db,service,config};
}
const count=async db=>(await db.prepare('SELECT COUNT(*) n FROM proofpay_ai_attempts').first()).n;
const code=expected=>error=>error.code===expected;

test('funding: paid/direct-provider configuration is disabled by default with zero network calls',async()=>{
  const old=globalThis.fetch;let calls=0;globalThis.fetch=async()=>{calls++;throw Error('forbidden');};
  try {
    for(const config of [{},{AI_API_KEY:'personal-key',AI_BASE_URL:'https://api.openai.com/v1',AI_MODEL:'personal-model'},fundedAiConfig({AI_FUNDING_MODE:'paid'}),fundedAiConfig({AI_GATEWAY_FREE_ONLY_CONFIRMED:'false'})]) await assert.rejects(propose('Review','sandbox',config),code('AI_NOT_CONFIGURED'));
    assert.equal(calls,0);
  }finally{globalThis.fetch=old;}
});
test('funding: missing, expired, over-limit and unreviewed grant settings block before network',async()=>{
  const old=globalThis.fetch;let calls=0;globalThis.fetch=async()=>{calls++;throw Error('forbidden');};
  try {
    for(const overrides of [
      {AI_GATEWAY_GRANT_ID:''},{AI_GATEWAY_GRANT_ID:'unsafe/grant'},{AI_GATEWAY_GRANT_EXPIRES_AT:'2020-01-01T00:00:00Z'},
      {AI_GATEWAY_GRANT_EXPIRES_AT:'2030-02-31T00:00:00Z'},{AI_GATEWAY_GRANT_EXPIRES_AT:'tomorrow'},
      {AI_GATEWAY_MAX_REQUESTS:'0'},{AI_GATEWAY_MAX_REQUESTS:'11'},{AI_GATEWAY_MAX_REQUESTS:'1.5'},
      {AI_GATEWAY_MODEL:'openai/gpt-expensive'},{AI_GATEWAY_MODEL:'vmc/unreviewed'},
      {VERCEL_OIDC_TOKEN:''},{VERCEL_OIDC_TOKEN:'Bearer malformed'},
    ]) await assert.rejects(propose('Review','sandbox',fundedAiConfig(overrides)));
    assert.equal(calls,0);
  }finally{globalThis.fetch=old;}
});
test('funding: populated legacy or gateway API-key settings cannot override OIDC',async()=>{
  const old=globalThis.fetch;let calls=0;globalThis.fetch=async()=>{calls++;throw Error('forbidden');};
  try {
    for(const field of ['AI_API_KEY','AI_BASE_URL','AI_MODEL','AI_GATEWAY_API_KEY']) await assert.rejects(propose('Review','sandbox',fundedAiConfig({[field]:'forbidden-personal-configuration'})),code('AI_FUNDING_RESTRICTED'));
    assert.equal(calls,0);
  }finally{globalThis.fetch=old;}
});
test('funding: approved request uses only fixed Gateway model/provider, OIDC, bounded tokens and no BYOK',async()=>{
  const old=globalThis.fetch,calls=[];globalThis.fetch=async(url,options)=>{calls.push({url:String(url),options});return response();};
  try {
    const config=fundedAiConfig({OPENAI_API_KEY:'must-never-be-used'});
    const result=await propose('Review','sandbox',config);assert.equal(result.source,'model');assert.equal(calls.length,1);
    assert.equal(calls[0].url,'https://ai-gateway.vercel.sh/v1/chat/completions');
    const {options}=calls[0],body=JSON.parse(options.body);
    assert.equal(options.headers.Authorization,'Bearer synthetic.oidc.token');assert.equal(options.redirect,'manual');
    assert.deepEqual(body.providerOptions,{gateway:{only:['openai'],models:[]}});
    assert.equal(body.model,'openai/gpt-4.1-mini');assert.equal(body.max_tokens,400);assert.equal(body.stream,false);
    assert.equal(body.response_format.type,'json_schema');assert.equal(body.response_format.json_schema.strict,true);
    assert.ok(!JSON.stringify(calls).includes('must-never-be-used'));assert.ok(!JSON.stringify(result).includes('synthetic.oidc.token'));
  }finally{globalThis.fetch=old;}
});
test('funding: authentication, balance, rate, redirect and transport errors never retry or fall back',async()=>{
  const old=globalThis.fetch;
  try {
    for(const status of [302,401,402,403,429,503]) {
      let calls=0;globalThis.fetch=async()=>{calls++;return new Response('rejected',{status});};
      await assert.rejects(propose('Review','sandbox',fundedAiConfig()),code('AI_UNAVAILABLE'));assert.equal(calls,1);
    }
    let calls=0;globalThis.fetch=async()=>{calls++;throw Error('timeout');};
    await assert.rejects(propose('Review','sandbox',fundedAiConfig()),code('AI_UNAVAILABLE'));assert.equal(calls,1);
  }finally{globalThis.fetch=old;}
});
test('funding: oversized model prompt is rejected and rehearsal does not use any grant',async()=>{
  const old=globalThis.fetch;let calls=0;globalThis.fetch=async()=>{calls++;throw Error('forbidden');};
  try {
    await assert.rejects(propose('x'.repeat(2001),'sandbox',fundedAiConfig()),code('INVALID_PROPOSAL'));
    const result=await propose('Smaller scope','rehearsal',{});assert.equal(result.source,'rehearsal-rule');assert.equal(calls,0);
  }finally{globalThis.fetch=old;}
});
test('funding: workspace allows one attempt while successful idempotent replay makes no additional model call',async()=>{
  let calls=0;const f=await fixture({},async()=>{calls++;return choice();});
  try {
    await f.service.propose('funding-owner',input());await f.service.propose('funding-owner',input());
    await assert.rejects(f.service.propose('funding-owner',input('second-request-key')),code('AI_ALLOWANCE_USED'));
    assert.equal(calls,1);assert.equal(await count(f.db),1);
    const evidence=await f.service.evidence('funding-owner',(await f.service.state('funding-owner')).operations[0].id);
    const detail=JSON.parse(evidence.events.find(event=>event.type==='PROPOSAL_CREATED').detail);
    assert.equal(detail.funding.mode,'vercel-free-credit');assert.equal(detail.funding.billingVerified,false);
  }finally{f.db.close();}
});
test('funding: failed model request remains consumed across service restart and new workspace cannot exceed grant cap',async()=>{
  const old=globalThis.fetch;let calls=0;globalThis.fetch=async()=>{calls++;throw Error('uncertain provider response');};
  const f=await fixture();let closed=false;
  try {
    await assert.rejects(f.service.propose('funding-owner',input()),code('AI_UNAVAILABLE'));assert.equal(await count(f.db),1);
    f.db.close();closed=true;const db=new ReviewD1(f.filename);
    try {
      const fresh=new ProofPayService({db,env:f.config});
      await assert.rejects(fresh.propose('funding-owner',input()),code('AI_ALLOWANCE_USED'));
      await fresh.start('funding-owner','sandbox');
      await assert.rejects(fresh.propose('funding-owner',input('new-workspace-key')),code('AI_ALLOWANCE_USED'));
      assert.equal(calls,1);assert.equal(await count(db),1);
    }finally{db.close();}
  }finally{globalThis.fetch=old;if(!closed)f.db.close();}
});
test('funding: configured grant cap three holds across four independent workspaces',async()=>{
  let calls=0;const f=await fixture({AI_GATEWAY_MAX_REQUESTS:'3'},async()=>{calls++;return choice();});
  try {
    for(let i=0;i<3;i++){if(i)await f.service.start('funding-owner','sandbox');await f.service.propose('funding-owner',input(`grant-attempt-${i}`));}
    await f.service.start('funding-owner','sandbox');
    await assert.rejects(f.service.propose('funding-owner',input('grant-attempt-four')),code('AI_ALLOWANCE_USED'));
    assert.equal(calls,3);assert.equal(await count(f.db),3);
    assert.deepEqual((await f.db.prepare('SELECT slot FROM proofpay_ai_attempts ORDER BY slot').all()).results.map(row=>row.slot),[1,2,3]);
  }finally{f.db.close();}
});
test('funding: claim and audit failure rolls back before model dispatch',async()=>{
  let calls=0;const f=await fixture({},async()=>{calls++;return choice();});
  try {
    await f.db.exec("CREATE TEMP TRIGGER reject_ai_audit BEFORE INSERT ON proofpay_events WHEN NEW.type='AI_FREE_ATTEMPT_CLAIMED' BEGIN SELECT RAISE(ABORT,'synthetic audit failure'); END;");
    await assert.rejects(f.service.propose('funding-owner',input()));assert.equal(calls,0);assert.equal(await count(f.db),0);
    await f.db.exec('DROP TRIGGER reject_ai_audit');await f.service.propose('funding-owner',input());
    assert.equal(calls,1);assert.equal(await count(f.db),1);
  }finally{f.db.close();}
});
function contender(filename,owner,config) {
  const child=fork(resolve('tests/review-ai-funding-worker.mjs'),[filename,serviceBundle,owner,JSON.stringify(config)],{stdio:['ignore','pipe','pipe','ipc']});
  let readyResolve,resultResolve,resultReject,stderr='';
  const ready=new Promise(resolve=>{readyResolve=resolve;});
  const result=new Promise((resolve,reject)=>{resultResolve=resolve;resultReject=reject;});
  child.stderr.on('data',chunk=>{stderr+=chunk;});
  child.on('message',value=>{if(value.ready)readyResolve();else resultResolve(value);});
  child.on('error',resultReject);child.on('exit',code=>{if(code)resultReject(Error(`Funding worker failed (${code}): ${stderr}`));});
  return{child,ready,result};
}
test('funding: two processes competing for the final grant slot dispatch exactly one synthetic model call',{timeout:15000},async()=>{
  const f=await fixture();
  try {
    await f.service.start('other-owner','sandbox');
    const a=contender(f.filename,'funding-owner',f.config),b=contender(f.filename,'other-owner',f.config);
    await Promise.all([a.ready,b.ready]);a.child.send('go');b.child.send('go');
    const results=await Promise.all([a.result,b.result]);
    assert.equal(results.filter(result=>result.ok).length,1);assert.equal(results.find(result=>!result.ok).code,'AI_ALLOWANCE_USED');
    assert.equal(results.reduce((total,result)=>total+result.calls,0),1);assert.equal(await count(f.db),1);
  }finally{f.db.close();}
});
