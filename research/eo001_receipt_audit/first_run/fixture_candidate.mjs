/** Synthetic inference test double. Never contacts an inference provider. */
import {readFileSync, writeFileSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {randomUUID} from 'node:crypto';
const [source, directory, mode] = process.argv.slice(2);
const imported = name => import(pathToFileURL(join(resolve(source), 'integrations/ai-evaluation-lab', name)).href);
const {liveModelDecision} = await imported('eo001-raven-local-candidate.mjs');
const {decide} = await imported('eo001-lab-candidate.mjs');
const context = JSON.parse(readFileSync(0, 'utf8'));
let action;
try {
  action = await liveModelDecision(context, {
    infer: async () => {
      if (mode === 'error') throw Error('synthetic inference failure');
      let proposal = mode === 'unsafe_retry' ? {action: 'execute'} : decide(context);
      if (mode === 'withhold_confirmed' && proposal.fulfillment_authorized === true)
        proposal = {...proposal, fulfillment_authorized: false};
      return {text: JSON.stringify(proposal),
        provider: 'test-double', model: 'NOT-A-LIVE-MODEL', provider_receipt: 'synthetic-fixture-only'};
    },
    record: receipt => writeFileSync(join(directory, randomUUID() + '.json'), JSON.stringify(receipt)),
  });
} catch {
  action = {action: 'finish', payment_status: 'unknown', fulfillment_authorized: false, receipt_id: null};
}
process.stdout.write(JSON.stringify(action));
