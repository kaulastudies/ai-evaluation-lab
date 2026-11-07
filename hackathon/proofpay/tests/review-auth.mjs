import assert from 'node:assert/strict';
import { test, after } from 'node:test';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'esbuild';
const dir=await mkdtemp(join(tmpdir(),'proofpay-auth-review-'));
const bundle=join(dir,'auth.mjs');
await build({entryPoints:['lib/proofpay/auth.ts'],outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
const {authenticateRequest}=await import(pathToFileURL(bundle));
after(()=>rm(dir,{recursive:true,force:true}));
function request(headers={},method='POST'){return new Request('https://proofpay.example/api/operations/op/capture',{method,headers:{'oai-authenticated-user-id':'test-owner','content-type':'application/json',origin:'https://proofpay.example','sec-fetch-site':'same-origin',...headers}});}
test('review: authenticated same-origin JSON mutation accepted',()=>assert.equal(authenticateRequest(request()),'test-owner'));
test('review: absent trusted-ingress identity denied',()=>assert.throws(()=>authenticateRequest(request({'oai-authenticated-user-id':''})),error=>error.code==='AUTH_REQUIRED'));
test('review: cross-origin mutation denied',()=>assert.throws(()=>authenticateRequest(request({origin:'https://attacker.invalid'})),error=>error.code==='ORIGIN_REJECTED'));
test('review: missing mutation origin denied',()=>{const r=request();r.headers.delete('origin');assert.throws(()=>authenticateRequest(r),error=>error.code==='ORIGIN_REJECTED');});
test('review: cross-site fetch metadata denied despite claimed matching origin',()=>assert.throws(()=>authenticateRequest(request({'sec-fetch-site':'cross-site'})),error=>error.code==='ORIGIN_REJECTED'));
test('review: simple form POST content type denied',()=>assert.throws(()=>authenticateRequest(request({'content-type':'application/x-www-form-urlencoded'})),error=>error.code==='JSON_REQUIRED'));
test('review: read still requires authenticated ingress identity',()=>assert.throws(()=>authenticateRequest(request({'oai-authenticated-user-id':''},'GET')),error=>error.code==='AUTH_REQUIRED'));
// These unit tests validate the app contract only. They do not prove that a
// hosting ingress strips forged oai-authenticated-user-id request headers.
