import assert from 'node:assert/strict';
import {test,after} from 'node:test';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {build} from 'esbuild';
const dir=await mkdtemp(join(tmpdir(),'proofpay-pg-unit-'));const bundle=join(dir,'pg.mjs');
await build({entryPoints:['lib/proofpay/postgres-database.ts'],outfile:bundle,bundle:true,platform:'node',format:'esm',logLevel:'silent'});
const {PostgresDatabase,postgresSql}=await import(pathToFileURL(bundle));after(()=>rm(dir,{recursive:true,force:true}));
test('postgres: positional bindings and null-safe CAS translation preserve literals and event ordering',()=>{
  assert.equal(postgresSql("SELECT '?' AS text, created_at AS createdAt, operation_id AS operationId FROM proofpay_events WHERE id=? AND approval_digest IS ? AND approval_expires_at IS NOT ? ORDER BY rowid -- ?\n"),"SELECT '?' AS text, created_at AS \"createdAt\", operation_id AS \"operationId\" FROM proofpay_events WHERE id=$1 AND approval_digest IS NOT DISTINCT FROM $2 AND approval_expires_at IS DISTINCT FROM $3 ORDER BY sequence -- ?\n");
});
test('postgres: bigint results normalize to safe numbers and reject precision loss',async()=>{
  const pool={async query(){return{rows:[{created_at:'1760000000000'}],fields:[{name:'created_at',dataTypeID:20}],rowCount:1};}};const db=new PostgresDatabase(pool);
  assert.equal((await db.prepare('SELECT created_at').first()).created_at,1760000000000);
  pool.query=async()=>({rows:[{created_at:'9007199254740993'}],fields:[{name:'created_at',dataTypeID:20}],rowCount:1});await assert.rejects(db.prepare('SELECT created_at').first());
});
function fake(code){const calls=[];let connections=0;return {calls,get connections(){return connections;},async connect(){connections++;const number=connections;return{release(){calls.push(`release:${number}`);},async query(query){const text=typeof query==='string'?query:query.text;calls.push(text);if(text==='COMMIT'&&number===1&&code){const error=Error('synthetic');error.code=code;throw error;}return{rows:[{id:'row'}],fields:[],rowCount:1};}};}};}
test('postgres: SQL batch uses one serializable client and retries only an acknowledged serialization abort',async()=>{
  const pool=fake('40001'),db=new PostgresDatabase(pool);const rows=await db.batch([db.prepare('INSERT INTO test(id) VALUES (?)').bind('safe')]);
  assert.equal(rows[0].meta.changes,1);assert.equal(pool.connections,2);assert.equal(pool.calls.filter(value=>value==='BEGIN ISOLATION LEVEL SERIALIZABLE').length,2);assert.equal(pool.calls.filter(value=>value==='ROLLBACK').length,1);
});
for(const code of ['ECONNRESET','23505'])test(`postgres: ${code} never retries an uncertain or conflicting batch`,async()=>{const pool=fake(code),db=new PostgresDatabase(pool);await assert.rejects(db.batch([db.prepare('UPDATE test SET value=?').bind(1)]));assert.equal(pool.connections,1);assert.ok(pool.calls.includes('ROLLBACK'));});
test('postgres: foreign adapter statements and unbound object values are rejected before execution',async()=>{const first=new PostgresDatabase(fake()),second=new PostgresDatabase(fake());await assert.rejects(first.batch([second.prepare('DELETE FROM test')]));assert.throws(()=>first.prepare('SELECT ?').bind({injected:true}));});
