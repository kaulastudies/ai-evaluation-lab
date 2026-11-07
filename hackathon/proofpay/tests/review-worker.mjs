// Separate-process approval contender used by review-service.mjs.
import { ReviewD1 } from './review-d1.mjs';
import { pathToFileURL } from 'node:url';
const [filename, bundle, owner, operationId] = process.argv.slice(2);
const { ProofPayService } = await import(pathToFileURL(bundle));
const db = new ReviewD1(filename);
const original = db.prepare.bind(db);
db.prepare = sql => {
  const statement = original(sql);
  const bind = statement.bind.bind(statement);
  statement.bind = (...params) => {
    const bound = bind(...params);
    if (/UPDATE proofpay_operations SET status = 'APPROVED'/.test(sql)) {
      const first = bound.first.bind(bound);
      bound.first = async (...args) => {
        await new Promise(resolve => { process.once('message', resolve); process.send({ready:true}); });
        return first(...args);
      };
    }
    return bound;
  };
  return statement;
};
try {
  await new ProofPayService({db,env:{}}).approve(owner, operationId, 1);
  process.send({ok:true});
} catch (error) { process.send({ok:false,code:error.code,message:error.message}); }
finally { db.close(); process.disconnect(); }
