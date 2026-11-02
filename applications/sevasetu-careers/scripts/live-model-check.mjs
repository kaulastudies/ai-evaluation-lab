import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { modelSelection } from './local-model.mjs';
import { prepareFeed, searchJobs, buildCV, withReceipt, validateProfile } from '../web/core.mjs';

const model = process.env.SEVASETU_TEST_MODEL || 'qwen2.5:0.5b';
const profiles = JSON.parse(await readFile(new URL('../web/data/profiles.json', import.meta.url)));
const bundle = JSON.parse(await readFile(new URL('../web/data/jobs.json', import.meta.url)));
const feed = prepareFeed(bundle), outcomes = [];
const tagsResponse = await fetch('http://127.0.0.1:11434/api/tags');
if (!tagsResponse.ok) throw new Error('Cannot inspect installed local model');
const tags = await tagsResponse.json();
const installed = tags.models?.find(m => m.name === model || m.model === model);
if (!installed) throw new Error('Requested local model is not installed');
const version = await (await fetch('http://127.0.0.1:11434/api/version')).json();
for (const raw of profiles) {
  const profile = validateProfile(raw);
  const job = searchJobs(feed.jobs, profile, { asOf: bundle.reference_date })[0].job;
  const start = performance.now();
  try {
    const selected = await modelSelection(profile, job, { model });
    const cv = await withReceipt(buildCV(profile, job, selected));
    const supported = cv.receipt.claims.every(c => profile.facts.some(f => f.id === c.fact_id && f.text === c.text));
    outcomes.push({ case: raw.id, status: supported ? 'PASS' : 'FAIL', selected_fact_ids: selected,
      claims_supported: supported, cv_sha256: cv.receipt.cv_sha256, elapsed_ms: Math.round(performance.now() - start) });
  } catch (err) {
    outcomes.push({ case: raw.id, status: 'FAIL', refused_output: true, reason: err.message, elapsed_ms: Math.round(performance.now() - start) });
  }
}
const report = { tested_at: new Date().toISOString(), model, model_digest: installed.digest, ollama_version: version.version,
  inference: 'real_local_model_cpu', scope: 'Three synthetic profiles; verifies accepted fact selection and claim rendering, not placement quality.',
  cases: outcomes, all_passed: outcomes.every(x => x.status === 'PASS') };
await mkdir('live-results', { recursive: true });
await writeFile('live-results/local-model.json', JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
if (!report.all_passed) process.exitCode = 1;
