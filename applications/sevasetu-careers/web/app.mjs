import { prepareFeed, validateProfile, searchJobs, lifecycle, buildCV, withReceipt, escapeHTML as e, validateSelection } from './core.mjs';

const $ = s => document.querySelector(s);
let bundle, feed, samples, profile, matches = [], selectedURL = null, cv = null, imported = false;
let asOf, draftSynthetic = true;
const labels = { logistics: 'Logistics & stores', administration: 'Administration', it: 'IT support', facilities: 'Facilities', healthcare: 'Healthcare operations', general: 'General' };
const statusLabel = { requirements_gap: 'Requirement gap', needs_review: 'Needs review', possible_match: 'Potential fit · verify with employer' };
const fmt = value => value ? new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeZone: 'Asia/Kolkata' }).format(new Date(value)) : 'Not supplied';
function showView(name) {
  for (const node of document.querySelectorAll('.view')) node.classList.toggle('hidden', node.id !== `${name}-view`);
  for (const button of document.querySelectorAll('.nav')) {
    button.classList.toggle('active', button.dataset.view === name);
    if (button.dataset.view === name) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
  }
  if (name === 'profile') fillProfile();
}
function download(name, content, type = 'application/json') {
  const u = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement('a'); a.href = u; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(u), 1000);
}
function renderMetrics() {
  const counts = { open: 0, review: 0, expired: 0, stale: 0 };
  for (const job of feed.jobs) counts[lifecycle(job, asOf).state]++;
  const withheld = counts.expired + counts.stale;
  const values = [[feed.input_count, 'source records reviewed'], [counts.open, 'within listed deadlines'], [counts.review, 'need deadline review'], [withheld + feed.rejected.length + (feed.input_count - feed.jobs.length - feed.rejected.length), 'old, duplicate or invalid records']];
  $('#metrics').innerHTML = values.map(([n, label]) => `<div class="metric"><b>${n}</b><span>${label}</span></div>`).join('');
  $('#feed-status').textContent = `${imported ? 'Imported feed · checked' : 'Synthetic feed · frozen'} ${fmt(asOf)}`;
}
function renderCandidate() {
  $('#candidate-name').textContent = profile.name;
  $('#candidate-location').textContent = profile.location || 'Location not supplied';
  $('.avatar').textContent = profile.name.split(' ').slice(0, 2).map(x => x[0]).join('');
  const skills = [...new Set(profile.facts.flatMap(f => f.skills))].slice(0, 6);
  $('#candidate-skills').innerHTML = skills.map(s => `<span class="tag">${e(s)}</span>`).join('');
}
function renderSearch() {
  matches = searchJobs(feed.jobs, profile, { query: $('#query').value, domain: $('#domain').value,
    location: $('#location').value, esmOnly: $('#esm-only').checked, includeReview: $('#include-review').checked, asOf });
  if (!matches.some(m => m.job.url === selectedURL)) selectedURL = matches[0]?.job.url || null;
  $('#result-count').textContent = `${matches.length} ${imported ? '' : 'sample '}${matches.length === 1 ? 'role' : 'roles'} to review`;
  $('#results').innerHTML = matches.length ? matches.map(m => `<article class="job-card ${m.job.url === selectedURL ? 'selected' : ''}">
    <div class="job-top"><span class="domain">${e(labels[m.job.domain] || m.job.domain)}</span><span class="sample-pill">${m.job.synthetic ? 'SAMPLE VACANCY' : 'IMPORTED LISTING'}</span></div>
    <h3>${e(m.job.title)}</h3><p class="employer">${e(m.job.employer)}</p><p class="job-meta">${e(m.job.location)}${m.job.remote ? ' · Remote' : ''}</p>
    <div class="job-status"><span class="status ${m.status === 'possible_match' && m.lifecycle.state === 'open' ? '' : 'warning'}">${e(m.lifecycle.state === 'review' ? 'Deadline needs review' : statusLabel[m.status])}</span></div>
    <div class="match-row"><div class="match-score">${m.score}/100 <span>relevance</span></div><button class="view-role" data-url="${e(m.job.url)}" aria-label="View role: ${e(m.job.title)}">View role →</button></div></article>`).join('') : '<div class="empty"><h3>No roles meet these filters.</h3><p>Try another location or area of work. Missing-deadline listings appear only when you include the review queue.</p></div>';
  for (const b of document.querySelectorAll('.view-role')) b.addEventListener('click', () => { selectedURL = b.dataset.url; renderSearch(); $('#detail').scrollIntoView({ behavior: 'smooth', block: 'nearest' }); });
  renderDetail();
}
function list(items, fallback) { return items.length ? `<ul>${items.map(x => `<li>${e(x)}</li>`).join('')}</ul>` : `<p>${e(fallback)}</p>`; }
function renderDetail() {
  const m = matches.find(x => x.job.url === selectedURL);
  if (!m) { $('#detail').innerHTML = '<div class="detail-body"><h2>Select a role</h2><p>Its requirements and source details will appear here.</p></div>'; return; }
  const j = m.job;
  $('#detail').innerHTML = `<div class="detail-head"><p class="eyebrow">ROLE DETAILS / CHECK BEFORE APPLYING</p><h2>${e(j.title)}</h2><p class="employer">${e(j.employer)} · ${e(j.location)}</p></div><div class="detail-body">
    <h3>Why this role appears</h3><p>${e(m.explanation)}</p><div class="tags">${m.matched_skills.map(s => `<span class="tag">${e(s)}</span>`).join('')}</div>
    <h3>Requirements to check</h3><p>Education: ${e(j.requirements.education === 'not_stated' ? 'Not specified' : j.requirements.education)} · Experience: ${j.requirements.min_years === null ? 'Not specified' : `${j.requirements.min_years}+ years`}</p>
    ${list(m.missing, 'No gap found in the structured requirements. Confirm the complete advertisement.')}${list(m.unknown, '')}
    <h3>Skills not in this profile</h3>${list(m.missing_skills, 'All structured skills have a candidate fact.')}
    <h3>About the vacancy</h3><p>${e(j.description)}</p><p>Pay: ${e(j.salary)}</p>
    <div class="detail-source"><p><strong>Deadline:</strong> ${e(fmt(j.valid_until))}</p><p><strong>Source checked:</strong> ${e(fmt(j.observed_at))}</p><p>${e(m.lifecycle.reason)}</p><p>${j.provenance.length} source observation${j.provenance.length === 1 ? '' : 's'}</p>${j.synthetic ? '<p>Demonstration listing. No actual vacancy or application link.</p>' : `<a href="${e(j.url)}" target="_blank" rel="noopener noreferrer">Open original advertisement ↗</a>`}</div>
    <button class="primary" id="build-cv">Build CV for this role</button><p class="small">Only candidate-supplied facts are used. No application is submitted.</p></div>`;
  $('#build-cv').addEventListener('click', async () => {
    try {
      cv = await withReceipt(buildCV(profile, j));
      $('#cv-preview').innerHTML = `<h2 class="cv-name">${e(cv.profile.name)}</h2><p class="cv-contact">${e([cv.profile.location, cv.profile.contact].filter(Boolean).join(' · '))}</p><p class="cv-target">Application for: ${e(j.title)}</p>` +
        [['experience', 'Experience'], ['education', 'Education'], ['certificate', 'Certificates and training'], ['achievement', 'Achievements']].map(([kind, title]) => {
          const claims = cv.receipt.claims.filter(c => c.kind === kind);
          return claims.length ? `<section class="cv-section"><h3>${title}</h3><ul>${claims.map(c => `<li>${e(c.text)}</li>`).join('')}</ul></section>` : '';
        }).join('');
      const warnings = [...m.missing, ...m.unknown];
      $('#cv-warning').textContent = warnings.length ? `Review before sharing: ${warnings.join('; ')}. These requirements have not been added to the CV.` : (cv.receipt.synthetic ? 'Sample candidate and vacancy. This CV demonstrates the workflow.' : 'Review the CV and complete advertisement before sharing. Credentials have not been independently verified.');
      $('#cv-dialog').showModal();
    } catch (err) { $('#notice').textContent = `CV could not be prepared: ${err.message}`; }
  });
}
function factEditor(f, i) {
  const opt = (value, label) => `<option value="${value}" ${f.kind === value ? 'selected' : ''}>${label}</option>`;
  return `<fieldset class="fact-editor" data-id="${e(f.id)}"><legend>FACT ${i + 1} / ${e(f.id)}</legend>
    <div class="fact-controls"><label class="sr-only" for="kind-${i}">Fact ${i + 1} type</label><select id="kind-${i}" class="fact-kind">${opt('experience', 'Experience')}${opt('education', 'Education')}${opt('certificate', 'Certificate / licence')}${opt('achievement', 'Achievement')}</select><button class="remove-fact" type="button">Remove</button></div>
    <label for="text-${i}">Fact ${i + 1}: what can the candidate support?</label><textarea id="text-${i}" class="fact-text" required maxlength="1200">${e(f.text)}</textarea>
    <label for="skills-${i}">Skills supported by this fact (comma-separated)</label><input id="skills-${i}" class="fact-skills" value="${e(f.skills.join(', '))}" placeholder="e.g. inventory, excel">
    <div class="fact-fields"><div class="education-field ${f.kind === 'education' ? '' : 'hidden'}"><label for="level-${i}">Completed education level</label><select id="level-${i}" class="fact-level">${['not_stated','10','10+2','diploma','graduate','postgraduate'].map(x => `<option ${f.level === x ? 'selected' : ''}>${x}</option>`).join('')}</select></div>
    <div class="years-field ${f.kind === 'experience' ? '' : 'hidden'}"><label for="years-${i}">Years supported by this fact (optional)</label><input id="years-${i}" class="fact-years" type="number" min="0" max="100" step="0.5" value="${f.years ?? ''}"></div>
    <div class="certificate-field ${f.kind === 'certificate' ? '' : 'hidden'}"><label for="cert-${i}">Certificate / licence name</label><input id="cert-${i}" class="fact-certificate" value="${e(f.certificate || '')}" placeholder="Use the exact qualification name"></div></div></fieldset>`;
}
function wireFacts() {
  for (const row of document.querySelectorAll('.fact-editor')) {
    row.querySelector('.remove-fact').addEventListener('click', () => row.remove());
    row.querySelector('.fact-kind').addEventListener('change', event => {
      for (const [kind, cls] of [['education', '.education-field'], ['experience', '.years-field'], ['certificate', '.certificate-field']]) row.querySelector(cls).classList.toggle('hidden', event.target.value !== kind);
    });
  }
}
function fillProfile(value = profile) {
  draftSynthetic = value.synthetic;
  $('#profile-name').value = value.name; $('#profile-location').value = value.location;
  $('#profile-contact').value = value.contact || ''; $('#profile-esm').checked = value.esm;
  $('#facts-editor').innerHTML = value.facts.map(factEditor).join(''); wireFacts();
}
function readProfile() {
  return validateProfile({ name: $('#profile-name').value, location: $('#profile-location').value, contact: $('#profile-contact').value, esm: $('#profile-esm').checked,
    synthetic: draftSynthetic,
    facts: [...document.querySelectorAll('.fact-editor')].map(row => {
      const kind = row.querySelector('.fact-kind').value;
      const years = row.querySelector('.fact-years').value;
      return { id: row.dataset.id, kind, text: row.querySelector('.fact-text').value,
        skills: row.querySelector('.fact-skills').value.split(',').map(x => x.trim()).filter(Boolean),
        level: kind === 'education' ? row.querySelector('.fact-level').value : null,
        years: kind === 'experience' && years !== '' ? Number(years) : null,
        certificate: kind === 'certificate' ? row.querySelector('.fact-certificate').value : null };
    }) });
}
async function readJSON(file) {
  if (!file || file.size > 2_000_000) throw new Error('Choose a JSON file under 2 MB');
  return JSON.parse(await file.text());
}
async function init() {
  [bundle, samples] = await Promise.all(['jobs', 'profiles'].map(async x => {
    const r = await fetch(`./data/${x}.json`); if (!r.ok) throw new Error('Could not load demonstration data'); return r.json();
  }));
  feed = prepareFeed(bundle); asOf = bundle.reference_date; profile = validateProfile(samples[0]);
  $('#sample-profile').innerHTML = samples.map((p, i) => `<option value="${i}">${e(p.name)}</option>`).join('');
  for (const b of document.querySelectorAll('.nav')) b.addEventListener('click', () => showView(b.dataset.view));
  $('#edit-profile').addEventListener('click', () => showView('profile'));
  $('#search-form').addEventListener('submit', event => { event.preventDefault(); renderSearch(); });
  for (const id of ['query', 'domain', 'location', 'esm-only', 'include-review']) $(`#${id}`).addEventListener(id === 'query' || id === 'location' ? 'input' : 'change', renderSearch);
  $('#sample-profile').addEventListener('change', event => { fillProfile(validateProfile(samples[Number(event.target.value)])); });
  $('#profile-form').addEventListener('submit', event => {
    event.preventDefault();
    try { profile = readProfile(); $('#profile-message').textContent = ''; renderCandidate(); renderSearch(); showView('search'); $('#notice').textContent = 'Candidate facts updated in this tab. Download the profile to keep a copy.'; }
    catch (err) { $('#profile-message').textContent = err.message; }
  });
  $('#add-fact').addEventListener('click', () => {
    if (document.querySelectorAll('.fact-editor').length >= 60) { $('#profile-message').textContent = 'Maximum 60 facts'; return; }
    const current = [...document.querySelectorAll('.fact-editor')];
    const i = Math.max(0, ...current.map(r => Number(r.querySelector('.fact-kind').id.split('-')[1]))) + 1;
    $('#facts-editor').insertAdjacentHTML('beforeend', factEditor({ id: `fact_${crypto.randomUUID().replaceAll('-', '').slice(0, 12)}`, kind: 'experience', text: '', skills: [] }, i));
    // Wire only the new row, preserving edits in existing rows.
    const row = $('#facts-editor').lastElementChild;
    row.querySelector('.remove-fact').addEventListener('click', () => row.remove());
    row.querySelector('.fact-kind').addEventListener('change', event => { for (const [kind, cls] of [['education', '.education-field'], ['experience', '.years-field'], ['certificate', '.certificate-field']]) row.querySelector(cls).classList.toggle('hidden', event.target.value !== kind); });
    row.querySelector('textarea').focus();
  });
  $('#download-profile').addEventListener('click', () => { try { download('sevasetu-profile.json', JSON.stringify(readProfile(), null, 2)); } catch (err) { $('#profile-message').textContent = err.message; } });
  $('#import-profile').addEventListener('click', () => $('#profile-file').click());
  $('#profile-file').addEventListener('change', async event => { try { fillProfile(validateProfile(await readJSON(event.target.files[0]))); $('#profile-message').textContent = 'Profile imported locally. Save facts to update matches.'; } catch (err) { $('#profile-message').textContent = `Import failed: ${err.message}`; } event.target.value = ''; });
  $('#import-jobs').addEventListener('click', () => $('#jobs-file').click());
  $('#jobs-file').addEventListener('change', async event => {
    try {
      const nextBundle = await readJSON(event.target.files[0]), nextFeed = prepareFeed(nextBundle);
      if (!nextFeed.jobs.length) throw new Error('No valid jobs found');
      bundle = nextBundle; feed = nextFeed; imported = true; asOf = new Date().toISOString();
      renderMetrics(); renderSearch();
      const failures = Array.isArray(nextBundle.failures) ? nextBundle.failures.length : 0;
      $('#notice').textContent = `Imported locally: ${feed.jobs.length} unique listings; ${feed.rejected.length} invalid records excluded.${failures ? ` Feed reports ${failures} source failure(s); coverage is incomplete.` : ''} Confirm dates and requirements on the original advertisements.`;
    } catch (err) { $('#notice').textContent = `Import failed: ${err.message}`; }
    event.target.value = '';
  });
  $('#close-cv').addEventListener('click', () => $('#cv-dialog').close());
  $('#download-cv').addEventListener('click', () => { if (cv) download('sevasetu-cv.txt', cv.text, 'text/plain;charset=utf-8'); });
  $('#download-receipt').addEventListener('click', () => { if (cv) download('sevasetu-cv-evidence.json', JSON.stringify(cv.receipt, null, 2)); });
  $('#print-cv').addEventListener('click', () => window.print());
  $('#run-checks').addEventListener('click', async () => {
    const f = prepareFeed(await (await fetch('./data/jobs.json')).json());
    const p = validateProfile(samples[0]), date = '2026-11-02T12:00:00Z';
    const controls = [
      ['Expired vacancy withheld', !searchJobs(f.jobs, p, { asOf: date }).some(m => m.job.id === 'sample-expired')],
      ['Stale source withheld', !searchJobs(f.jobs, p, { asOf: date }).some(m => m.job.id === 'sample-stale')],
      ['Invalid URL rejected', f.rejected.length === 1],
      ['Duplicate listing collapsed', f.jobs.filter(j => j.title === 'Warehouse Coordinator').length === 1],
    ];
    let refused = false; try { validateSelection({ fact_ids: ['invented_degree'] }, p); } catch { refused = true; }
    controls.push(['Unsupported model claim refused', refused]);
    $('#check-results').textContent = controls.map(([name, ok]) => `${ok ? 'PASS' : 'FAIL'}  ${name}`).join('\n') + '\n\nThese fixture checks do not measure placement outcomes or live-model quality.';
  });
  renderMetrics(); renderCandidate(); renderSearch();
}
init().catch(err => { $('#notice').textContent = `Unable to start: ${err.message}. Use the local server described in the README.`; });
