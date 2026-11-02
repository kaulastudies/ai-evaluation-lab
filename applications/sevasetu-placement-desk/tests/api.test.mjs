import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createDeskServer } from '../server.mjs';
const DATA=JSON.parse(await readFile(new URL('../fixtures/sample-data.json',import.meta.url)));
test('actual HTTP API checks sessions, projection, purpose, candidate ownership and certificate workflow',async()=>{
 const server=createDeskServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 let cookie='';const request=async(route,body,options={})=>{const r=await fetch(base+route,{method:body===undefined?'GET':'POST',headers:{...(cookie?{Cookie:cookie}:{}),...(body===undefined?{}:{'Content-Type':'application/json'}),...options.headers},body:body===undefined?undefined:JSON.stringify(body)});if(r.headers.get('set-cookie'))cookie=r.headers.get('set-cookie').split(';')[0];return {status:r.status,data:await r.json(),headers:r.headers};};
 try{
  assert.equal((await request('/api/catalog')).status,401);assert.equal((await request('/sample-data.json')).status,404);assert.equal((await request('/fixtures/sample-data.json')).status,404);
  assert.equal((await request('/deployment.json')).data.mode,'local_fixture_api');
  const session=await request('/api/session',{role:'counsellor'});assert.equal(session.status,200);assert.match(session.headers.get('set-cookie'),/HttpOnly; SameSite=Strict/);const oldCookie=cookie;
  const lookup=await request('/api/lookup',{id:'ESM-DEMO-1001',purpose:'placement_review',role:'verifier'});assert.equal(lookup.data.dob,null);assert.equal(lookup.data.last_pay,null);
  assert.equal((await request('/api/lookup',{id:'ESM-DEMO-1001',purpose:'pay_reference'})).status,403);
  assert.equal((await request('/api/session',{role:'admin'})).status,400);
  assert.equal((await request('/api/lookup',{id:'ESM-DEMO-1001'},{headers:{Origin:'https://untrusted.example'}})).status,403);
  const submitted=await request('/api/submit',{id:'ESM-DEMO-1001',input:DATA.submission_example,purpose:'placement_review'});assert.equal(submitted.data.status,'pending');
  assert.equal((await request('/api/verify',{id:'ESM-DEMO-1001',qualificationID:submitted.data.id,purpose:'placement_review'})).status,403);
  await request('/api/session',{role:'verifier'});assert.notEqual(cookie,oldCookie);
  assert.equal((await request('/api/catalog',undefined,{headers:{Cookie:oldCookie}})).status,401);
  assert.equal((await request('/api/verify',{id:'ESM-DEMO-1001',qualificationID:submitted.data.id,purpose:'record_verification'})).data.status,'verified');
  assert.equal((await request('/api/assess',{id:'ESM-DEMO-1001',roleID:'warehouse-supervisor',purpose:'record_verification'})).data.state,'documented_checks_met');
  assert.equal((await request('/api/lookup',{id:'ESM-DEMO-1001',purpose:'pay_reference'})).data.last_pay.amount,72000);
  const cv=await request('/api/cv',{id:'ESM-DEMO-1001',roleID:'warehouse-supervisor',purpose:'record_verification'});assert(cv.data.text.includes(DATA.submission_example.title));assert(!cv.data.text.includes('72000'));
  await request('/api/session',{role:'candidate'});assert.equal((await request('/api/lookup',{id:'ESM-DEMO-1002'})).status,403);assert.equal((await request('/api/lookup',{id:'ESM-DEMO-1001'})).status,200);
  const audit=await request('/api/history',{id:'ESM-DEMO-1001'});assert(audit.data.some(e=>e.action==='verify_qualification'&&e.result==='verified'));assert(!JSON.stringify(audit.data).includes('72000'));
 }finally{await new Promise(r=>server.close(r));}
});
