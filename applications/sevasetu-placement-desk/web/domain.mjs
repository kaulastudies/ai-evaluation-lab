export const VERSION = '0.1.0';
export const DAY = 86400000;
export class DeskError extends Error { constructor(message, status = 400) { super(message); this.status = status; } }
export const clean = (value, max = 500) => typeof value === 'string' ? value.replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max) : '';
export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
export function day(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return NaN;
  const n = Date.parse(value + 'T00:00:00Z');
  return Number.isFinite(n) && new Date(n).toISOString().slice(0, 10) === value ? n : NaN;
}
export function ageAt(dob, cutoff) {
  if (!Number.isFinite(day(dob)) || !Number.isFinite(day(cutoff)) || day(dob) > day(cutoff)) return null;
  const [y,m,d] = dob.split('-').map(Number), [cy,cm,cd] = cutoff.split('-').map(Number);
  return cy - y - (cm < m || cm === m && cd < d ? 1 : 0);
}
export function duration(start, end) {
  if (!Number.isFinite(day(start)) || !Number.isFinite(day(end)) || day(start) > day(end)) return null;
  const [y,m,d] = start.split('-').map(Number), [ey,em,ed] = end.split('-').map(Number);
  const months = (ey-y)*12 + em-m - (ed < d ? 1 : 0);
  return { years: Math.floor(months/12), months: months%12, complete_years: Math.floor(months/12) };
}
export function validID(id) { return /^ESM-DEMO-\d{4}$/.test(id); }
export function actorFor(role) {
  const actors = {
    counsellor: { id:'operator-demo-01', role:'counsellor', label:'Placement counsellor (sample)' },
    verifier: { id:'verifier-demo-01', role:'verifier', label:'Records verifier (sample)' },
    candidate: { id:'candidate-demo-1001', role:'candidate', candidate_id:'ESM-DEMO-1001', label:'Candidate: ESM-DEMO-1001 (sample)' },
  };
  if (!actors[role]) throw new DeskError('Choose a supported demonstration role');
  return { ...actors[role] };
}
export function permit(record, actor, purpose) {
  if (!actor?.id || !['counsellor','verifier','candidate'].includes(actor.role)) throw new DeskError('A sample session is required', 401);
  if (actor.role === 'candidate' && actor.candidate_id !== record.id) throw new DeskError('This sample session can access only its own record', 403);
  if (!['placement_review','record_verification','pay_reference'].includes(purpose)) throw new DeskError('Choose a documented access purpose');
  if (actor.role !== 'candidate' && !record.consent.placement) throw new DeskError('Placement access is not enabled for this record', 403);
  if (purpose !== 'placement_review' && actor.role !== 'verifier' && actor.role !== 'candidate') throw new DeskError('This role does not have that access purpose', 403);
}
export function qualificationState(q, cutoff, asOf=cutoff) {
  if (q.status === 'revoked') return 'revoked';
  if (q.status === 'conflicting') return 'conflicting';
  if (q.expires_on && (!Number.isFinite(day(q.expires_on)) || day(q.expires_on) < day(cutoff))) return Number.isFinite(day(q.expires_on)) ? 'expired' : 'needs_review';
  if (!Number.isFinite(day(q.awarded_on)) || day(q.awarded_on) > Math.min(day(cutoff),day(asOf))) return 'needs_review';
  return q.status === 'verified' && q.verification?.reference && q.verification?.authority ? 'verified' : 'pending';
}
export function projectRecord(record, actor, purpose, cutoff, asOf=cutoff) {
  permit(record, actor, purpose);
  if (!Number.isFinite(day(cutoff))) throw new DeskError('Supply a valid assessment cutoff date');
  const own = actor.role === 'candidate';
  const canDOB = own || actor.role === 'verifier' && purpose !== 'placement_review';
  const canPay = (own || actor.role === 'verifier' && purpose === 'pay_reference') && record.consent.pay_reference;
  const verifiedDOB = record.dob.status === 'verified';
  const end=Math.min(day(record.service.end),day(cutoff),day(asOf));
  const view = {
    id: record.id, name: record.name, status: record.status, synthetic: true, cutoff, as_of:asOf,
    age_at_cutoff: verifiedDOB ? ageAt(record.dob.value, cutoff) : null,
    dob: canDOB ? record.dob.value : null,
    last_pay: canPay ? structuredClone(record.last_pay) : null,
    protected_fields: {
      dob: canDOB ? null : 'Withheld in placement view; verified age is used for stated rules',
      last_pay: canPay ? null : 'Withheld; pay-reference purpose and permission are required. Not used to assess job fit',
    },
    dob_verification: record.dob.status, dob_reference: record.dob.source_ref,
    service: { ...record.service, duration: Number.isFinite(end)?duration(record.service.start, new Date(end).toISOString().slice(0,10)):null },
    qualifications: record.qualifications.map(q => ({ ...structuredClone(q), assessed_status: qualificationState(q, cutoff,asOf), stage: day(q.awarded_on) > day(record.service.end) ? 'After service' : 'During/before service' })),
    competencies: structuredClone(record.competencies), snapshot: structuredClone(record.snapshot),
    consent: { placement: record.consent.placement, pay_reference: record.consent.pay_reference },
  };
  return view;
}
const EDUCATION = { '10':['10','10+2','graduate','postgraduate'], '10+2':['10+2','graduate','postgraduate'], diploma:['diploma'], graduate:['graduate','postgraduate'], postgraduate:['postgraduate'] };
export function compareRole(record, role, asOf) {
  const rows = [];
  const add = (code, state, message, evidence = []) => rows.push({ code, state, message, evidence });
  if (![asOf, role.deadline, role.cutoff].every(x => Number.isFinite(day(x)))) throw new DeskError('Invalid role assessment dates');
  if (day(asOf) > day(role.deadline) || role.closed === true) return { role_id:role.id, role_title:role.title, state:'not_open', cutoff:role.cutoff, rows:[{code:'deadline',state:'gap',message:'The application window has closed',evidence:[role.source_ref]}], disclaimer:'Record comparison only. The employer and authorised reviewer determine eligibility.' };
  const fresh = Number.isFinite(day(record.snapshot.checked_on)) && day(asOf) >= day(record.snapshot.checked_on) && day(asOf)-day(record.snapshot.checked_on) <= 30*DAY;
  add('source', fresh ? 'pass':'review', fresh ? 'Sample register snapshot is within the 30-day review interval' : 'Register snapshot needs refresh or date clarification', [record.snapshot.reference]);
  add('service_status', record.service.verification === 'verified' ? role.accepted_statuses.includes(record.status) ? 'pass':'gap' : 'review', `${record.status}; role accepts ${role.accepted_statuses.join(', ')}`, [record.service.source_ref]);
  if (role.max_age !== null || role.min_age !== null) {
    const age = record.dob.status === 'verified' ? ageAt(record.dob.value, role.cutoff) : null;
    const pass = age !== null && (role.max_age === null || age <= role.max_age) && (role.min_age === null || age >= role.min_age);
    add('age', age === null ? 'review' : pass ? 'pass':'gap', age === null ? 'Verified date of birth is needed to compare the stated age rule' : `${age} completed years at ${role.cutoff}; stated range ${role.min_age ?? 'any'}–${role.max_age ?? 'any'}`, [record.dob.source_ref]);
  }
  if (role.education) {
    const education = record.qualifications.filter(q => q.kind === 'education');
    const matches = education.filter(q => (EDUCATION[role.education] || []).includes(q.level));
    const verified = matches.find(q => qualificationState(q, role.cutoff,asOf) === 'verified');
    const pending = matches.some(q => ['pending','needs_review','conflicting'].includes(qualificationState(q, role.cutoff,asOf)));
    add('education', verified ? 'pass' : pending ? 'review':'gap', verified ? `Required ${role.education}: supported by ${verified.title}` : pending ? `Required ${role.education}: matching claim needs verification` : `Required ${role.education}: not evidenced by the current verified record; equivalence is not assumed`, verified ? [verified.verification.reference] : []);
  }
  for (const requirement of role.certificates || []) {
    const matches = record.qualifications.filter(q => q.code === requirement);
    const verified = matches.find(q => qualificationState(q, role.cutoff,asOf) === 'verified');
    const pending = matches.some(q => ['pending','needs_review','conflicting'].includes(qualificationState(q, role.cutoff,asOf)));
    add('certificate:'+requirement, verified ? 'pass' : pending ? 'review':'gap', verified ? `${verified.title}: verified and current at cutoff` : pending ? `${requirement}: certificate or issuer check pending` : `${requirement}: no current verified certificate in the record`, verified ? [verified.verification.reference] : matches.map(q => q.serial));
  }
  for (const requirement of role.experience || []) {
    const supported = record.competencies.find(c => c.skill === requirement.skill && c.status === 'verified' && Number.isFinite(c.years) && c.years >= requirement.min_years);
    const unknown = record.competencies.some(c => c.skill === requirement.skill && c.status !== 'verified');
    add('experience:'+requirement.skill, supported ? 'pass' : unknown ? 'review':'gap', supported ? `${requirement.skill}: ${supported.years} verified sample years against ${requirement.min_years} required` : `${requirement.skill}: ${requirement.min_years} years not evidenced by verified trade/role history; total service is not substituted`, supported ? [supported.source_ref] : []);
  }
  const state = rows.some(r => r.state === 'review') ? 'needs_review' : rows.some(r => r.state === 'gap') ? 'recorded_gap' : 'documented_checks_met';
  return { role_id:role.id, role_title:role.title, state, cutoff:role.cutoff, rows, disclaimer:'Record comparison only. No selection, rejection or application is made. Confirm the full advertisement and any applicable relaxation/equivalence with the authorised reviewer.' };
}
export function buildVerifiedCV(view, role) {
  const claims = [];
  if (view.service.verification === 'verified' && view.service.duration) claims.push({ id:'service:'+view.id, text:`Recorded completed calendar service: ${view.service.duration.years} years and ${view.service.duration.months} months (as of ${view.as_of}).`, reference:view.service.source_ref });
  for (const c of view.competencies.filter(c => c.status === 'verified')) claims.push({ id:'skill:'+c.skill, text:`${c.skill}: ${c.years} years recorded experience.`, reference:c.source_ref });
  for (const q of view.qualifications.filter(q => q.assessed_status === 'verified')) claims.push({ id:q.id, text:q.title, reference:q.verification.reference });
  const text = [view.name, 'Application for: '+role.title, '', 'EXPERIENCE AND VERIFIED SAMPLE QUALIFICATIONS', ...claims.map(c => '- '+c.text)].join('\n');
  return { text, receipt:{ version:VERSION, candidate_id:view.id, role_id:role.id, cutoff:view.cutoff, synthetic:true, claims, omitted_sensitive_fields:['date_of_birth','last_pay'], excluded_qualification_ids:view.qualifications.filter(q => q.assessed_status !== 'verified').map(q => q.id), note:'Verified means confirmed in the fictional sample register, not by the Army or a real issuer.' } };
}
export async function digest(value) {
  const data = new TextEncoder().encode(typeof value === 'string' ? value : JSON.stringify(value));
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))].map(x => x.toString(16).padStart(2,'0')).join('');
}
export function qualificationInput(input) {
  if (!input || !['certificate','education'].includes(input.kind) || !clean(input.title) || !clean(input.issuer) || !clean(input.serial)) throw new DeskError('Supply the qualification, issuer and certificate reference');
  if (!Number.isFinite(day(input.awarded_on)) || input.expires_on && (!Number.isFinite(day(input.expires_on)) || day(input.expires_on) < day(input.awarded_on))) throw new DeskError('Check the qualification dates');
  if (!/^[a-f0-9]{64}$/.test(input.document_sha256 || '')) throw new DeskError('A test document SHA-256 fingerprint is required');
  if (input.kind === 'education' && !EDUCATION[input.level]) throw new DeskError('Choose an explicit education level');
  if (!/[a-zA-Z0-9]/.test(clean(input.serial,60))) throw new DeskError('Use a certificate reference containing letters or numbers');
  return { id:'q-'+clean(input.serial,60).replace(/[^a-zA-Z0-9_-]/g,''), code:clean(input.code,80), kind:input.kind, title:clean(input.title,240), issuer:clean(input.issuer,160), serial:clean(input.serial,100), awarded_on:input.awarded_on, expires_on:input.expires_on || null, level:input.kind==='education'?input.level:null, document_sha256:input.document_sha256, status:'pending', verification:null };
}
