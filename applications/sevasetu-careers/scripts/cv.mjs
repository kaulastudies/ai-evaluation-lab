import { readFile, writeFile } from 'node:fs/promises';
import { prepareFeed, buildCV, withReceipt } from '../web/core.mjs';
import { modelSelection } from './local-model.mjs';

const [profilePath, feedPath, jobID, outputPath, model] = process.argv.slice(2);
if (!profilePath || !feedPath || !jobID || !outputPath) {
  console.error('Usage: node scripts/cv.mjs profile.json feed.json job-id output.txt [installed-ollama-model]');
  process.exitCode = 2;
} else {
  try {
    const profile = JSON.parse(await readFile(profilePath, 'utf8'));
    const feed = prepareFeed(JSON.parse(await readFile(feedPath, 'utf8')));
    const job = feed.jobs.find(j => j.id === jobID);
    if (!job) throw new Error('Job ID not found');
    const ids = model ? await modelSelection(profile, job, { model }) : null;
    const cv = await withReceipt(buildCV(profile, job, ids));
    cv.receipt.selection_method = model ? 'local_model_validated_fact_ids' : 'deterministic_skill_relevance';
    if (model) cv.receipt.model = model;
    await writeFile(outputPath, cv.text, { mode: 0o600 });
    await writeFile(`${outputPath}.receipt.json`, JSON.stringify(cv.receipt, null, 2) + '\n', { mode: 0o600 });
    console.log(`Wrote CV and evidence receipt. Review requirements: ${cv.receipt.eligibility_check.status}`);
  } catch (err) { console.error(err.message); process.exitCode = 1; }
}
