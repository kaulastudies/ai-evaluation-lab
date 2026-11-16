import assert from 'node:assert/strict';
import {test,after} from 'node:test';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {build} from 'esbuild';
import {ReviewD1} from './review-d1.mjs';
import {ownerConfig,ownerCookie,TEST_OWNER_PASSWORD} from './owner-fixture.mjs';
const dir=await mkdtemp(join(tmpdir(),'proofpay-vercel-review-')),bundle=join(dir,'owner.mjs');
const env=ownerConfig();globalThis.__proofpayOwnerTestEnv=env;
await build({stdin:{contents:'export * from "./lib/proofpay/auth.ts";export * from "./lib/proofpay/login.ts";',resolveDir:process.cwd()},outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent',plugins:[{name:'runtime-test-only',setup(b){b.onResolve({filter:/^\.\/runtime$/},()=>({path:'runtime',namespace:'test-runtime'}));b.onLoad({filter:/.*/,namespace:'test-runtime'},()=>({contents:'const env=globalThis.__proofpayOwnerTestEnv;export function getRuntimeConfiguration(){return env;}export function getDatabase(){return env.DB;}'}));}}]});
const {ownerLogin,authenticateRequest,verifyOwnerPassword,sessionCookie}=await import(pathToFileURL(bundle));
after(async()=>{delete globalThis.__proofpayOwnerTestEnv;await rm(dir,{recursive:true,force:true});});
async function fixture(){const db=new ReviewD1(':memory:');await db.exec(await readFile('drizzle/0001_owner_auth_limits.sql','utf8'));env.DB=db;return db;}
function req(body={password:TEST_OWNER_PASSWORD},headers={}){return new Request('https://proofpay.example/api/auth/login',{method:'POST',headers:{origin:'https://proofpay.example','content-type':'application/json',...headers},body:JSON.stringify(body)});}
test('vercel: scrypt owner key accepts only the configured secret',async()=>{assert.equal(await verifyOwnerPassword(TEST_OWNER_PASSWORD,env),true);assert.equal(await verifyOwnerPassword('a-different-owner-key-for-test',env),false);});
test('vercel: login issues secure owner session, logout expires it and neither returns the key',async()=>{
  const db=await fixture();try{const response=await ownerLogin(req());assert.equal(response.status,200);assert.deepEqual(await response.json(),{ok:true});const cookie=response.headers.get('set-cookie');for(const flag of ['__Host-proofpay-session=','HttpOnly','Secure','SameSite=Strict','Path=/','Max-Age=28800'])assert.ok(cookie.includes(flag));assert.ok(!cookie.includes(TEST_OWNER_PASSWORD));assert.equal(await authenticateRequest(new Request('https://proofpay.example/api/state',{headers:{cookie:cookie.split(';')[0]}}),env),env.OWNER_ID);const logout=await ownerLogin(req({}),true);assert.equal(logout.status,200);assert.ok(logout.headers.get('set-cookie').includes('Max-Age=0'));}finally{db.close();delete env.DB;}
});
test('vercel: durable global login cap persists across repeated requests and fails closed',async()=>{
  const db=await fixture();try{for(let i=0;i<10;i++)assert.equal((await ownerLogin(req({password:'wrong'}))).status,401);const denied=await ownerLogin(req());assert.equal(denied.status,429);assert.equal(denied.headers.get('retry-after'),'60');assert.equal((await db.prepare("SELECT attempts FROM proofpay_auth_limits WHERE id='owner-login'").first()).attempts,10);}finally{db.close();delete env.DB;}
});
test('vercel: sign-in rejects origin spoofing and missing config without exposing credentials',async()=>{
  assert.equal((await ownerLogin(req(undefined,{origin:'https://attacker.invalid'}))).status,403);
  const secret=env.SESSION_SECRET;delete env.SESSION_SECRET;
  try{const response=await ownerLogin(req());assert.equal(response.status,503);assert.equal((await response.json()).code,'AUTH_NOT_CONFIGURED');}finally{env.SESSION_SECRET=secret;}
  assert.ok(!sessionCookie(ownerCookie(env)).includes(TEST_OWNER_PASSWORD));
});
