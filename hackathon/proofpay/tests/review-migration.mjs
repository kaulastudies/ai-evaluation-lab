import assert from 'node:assert/strict';
import {test,after} from 'node:test';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
const directory=await mkdtemp(join(tmpdir(),'proofpay-migration-redaction-'));
after(()=>rm(directory,{recursive:true,force:true}));
const marker='SYNTHETIC_DO_NOT_LOG_PASSWORD';
function run(url,hook){
  const env={...process.env,DATABASE_URL:url};
  for(const name of ['DATABASE_URL_UNPOOLED','POSTGRES_URL_NON_POOLING','POSTGRES_URL'])delete env[name];
  return spawnSync(process.execPath,[...(hook?['--import',hook]:[]),resolve('scripts/migrate-postgres.mjs')],{env,encoding:'utf8',timeout:5000,maxBuffer:1024*1024});
}
async function hook(name,source){
  const path=join(directory,`${name}.mjs`);
  const moduleUrl=`data:text/javascript,${encodeURIComponent(source)}`;
  await writeFile(path,`import {registerHooks} from 'node:module';registerHooks({resolve(specifier,context,next){if(specifier==='pg')return{url:${JSON.stringify(moduleUrl)},shortCircuit:true};return next(specifier,context);}});`);
  return path;
}
function redacted(result,code){assert.equal(result.status,1);assert.equal(result.stderr,`${code}\n`);assert.ok(!`${result.stdout}${result.stderr}`.includes(marker));assert.ok(!`${result.stdout}${result.stderr}`.includes('postgresql://'));}
test('migration: malformed credential-bearing URL emits only bounded configuration failure',()=>{
  redacted(run(`postgresql://testuser:${marker}@invalid.test:notaport/db`),'MIGRATION_CONFIGURATION_INVALID');
});
test('migration: connection and pool-cleanup exceptions cannot echo credentials or raw causes',async()=>{
  const loader=await hook('connection',`export class Pool{on(){}async connect(){throw Object.assign(Error('${marker}'),{input:'postgresql://${marker}',cause:Error('${marker}')});}async end(){throw Error('${marker}');}}`);
  redacted(run(`postgresql://testuser:${marker}@invalid.test/db`,loader),'MIGRATION_CONNECTION_FAILED');
});
test('migration: transaction, rollback and release failures retain one redacted failure code',async()=>{
  const loader=await hook('rollback',`export class Pool{on(){}async connect(){return{async query(sql){if(sql==='BEGIN')return{};throw Error('${marker}');},release(){throw Error('${marker}');}};}async end(){throw Error('${marker}');}}`);
  redacted(run(`postgresql://testuser:${marker}@invalid.test/db`,loader),'MIGRATION_TRANSACTION_FAILED');
});
