// Separate-process state contender used by the independent SQLite reviews.
import { ReviewD1 } from './review-d1.mjs';
import { pathToFileURL } from 'node:url';
const [filename, bundle, owner, operationId, action='approve'] = process.argv.slice(2);
const targetStatus=action==='cancel'?'CANCELLED':'APPROVED';
const isTarget=sql=>sql.includes(`UPDATE proofpay_operations SET status = '${targetStatus}'`);
const { ProofPayService } = await import(pathToFileURL(bundle));
const db = new ReviewD1(filename);
let paused = false;
async function pauseAtReservation() {
  if(paused)return;
  paused=true;
  await new Promise(resolve => { process.once('message', resolve); process.send({ready:true}); });
}
const batch = db.batch.bind(db);
db.batch = async statements => {
  if(statements.some(statement=>isTarget(statement.sql)))await pauseAtReservation();
  return batch(statements);
};
const original = db.prepare.bind(db);
db.prepare = sql => {
  const statement = original(sql);
  const bind = statement.bind.bind(statement);
  statement.bind = (...params) => {
    const bound = bind(...params);
    if (isTarget(sql)) {
      const first = bound.first.bind(bound);
      bound.first = async (...args) => {
        await pauseAtReservation();
        return first(...args);
      };
    }
    return bound;
  };
  return statement;
};
try {
  const service=new ProofPayService({db,env:{}});
  if(action==='cancel')await service.cancelBeforeDispatch(owner,operationId,1);
  else await service.approve(owner, operationId, 1);
  process.send({ok:true});
} catch (error) { process.send({ok:false,code:error.code,message:error.message}); }
finally { db.close(); process.disconnect(); }
