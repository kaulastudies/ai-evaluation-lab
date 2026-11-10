import {pathToFileURL} from 'node:url';
import {ReviewD1} from './review-d1.mjs';
const [filename,bundle,owner,configJSON]=process.argv.slice(2);
const {ProofPayService}=await import(pathToFileURL(bundle));
const db=new ReviewD1(filename);let calls=0;
const service=new ProofPayService({db,env:JSON.parse(configJSON),ai:async()=>{calls++;return{sku:'workflow-review',rationale:'Synthetic concurrent funding test.',source:'model'};}});
process.on('message',async message=>{
  if(message!=='go')return;
  try{await service.propose(owner,{mode:'sandbox',request:'Workflow review',idempotencyKey:'parallel-funding-test'});process.send({ok:true,calls});}
  catch(error){process.send({ok:false,calls,code:error.code??'UNEXPECTED'});}
  finally{db.close();process.disconnect();}
});
process.send({ready:true});
