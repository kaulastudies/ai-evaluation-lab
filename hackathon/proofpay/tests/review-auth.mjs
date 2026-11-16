import assert from 'node:assert/strict';
import {test,after} from 'node:test';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {build} from 'esbuild';
import {ownerConfig,ownerCookie} from './owner-fixture.mjs';
const dir=await mkdtemp(join(tmpdir(),'proofpay-auth-review-'));const bundle=join(dir,'auth.mjs');
await build({entryPoints:['lib/proofpay/auth.ts'],outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
const {authenticateRequest}=await import(pathToFileURL(bundle));after(()=>rm(dir,{recursive:true,force:true}));
const config=ownerConfig();
function request(headers={},method='POST'){return new Request('https://proofpay.example/api/operations/op/capture',{method,headers:{cookie:ownerCookie(config),'content-type':'application/json',origin:'https://proofpay.example','sec-fetch-site':'same-origin',...headers}});}
test('review: independently signed owner session and same-origin JSON mutation accepted',async()=>assert.equal(await authenticateRequest(request(),config),'test-owner'));
test('review: forged Sites and Vercel identity headers cannot authenticate',async()=>{for(const header of ['oai-authenticated-user-id','x-openai-user-id','x-vercel-user-id'])await assert.rejects(authenticateRequest(request({cookie:'',[header]:'test-owner'}),config),e=>e.code==='AUTH_REQUIRED');});
test('review: cross-origin mutation denied despite valid session',async()=>assert.rejects(authenticateRequest(request({origin:'https://attacker.invalid'}),config),e=>e.code==='ORIGIN_REJECTED'));
test('review: missing mutation origin denied',async()=>{const r=request();r.headers.delete('origin');await assert.rejects(authenticateRequest(r,config),e=>e.code==='ORIGIN_REJECTED');});
test('review: cross-site fetch metadata denied despite matching origin',async()=>assert.rejects(authenticateRequest(request({'sec-fetch-site':'cross-site'}),config),e=>e.code==='ORIGIN_REJECTED'));
test('review: simple form POST content type denied',async()=>assert.rejects(authenticateRequest(request({'content-type':'application/x-www-form-urlencoded'}),config),e=>e.code==='JSON_REQUIRED'));
test('review: reads require owner session and missing runtime auth fails closed',async()=>{await assert.rejects(authenticateRequest(request({cookie:''},'GET'),config),e=>e.code==='AUTH_REQUIRED');await assert.rejects(authenticateRequest(request(),{}),e=>e.code==='AUTH_NOT_CONFIGURED');});
test('review: expired, tampered, duplicated, foreign-owner and rotated-key sessions fail closed',async()=>{
  const valid=ownerCookie(config);
  for(const cookie of [ownerCookie(config,Date.now()-28801000),valid.slice(0,-2)+'xx',`${valid}; ${valid}`,ownerCookie({...config,OWNER_ID:'other-owner'})])await assert.rejects(authenticateRequest(request({cookie}),config),e=>e.code==='AUTH_REQUIRED');
  await assert.rejects(authenticateRequest(request(),{...config,SESSION_SECRET:'r'.repeat(43)}),e=>e.code==='AUTH_REQUIRED');
});
