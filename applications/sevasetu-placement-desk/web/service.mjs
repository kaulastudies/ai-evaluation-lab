import { DeskError, actorFor, validID, permit, projectRecord, compareRole, buildVerifiedCV, qualificationInput, digest, clean } from './domain.mjs';

export class FixtureService {
  constructor(data, options={}) {
    this.data=options.shared?data:structuredClone(data); this.actor=options.actor||actorFor('counsellor'); this.ledger=options.ledger||[];this.auditState=options.auditState||{queue:Promise.resolve()};
    for(const r of this.data.records) if(!validID(r.id) || new Set(r.qualifications.map(q=>q.id)).size!==r.qualifications.length) throw new DeskError('Invalid sample register');
  }
  async setRole(role) { this.actor=actorFor(role); return this.actor; }
  async catalog() { return { reference_date:this.data.reference_date, roles:this.data.roles, sample_ids:this.data.records.filter(r=>this.actor.role!=='candidate'||r.id===this.actor.candidate_id).map(r=>({id:r.id,name:r.name})), submission_example:this.data.submission_example, actor:this.actor }; }
  find(id) {
    if(!validID(id)) throw new DeskError('Use a sample ID such as ESM-DEMO-1001');
    const r=this.data.records.find(r=>r.id===id); if(!r)throw new DeskError('Sample record unavailable',404); return r;
  }
  async authorise(id,purpose,action) {
    try { const record=this.find(id);permit(record,this.actor,purpose);return record; }
    catch(e){await this.audit(action,validID(id)?id:'invalid-id',purpose,'denied');throw e;}
  }
  async audit(action,id,purpose,result) {
    const actor={...this.actor};
    const task=this.auditState.queue.then(async()=>{
      const event={ sequence:this.ledger.length+1, actor:actor.id, role:actor.role, candidate_id:id, action,purpose,result, previous:this.ledger.at(-1)?.hash||'0'.repeat(64) };
      event.hash=await digest(event); this.ledger.push(event);
    });
    this.auditState.queue=task.catch(()=>{});await task;
  }
  async lookup(id,purpose='placement_review',cutoff=this.data.reference_date) {
    try { const view=projectRecord(this.find(id),this.actor,purpose,cutoff,this.data.reference_date); await this.audit('lookup',id,purpose,'allowed'); return view; }
    catch(e){await this.audit('lookup',validID(id)?id:'invalid-id',purpose,'denied');throw e;}
  }
  async assess(id,roleID,purpose='placement_review') {
    const r=await this.authorise(id,purpose,'compare');
    const role=this.data.roles.find(j=>j.id===roleID); if(!role)throw new DeskError('Sample role unavailable',404);
    const result=compareRole(r,role,this.data.reference_date); await this.audit('compare',id,purpose,result.state);return result;
  }
  async submit(id,input,purpose='placement_review') {
    const r=await this.authorise(id,purpose,'submit_qualification');
    const q=qualificationInput(input);
    if(r.qualifications.some(x=>x.id===q.id||x.serial===q.serial))throw new DeskError('This qualification reference is already in the record; check its existing review status');
    r.qualifications.push(q);await this.audit('submit_qualification',id,purpose,'pending');return {id:q.id,status:q.status};
  }
  async verify(id,qualificationID,purpose='record_verification') {
    const r=await this.authorise(id,purpose,'verify_qualification');
    if(this.actor.role!=='verifier'||purpose!=='record_verification'){await this.audit('verify_qualification',id,purpose,'denied');throw new DeskError('A records-verifier session and verification purpose are required',403);}
    const q=r.qualifications.find(q=>q.id===qualificationID);if(!q)throw new DeskError('Qualification not found',404);
    const issuer=this.data.issuer_registry.find(x=>x.serial===q.serial);
    const identityMatch=issuer?.candidate_id===r.id;
    const payloadMatch=issuer?.document_sha256===q.document_sha256&&issuer?.issuer===q.issuer&&issuer?.title===q.title&&issuer?.code===q.code&&issuer?.awarded_on===q.awarded_on&&issuer?.expires_on===q.expires_on&&issuer?.kind===q.kind&&(q.kind!=='education'||issuer?.level===q.level);
    if(issuer?.revoked){q.status='revoked';q.verification=null;}
    else if(issuer&&(!identityMatch||!payloadMatch)){q.status='conflicting';q.verification=null;}
    else if(!issuer){q.status='pending';q.verification=null;}
    else {q.status='verified';q.verification={reference:'SAMPLE-ISSUER-CHECK:'+issuer.serial,authority:issuer.issuer,reviewer:this.actor.id,checked_on:this.data.reference_date};}
    await this.audit('verify_qualification',id,purpose,q.status);
    return {id:q.id,status:q.status,explanation:q.status==='verified'?'Matched the fictional issuer register, candidate ID and document fingerprint. No real issuer was contacted.':q.status==='conflicting'?'Candidate identity, document fingerprint or qualification metadata does not match the sample issuer record.':'A valid issuer confirmation is not available; do not credit this claim as verified.'};
  }
  async cv(id,roleID,purpose='placement_review') {
    const r=await this.authorise(id,purpose,'prepare_cv');const role=this.data.roles.find(j=>j.id===roleID);if(!role)throw new DeskError('Sample role unavailable',404);
    const result=buildVerifiedCV(projectRecord(r,this.actor,purpose,role.cutoff,this.data.reference_date),role);
    result.receipt.cv_sha256=await digest(result.text);await this.audit('prepare_cv',id,purpose,'draft');return result;
  }
  async history(id,purpose='placement_review') {permit(this.find(id),this.actor,purpose);return this.ledger.filter(e=>e.candidate_id===id);}
}
export class APIGateway {
  async request(route, body) {
    const r=await fetch('./api/'+route,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),credentials:'same-origin'});
    const data=await r.json();if(!r.ok)throw new DeskError(data.error||'Request failed',r.status);return data;
  }
  setRole(role){return this.request('session',{role});}
  catalog(){return this.request('catalog');}
  lookup(id,purpose,cutoff){return this.request('lookup',{id,purpose,cutoff});}
  assess(id,roleID,purpose){return this.request('assess',{id,roleID,purpose});}
  submit(id,input,purpose){return this.request('submit',{id,input,purpose});}
  verify(id,qualificationID,purpose){return this.request('verify',{id,qualificationID,purpose});}
  cv(id,roleID,purpose){return this.request('cv',{id,roleID,purpose});}
  history(id,purpose){return this.request('history',{id,purpose});}
}
export async function connect() {
  const r=await fetch('./deployment.json');if(!r.ok)throw new DeskError('Start the local server or use the published sample demo');
  const manifest=await r.json();
  if(manifest.mode==='local_fixture_api')return {service:new APIGateway(),mode:manifest.mode};
  if(manifest.mode!=='static_fixture_demo')throw new DeskError('Unsupported demonstration mode');
  const data=await(await fetch('./sample-data.json')).json();return {service:new FixtureService(data),mode:manifest.mode};
}
