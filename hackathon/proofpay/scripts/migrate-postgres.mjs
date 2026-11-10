import {Pool} from 'pg';
import {createHash} from 'node:crypto';
import {readdir,readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

// Never let a parser, driver, rollback or cleanup error print a connection URL.
// Error messages/cause/input/code may all contain provider-controlled material.
let pool,client,inTransaction=false;
let phase='configuration',failure;
const failures={configuration:'MIGRATION_CONFIGURATION_INVALID',connection:'MIGRATION_CONNECTION_FAILED',transaction:'MIGRATION_TRANSACTION_FAILED',cleanup:'MIGRATION_CLEANUP_FAILED'};
try {
  const url=new URL(process.env.DATABASE_URL_UNPOOLED??process.env.POSTGRES_URL_NON_POOLING??process.env.DATABASE_URL??process.env.POSTGRES_URL??'');
  if(!['postgres:','postgresql:'].includes(url.protocol)||!url.hostname||!url.username||!url.password||url.pathname==='/'||url.hash)throw Error('Invalid configuration');
  for(const name of ['sslmode','sslcert','sslkey','sslrootcert','sslnegotiation'])url.searchParams.delete(name);
  phase='connection';
  pool=new Pool({connectionString:url.toString(),ssl:{rejectUnauthorized:true},max:1,connectionTimeoutMillis:15000,application_name:'proofpay-migrate'});
  pool.on('error',()=>{});
  client=await pool.connect();
  phase='transaction';
  await client.query('BEGIN');inTransaction=true;
  await client.query('SELECT pg_advisory_xact_lock(729105240182::bigint)');
  await client.query('CREATE TABLE IF NOT EXISTS proofpay_migrations (name TEXT PRIMARY KEY, sha256 TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())');
  const directory=new URL('../db/postgres/',import.meta.url);
  for(const name of (await readdir(fileURLToPath(directory))).filter(name=>/^\d{4}_[a-z0-9_]+\.sql$/.test(name)).sort()){
    const sql=await readFile(new URL(name,directory),'utf8');const hash=createHash('sha256').update(sql).digest('hex');
    const prior=await client.query('SELECT sha256 FROM proofpay_migrations WHERE name=$1',[name]);
    if(prior.rows.length){if(prior.rows[0].sha256!==hash)throw Error('Migration checksum mismatch');continue;}
    await client.query(sql);await client.query('INSERT INTO proofpay_migrations(name,sha256) VALUES($1,$2)',[name,hash]);
    process.stdout.write(`Prepared migration ${name}\n`);
  }
  await client.query('COMMIT');inTransaction=false;
} catch {
  failure=failures[phase]??'MIGRATION_TRANSACTION_FAILED';
  if(client&&inTransaction){try{await client.query('ROLLBACK');}catch{/* Preserve the bounded original failure; outcome may be uncertain. */}}
} finally {
  if(client){try{client.release();}catch{failure??=failures.cleanup;}}
  if(pool){try{await pool.end();}catch{failure??=failures.cleanup;}}
}
if(failure){process.stderr.write(`${failure}\n`);process.exitCode=1;}
else process.stdout.write('PostgreSQL migrations committed.\n');
