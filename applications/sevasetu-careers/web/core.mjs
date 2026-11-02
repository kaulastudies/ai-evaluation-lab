/* Shared browser/CLI logic. No external requests, storage, or model calls here. */
export const VERSION = '0.1.0';
export const POLICY = { maxAgeDays: 7, maxJobs: 2000, maxFacts: 60 };
const DAY = 86400000;
const LEVELS = ['not_stated', '10', '10+2', 'diploma', 'graduate', 'postgraduate'];
const STOP = new Set('the and for with from that this have your will are was into role work job experience'.split(' '));
const ALIASES = {
  'stores': 'inventory', 'warehouse': 'inventory',
  'store keeping': 'inventory', 'storekeeping': 'inventory', 'stock control': 'inventory',
  'stores management': 'inventory', 'warehouse management': 'inventory',
  'ms excel': 'excel', 'microsoft excel': 'excel', 'spreadsheets': 'excel',
  'help desk': 'it support', 'helpdesk': 'it support',
  'network administration': 'networking', 'computer networking': 'networking',
  'fleet management': 'fleet operations', 'वाहन प्रबंधन': 'fleet operations',
  'भंडार प्रबंधन': 'inventory', 'कंप्यूटर सहायता': 'it support',
};
export function text(value, max = 5000) {
  if (typeof value !== 'string') return '';
  return value.replace(/<[^>]*>/g, ' ').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '')
    .replace(/\s+/g, ' ').trim().slice(0, max);
}
export function skill(value) {
  const s = text(value, 100).toLowerCase();
  return ALIASES[s] || s;
}
export function tokens(value) {
  let s = text(value).toLowerCase();
  for (const [a, b] of Object.entries(ALIASES)) s = s.replaceAll(a, b);
  return (s.match(/[\p{L}\p{N}+#]+/gu) || []).filter(t => t.length > 1 && !STOP.has(t));
}
export function dateMillis(value, endOfDay = false) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2}))?$/.test(value)) return NaN;
  const day = value.slice(0, 10);
  const check = new Date(`${day}T00:00:00Z`);
  if (!Number.isFinite(+check) || check.toISOString().slice(0, 10) !== day) return NaN;
  // Date-only vacancy cutoffs are inclusive through the end of the day in India.
  return Date.parse(value.length === 10 ? `${value}T${endOfDay ? '23:59:59.999' : '00:00:00'}+05:30` : value);
}
export function canonicalURL(value) {
  const u = new URL(value);
  if (u.protocol !== 'https:' || u.username || u.password) throw new Error('A public HTTPS source URL is required');
  u.hash = '';
  for (const k of [...u.searchParams.keys()]) if (/^(utm_|fbclid|gclid)/i.test(k)) u.searchParams.delete(k);
  u.searchParams.sort();
  return u.href;
}
function numberOrNull(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100 ? value : null;
}
export function normalizeJob(raw, source = {}, observedAt = new Date().toISOString()) {
  if (!raw || typeof raw !== 'object') throw new Error('Job must be an object');
  const title = text(raw.title, 240), employer = text(raw.employer, 240);
  if (!title || !employer) throw new Error('Job title and employer are required');
  const url = canonicalURL(raw.url);
  const sourceURL = canonicalURL(source.url || raw.source_url || url);
  const checked = raw.observed_at || source.observed_at || observedAt;
  const posted = raw.posted_at || null, until = raw.valid_until || null;
  for (const [field, val] of [['observed_at', checked], ['posted_at', posted], ['valid_until', until]]) {
    if (val !== null && !Number.isFinite(dateMillis(val))) throw new Error(`Invalid or ambiguous ${field}`);
  }
  if (posted && until && dateMillis(until, true) < dateMillis(posted)) throw new Error('Deadline precedes posting');
  const req = raw.requirements || {};
  if (req.education && !LEVELS.includes(req.education)) throw new Error('Unknown education requirement');
  if (req.min_years != null && numberOrNull(req.min_years) === null) throw new Error('Invalid minimum experience');
  for (const [name, value] of [['skills', raw.skills], ['required skills', req.skills], ['certificates', req.certificates]]) {
    if (value !== undefined && (!Array.isArray(value) || value.length > 80 || value.some(x => typeof x !== 'string'))) throw new Error(`Invalid ${name}`);
  }
  const sample = source.synthetic === true || raw.synthetic === true;
  const id = text(raw.id, 120) || url;
  const provenance = [];
  if (raw.provenance !== undefined) {
    if (!Array.isArray(raw.provenance) || raw.provenance.length > 40) throw new Error('Invalid provenance observations');
    for (const observation of raw.provenance) {
      if (!observation || !Number.isFinite(dateMillis(observation.observed_at))) throw new Error('Invalid provenance date');
      provenance.push({ source: text(observation.source, 160), url: canonicalURL(observation.url),
        observed_at: observation.observed_at, synthetic: observation.synthetic === true });
    }
  }
  const observation = { source: text(source.name || raw.source || 'Imported source', 160), url: sourceURL, observed_at: checked, synthetic: sample };
  if (!provenance.some(p => JSON.stringify(p) === JSON.stringify(observation))) provenance.push(observation);
  return {
    id, title, employer, url, location: text(raw.location || 'Not specified', 160),
    remote: raw.remote === true, domain: text(raw.domain || 'general', 80),
    description: text(raw.description), skills: [...new Set((raw.skills || []).map(skill))],
    esm: typeof raw.esm === 'boolean' ? raw.esm : null,
    salary: text(raw.salary || 'Not stated', 160), posted_at: posted, valid_until: until,
    requirements: { education: req.education || 'not_stated', min_years: numberOrNull(req.min_years),
      skills: (req.skills || []).map(skill), certificates: (req.certificates || []).map(skill), review_required: req.review_required !== false },
    source_status: ['closed', 'withdrawn'].includes(raw.source_status || raw.status) ? raw.source_status || raw.status : null,
    deadline_conflict: raw.deadline_conflict === true, requirements_conflict: raw.requirements_conflict === true,
    synthetic: sample || provenance.some(p => p.synthetic), provenance,
    observed_at: checked,
  };
}
export function lifecycle(job, asOf = new Date().toISOString()) {
  const now = dateMillis(asOf), checked = dateMillis(job.observed_at);
  if (!Number.isFinite(now)) throw new Error('Invalid assessment date');
  if (job.source_status) return { state: 'expired', reason: 'Source marks this listing closed or withdrawn' };
  if (job.deadline_conflict) return { state: 'review', reason: 'Sources disagree about the deadline' };
  if (job.requirements_conflict) return { state: 'review', reason: 'Sources disagree about the requirements' };
  if (checked > now + 300000 || (job.posted_at && dateMillis(job.posted_at) > now)) return { state: 'review', reason: 'A source date is in the future' };
  if (job.valid_until && dateMillis(job.valid_until, true) < now) return { state: 'expired', reason: 'Application deadline has passed' };
  if (now - checked > POLICY.maxAgeDays * DAY) return { state: 'stale', reason: 'Source has not been checked within 7 days' };
  if (!job.valid_until) return { state: 'review', reason: 'No application deadline supplied' };
  return { state: 'open', reason: 'Listed deadline has not passed; confirm on the source' };
}
export function deduplicate(jobs) {
  const output = [], byURL = new Map(), byRole = new Map();
  for (const job of jobs) {
    const role = [job.title, job.employer, job.location].map(x => text(x).toLowerCase()).join('|');
    const prior = byURL.get(job.url) || byRole.get(role);
    if (!prior) { output.push(job); byURL.set(job.url, job); byRole.set(role, job); continue; }
    const oldSources = prior.provenance;
    const conflict = prior.deadline_conflict || prior.valid_until !== job.valid_until;
    const requirementConflict = prior.requirements_conflict || JSON.stringify(prior.requirements) !== JSON.stringify(job.requirements);
    const sourceClosed = prior.source_status || job.source_status;
    if (dateMillis(job.observed_at) > dateMillis(prior.observed_at)) Object.assign(prior, job);
    prior.provenance = [...oldSources, ...job.provenance].filter((x, i, a) => a.findIndex(y => JSON.stringify(y) === JSON.stringify(x)) === i);
    prior.deadline_conflict = conflict;
    prior.requirements_conflict = requirementConflict;
    prior.source_status = sourceClosed;
    // A synthetic observation never becomes a real job through deduplication.
    prior.synthetic = prior.provenance.some(p => p.synthetic);
    byURL.set(job.url, prior); byRole.set(role, prior);
  }
  return output;
}
export function prepareFeed(bundle) {
  if (!bundle || !Array.isArray(bundle.jobs) || bundle.jobs.length > POLICY.maxJobs) throw new Error('Feed must contain at most 2000 jobs');
  const normalized = [], rejected = [];
  bundle.jobs.forEach((raw, index) => {
    try { normalized.push(normalizeJob(raw, bundle.source || {}, bundle.observed_at)); }
    catch (err) { rejected.push({ index, reason: err.message }); }
  });
  return { jobs: deduplicate(normalized), rejected, input_count: bundle.jobs.length };
}
export function validateProfile(p) {
  if (!p || typeof p !== 'object' || !text(p.name, 160)) throw new Error('Enter a candidate name');
  if (!Array.isArray(p.facts) || p.facts.length === 0 || p.facts.length > POLICY.maxFacts) throw new Error('Supply 1–60 candidate facts');
  const ids = new Set();
  const facts = p.facts.map(f => {
    if (!f || !/^[a-zA-Z0-9_-]{1,60}$/.test(f.id) || ids.has(f.id) || !text(f.text)) throw new Error('Every fact needs a unique ID and text');
    if (!['experience', 'education', 'certificate', 'achievement'].includes(f.kind)) throw new Error('Invalid fact kind');
    if (f.skills && (!Array.isArray(f.skills) || f.skills.some(s => typeof s !== 'string'))) throw new Error('Invalid fact skills');
    ids.add(f.id);
    return { id: f.id, text: text(f.text, 1200), kind: f.kind, skills: (f.skills || []).map(skill),
      level: LEVELS.includes(f.level) ? f.level : null,
      certificate: typeof f.certificate === 'string' ? skill(f.certificate) : null,
      years: numberOrNull(f.years) };
  });
  return { name: text(p.name, 160), location: text(p.location, 160), contact: text(p.contact, 180),
    esm: p.esm === true, facts, synthetic: p.synthetic === true };
}
function tfidf(documents, query) {
  const docs = documents.map(tokens), q = tokens(query), N = docs.length;
  const df = new Map();
  for (const d of docs) for (const t of new Set(d)) df.set(t, (df.get(t) || 0) + 1);
  const vector = ts => {
    const v = new Map();
    for (const t of ts) v.set(t, (v.get(t) || 0) + 1);
    for (const [t, n] of v) v.set(t, (1 + Math.log(n)) * (1 + Math.log((N + 1) / ((df.get(t) || 0) + 1))));
    return v;
  };
  const qv = vector(q), norm = v => Math.sqrt([...v.values()].reduce((a, x) => a + x * x, 0));
  const qn = norm(qv);
  return docs.map(d => { const v = vector(d), vn = norm(v); return qn && vn ? [...qv].reduce((a, [t, w]) => a + w * (v.get(t) || 0), 0) / (qn * vn) : 0; });
}
export function assess(job, profile) {
  const p = validateProfile(profile);
  const candidateSkills = new Set(p.facts.flatMap(f => f.skills));
  const matched = job.skills.filter(s => candidateSkills.has(s));
  const missing = [], unknown = [];
  const levels = p.facts.filter(f => f.kind === 'education' && f.level).map(f => f.level);
  const allowed = { '10': ['10','10+2','graduate','postgraduate'], '10+2': ['10+2','graduate','postgraduate'], diploma: ['diploma'], graduate: ['graduate','postgraduate'], postgraduate: ['postgraduate'] };
  if (job.requirements.education !== 'not_stated') {
    if (!levels.length) unknown.push('Education evidence not supplied');
    else if (!levels.some(l => allowed[job.requirements.education].includes(l))) missing.push(`Education: ${job.requirements.education}`);
  }
  // Do not add years from overlapping roles. A single fact must support the required duration.
  const years = p.facts.filter(f => f.kind === 'experience' && f.years !== null).map(f => f.years);
  if (job.requirements.min_years !== null) {
    if (!years.length) unknown.push('Experience duration not supplied');
    else if (Math.max(...years) < job.requirements.min_years) missing.push(`Experience: ${job.requirements.min_years} years`);
  }
  const certs = new Set(p.facts.filter(f => f.kind === 'certificate').map(f => f.certificate));
  for (const c of job.requirements.certificates) if (!certs.has(c)) missing.push(`Certificate not supplied: ${c}`);
  for (const s of job.requirements.skills || []) if (!candidateSkills.has(s)) missing.push(`Required skill not supplied: ${s}`);
  if (job.esm === true && !p.esm) unknown.push('Ex-serviceman status must be confirmed');
  if (job.requirements.review_required) unknown.push('Full advertisement needs a manual eligibility check');
  return { matched_skills: matched, missing_skills: job.skills.filter(s => !candidateSkills.has(s)), missing, unknown,
    status: missing.length ? 'requirements_gap' : unknown.length ? 'needs_review' : 'possible_match' };
}
export function searchJobs(jobs, profile, options = {}) {
  const p = validateProfile(profile), query = text(options.query || '', 500);
  const queryTokens = tokens(query);
  const eligible = jobs.filter(j => {
    const state = lifecycle(j, options.asOf).state;
    const jobTokens = new Set(tokens(`${j.title} ${j.description} ${j.skills.join(' ')} ${j.employer}`));
    return (state === 'open' || options.includeReview && state === 'review') && (!queryTokens.length || queryTokens.some(t => jobTokens.has(t))) &&
      (!options.esmOnly || j.esm === true) && (!options.domain || j.domain === options.domain) &&
      (!options.location || j.remote || j.location.toLowerCase().includes(options.location.toLowerCase()));
  });
  const descriptions = eligible.map(j => `${j.title} ${j.description} ${j.skills.join(' ')}`);
  const similarities = tfidf(descriptions, query || p.facts.flatMap(f => f.skills).join(' '));
  return eligible.map((job, i) => {
    const assessment = assess(job, p);
    const coverage = job.skills.length ? assessment.matched_skills.length / job.skills.length : 0;
    const local = job.remote || job.location.toLowerCase().includes(p.location.toLowerCase());
    let score = Math.round((query ? 35 : 60) * coverage + (query ? 55 : 30) * similarities[i] + (local && p.location ? 10 : 0));
    if (assessment.missing.length) score = Math.min(score, 39);
    return { job, ...assessment, score, lifecycle: lifecycle(job, options.asOf),
      explanation: `${assessment.matched_skills.length}/${job.skills.length} listed skills supported by candidate facts; relevance score is not a hiring probability.` };
  }).sort((a, b) => b.score - a.score || a.job.id.localeCompare(b.job.id));
}
export function selectFacts(profile, job) {
  const p = validateProfile(profile);
  return [...p.facts].sort((a, b) => {
    const n = f => f.skills.filter(s => job.skills.includes(s)).length;
    return n(b) - n(a) || p.facts.indexOf(a) - p.facts.indexOf(b);
  }).map(f => f.id);
}
export function validateSelection(value, profile) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.keys(value).some(k => k !== 'fact_ids') || !Array.isArray(value.fact_ids) || !value.fact_ids.length) throw new Error('Model must return only a non-empty fact_ids array');
  const p = validateProfile(profile), ids = new Set(p.facts.map(f => f.id));
  if (value.fact_ids.some(id => typeof id !== 'string' || !ids.has(id)) || new Set(value.fact_ids).size !== value.fact_ids.length) throw new Error('Model selected an unsupported or duplicate fact');
  // Qualifications cannot be silently dropped to hide a requirement gap.
  for (const f of p.facts.filter(f => ['education', 'certificate'].includes(f.kind))) {
    if (!value.fact_ids.includes(f.id)) throw new Error('Model omitted an education or certificate fact');
  }
  return value.fact_ids;
}
export function buildCV(profile, job, selectedIDs = null) {
  const p = validateProfile(profile);
  const ids = validateSelection({ fact_ids: selectedIDs || selectFacts(p, job) }, p);
  const facts = ids.map(id => p.facts.find(f => f.id === id));
  const lines = [p.name, [p.location, p.contact].filter(Boolean).join(' | '), '', `Application for: ${job.title}`];
  for (const [kind, heading] of [['experience', 'EXPERIENCE'], ['education', 'EDUCATION'], ['certificate', 'CERTIFICATES AND TRAINING'], ['achievement', 'ACHIEVEMENTS']]) {
    const section = facts.filter(f => f.kind === kind);
    if (section.length) { lines.push('', heading); for (const f of section) lines.push(`- ${f.text}`); }
  }
  const assessment = assess(job, p);
  return { text: lines.join('\n'), profile: p,
    receipt: { version: VERSION, method: 'verbatim_candidate_facts', job_id: job.id, job_url: job.url,
      disclaimer: 'Candidate-supplied facts; no independent credential verification. Employer determines eligibility.',
      synthetic: p.synthetic || job.synthetic, selected_fact_ids: ids,
      claims: facts.map(({ id, text, kind }) => ({ fact_id: id, text, kind })),
      eligibility_check: assessment, source_provenance: job.provenance } };
}
export async function sha256(value) {
  const bytes = new TextEncoder().encode(typeof value === 'string' ? value : JSON.stringify(value));
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(b => b.toString(16).padStart(2, '0')).join('');
}
export async function withReceipt(cv) {
  return { ...cv, receipt: { ...cv.receipt, cv_sha256: await sha256(cv.text), profile_sha256: await sha256(cv.profile) } };
}
export const escapeHTML = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
