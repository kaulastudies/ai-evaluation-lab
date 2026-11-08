import assert from 'node:assert/strict';
import { test, after } from 'node:test';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'esbuild';
import { ReviewD1 } from './review-d1.mjs';
import { ownerConfig, ownerCookie } from './owner-fixture.mjs';
import { fundedAiConfig } from './ai-fixture.mjs';

const dir = await mkdtemp(join(tmpdir(), 'proofpay-security-'));
const testEnv = ownerConfig({OWNER_ID:'security-owner'});
globalThis.__proofpaySecurityEnv = testEnv;
const entry = join(dir, 'security.mjs');
await build({stdin:{contents:'export * from "./lib/proofpay/http.ts"; export * from "./lib/proofpay/auth.ts"; export * from "./lib/proofpay/request.ts"; export * from "./lib/proofpay/provider.ts"; export {propose} from "./lib/proofpay/ai.ts";',resolveDir:process.cwd()},outfile:entry,bundle:true,platform:'node',format:'esm',logLevel:'silent',plugins:[{name:'test-worker-env',setup(b){b.onResolve({filter:/^\.\/runtime$/},()=>({path:'env',namespace:'test-env'}));b.onLoad({filter:/.*/,namespace:'test-env'},()=>({contents:'const env=globalThis.__proofpaySecurityEnv;export function getRuntimeConfiguration(){return env;} export function getDatabase(){return env.DB;} export async function getRequestConfiguration(config){return config;}'}));}}]});
const {handle, authenticateRequest, parseApiRequest, readTextLimited, PayPalSandboxProvider, propose} = await import(pathToFileURL(entry));
after(async()=>{delete globalThis.__proofpaySecurityEnv;await rm(dir,{recursive:true,force:true});});
const id = '10000000-0000-4000-8000-000000000001';
function request(body={}, options={}) {
  const method=options.method??'POST';
  return new Request(`https://proofpay.example/api/operations/${id}/approve`,{method,headers:{cookie:ownerCookie(testEnv),origin:'https://proofpay.example','content-type':'application/json',...options.headers},...(method==='GET'||method==='HEAD'?{}:{body:typeof body==='string'?body:JSON.stringify(body)})});
}
const code = expected => error => error.code===expected;

test('security: application/json lookalikes and forged identities fail closed',async()=>{
  for(const type of ['application/jsonp','application/json-malicious','text/plain','application/x-www-form-urlencoded']) await assert.rejects(authenticateRequest(request({}, {headers:{'content-type':type}}),testEnv),code('JSON_REQUIRED'));
  assert.equal(await authenticateRequest(request({}, {headers:{'content-type':'application/json; charset=utf-8'}}),testEnv),'security-owner');
  await assert.rejects(authenticateRequest(request({}, {headers:{cookie:'','oai-authenticated-user-id':'security-owner'}}),testEnv),code('AUTH_REQUIRED'));
});
test('security: read-only and mutation actions reject wrong HTTP methods before database access',async()=>{
  for(const [method,action] of [['GET','start-rehearsal'],['GET','approve'],['POST','state'],['POST','evidence']]) {
    const response=await handle(request({}, {method}), action, id);
    assert.equal(response.status,405); assert.equal((await response.json()).code,'METHOD_NOT_ALLOWED');
    assert.equal(response.headers.get('allow'),['state','evidence'].includes(action)?'GET, HEAD':'POST');
  }
});
test('security: malformed operation IDs, versions, compressed bodies and unsupported authority fields are rejected',async()=>{
  await assert.rejects(parseApiRequest(request({approvalVersion:1}),'approve','../../other-owner'),code('INVALID_OPERATION'));
  for(const version of [null,0,-1,1.5,'1',Number.MAX_SAFE_INTEGER+1]) await assert.rejects(parseApiRequest(request({approvalVersion:version}),'approve',id),code('INVALID_VERSION'));
  await assert.rejects(parseApiRequest(request({approvalVersion:1,amountCents:1}),'approve',id),code('UNSUPPORTED_FIELD'));
  await assert.rejects(parseApiRequest(request({}, {headers:{'content-encoding':'gzip'}}),'start-rehearsal'),code('ENCODING_UNSUPPORTED'));
  assert.deepEqual(await parseApiRequest(request({approvalVersion:1}),'approve',id),{approvalVersion:1});
});
test('security: chunked oversized body is cancelled at the byte limit without trusting content-length',async()=>{
  let reads=0, cancelled=false;
  const stream=new ReadableStream({pull(c){reads++;c.enqueue(new Uint8Array(3000).fill(32));},cancel(){cancelled=true;}},{highWaterMark:0});
  const req=new Request('https://proofpay.example/api/rehearsal/start',{method:'POST',headers:{'content-length':'1'},body:stream,duplex:'half'});
  await assert.rejects(parseApiRequest(req,'start-rehearsal'),code('PAYLOAD_TOO_LARGE'));
  assert.equal(cancelled,true); assert.ok(reads<=4,`Unexpected extra body reads: ${reads}`);
});
test('security: oversized declared bodies are rejected before reading; multibyte text is counted in bytes',async()=>{
  let reads=0;
  const stream=new ReadableStream({pull(){reads++;},cancel(){}},{highWaterMark:0});
  const req=new Request('https://proofpay.example',{method:'POST',headers:{'content-length':'10001'},body:stream,duplex:'half'});
  await assert.rejects(readTextLimited(req,10000),code('PAYLOAD_TOO_LARGE')); assert.equal(reads,0);
  await assert.rejects(readTextLimited(new Response('💳'.repeat(2501)),10000),code('PAYLOAD_TOO_LARGE'));
  assert.equal((await readTextLimited(new Response(' '.repeat(10000)),10000)).length,10000);
});
test('security: truncated UTF-8 and nonobject JSON are rejected without unbounded parsing',async()=>{
  await assert.rejects(readTextLimited(new Response(new Uint8Array([0xc3])),10000),code('INVALID_PAYLOAD'));
  for(const value of ['null','[]','true','"text"','{']) await assert.rejects(parseApiRequest(request(value),'start-rehearsal'),error=>['INVALID_JSON'].includes(error.code));
});
test('security: API success and errors retain no-store, no-referrer, nosniff and restrictive JSON document policy',async()=>{
  const db=new ReviewD1(':memory:');await db.exec(await readFile('drizzle/0000_greedy_living_lightning.sql','utf8'));testEnv.DB=db;
  try {
    const responses=[await handle(request({}, {method:'GET'}),'state'),await handle(request({}, {headers:{origin:'https://attacker.invalid'}}),'start-rehearsal')];
    assert.deepEqual(responses.map(r=>r.status),[200,403]);
    for(const response of responses){assert.equal(response.headers.get('cache-control'),'no-store');assert.equal(response.headers.get('referrer-policy'),'no-referrer');assert.equal(response.headers.get('x-content-type-options'),'nosniff');assert.equal(response.headers.get('cross-origin-resource-policy'),'same-origin');assert.ok(response.headers.get('content-security-policy').includes("frame-ancestors 'none'"));}
  } finally {delete testEnv.DB;db.close();}
});

const config={PAYPAL_CLIENT_ID:'synthetic-client',PAYPAL_CLIENT_SECRET:'synthetic-secret',PAYPAL_MERCHANT_ID:'seller',...fundedAiConfig()};
const op={id:'operation',order_id:'order',merchant_id:'seller',currency:'USD',amount_cents:18000,create_request_id:'create',capture_request_id:'capture'};
test('security: credentialed PayPal auth and order fetches never follow redirects or retry',async()=>{
  const original=globalThis.fetch;
  try {
    for(const redirectAt of ['auth','order']){
      const calls=[];globalThis.fetch=async(url,init)=>{calls.push({url:String(url),init});return String(url).endsWith('/token')&&redirectAt!=='auth'?Response.json({access_token:'synthetic-access'}):new Response(null,{status:307,headers:{location:'https://attacker.invalid/collect'}});};
      const provider=new PayPalSandboxProvider(config);await assert.rejects(provider.get(op));
      assert.equal(calls.length,redirectAt==='auth'?1:2);assert.ok(calls.every(call=>call.init.redirect==='manual'));assert.ok(calls.every(call=>call.url.startsWith('https://api-m.sandbox.paypal.com/')));
    }
  } finally {globalThis.fetch=original;}
});
test('security: model redirect, oversize response and malformed token create no fallback or secret echo',async()=>{
  const original=globalThis.fetch;
  try {
    let calls=0;
    globalThis.fetch=async(_url,init)=>{calls++;assert.equal(init.redirect,'manual');return new Response(null,{status:302,headers:{location:'https://attacker.invalid/collect'}});};
    await assert.rejects(propose('workflow','sandbox',config),code('AI_UNAVAILABLE'));assert.equal(calls,1);
    globalThis.fetch=async()=>new Response('x'.repeat(262145));
    await assert.rejects(propose('workflow','sandbox',config),code('AI_UNAVAILABLE'));
    globalThis.fetch=async()=>Response.json({access_token:{secret:'do-not-echo'}});
    await assert.rejects(new PayPalSandboxProvider(config).get(op),error=>error.code==='PAYPAL_AUTH'&&!error.message.includes('do-not-echo'));
  } finally {globalThis.fetch=original;}
});

// Synthetic streams, transport fixtures and local SQLite only. These checks do
// not establish private ingress identity stripping, hosted headers or live API
// outcomes. Credential redirect behavior follows the Cloudflare Workers contract.
