import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { prepareFeed, searchJobs, buildCV, validateProfile, withReceipt } from '../web/core.mjs';

const root = new URL('../', import.meta.url);
const paths = ['web/data/jobs.json', 'web/data/profiles.json', 'tests/relevance-labels.json', 'web/core.mjs'];
const files = await Promise.all(paths.map(p => readFile(new URL(p, root), 'utf8')));
const bundle = JSON.parse(files[0]), profiles = JSON.parse(files[1]), labels = JSON.parse(files[2]);
const feed = prepareFeed(bundle), cases = [];
for (const label of labels.cases) {
  const profile = profiles.find(p => p.id === label.profile);
  const ranked = searchJobs(feed.jobs, profile, { asOf: bundle.reference_date });
  const facts = validateProfile(profile).facts;
  const cv = await withReceipt(buildCV(profile, ranked[0].job));
  const checks = {
    acceptable_first: label.acceptable_first.includes(ranked[0]?.job.id),
    unsafe_lifecycle_withheld: label.must_withhold.every(id => !ranked.some(r => r.job.id === id)),
    qualification_gaps_visible: label.must_flag_gap.every(id => ranked.find(r => r.job.id === id)?.status === 'requirements_gap'),
    cv_claims_supported: cv.receipt.claims.every(c => facts.some(f => f.id === c.fact_id && f.text === c.text)),
  };
  cases.push({ profile: label.profile, first_result: ranked[0]?.job.id, checks, passed: Object.values(checks).every(Boolean), cv_sha256: cv.receipt.cv_sha256 });
}
const report = { version: '0.1.0', assessment_date: bundle.reference_date,
  scope: 'Three author-labelled synthetic candidates. No real candidate, vacancy-feed, placement or live-model quality evaluation.',
  input_records: feed.input_count, unique_jobs: feed.jobs.length, rejected_records: feed.rejected.length,
  cases, passed: cases.every(c => c.passed),
  inputs_sha256: Object.fromEntries(paths.map((p, i) => [p, createHash('sha256').update(files[i]).digest('hex')])),
};
const output = process.argv[2] || new URL('evidence/offline-evaluation.json', root);
await writeFile(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ passed: report.passed, cases: cases.length, first_results: cases.map(c => c.first_result) }));
if (!report.passed) process.exitCode = 1;
