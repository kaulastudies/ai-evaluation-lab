/** Lab-owned tests of the pinned native CLI on disposable synthetic state only.
 * The Python controller verifies the complete source closure before invocation.
 * No live mission, model, dispatch adapter, or external provider is opened.
 */
import assert from 'node:assert/strict';
import {createHash, generateKeyPairSync, sign} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {mkdtempSync, readFileSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve, join} from 'node:path';
import {pathToFileURL} from 'node:url';

const root = resolve(process.argv[2]);
const sessions = JSON.parse(readFileSync(process.argv[3], 'utf8'));
const moduleAt = name => pathToFileURL(join(root, 'systemia/organism', name)).href;
const runtime = await import(moduleAt('goal-runtime.mjs'));
const store = await import(moduleAt('goal-store.mjs'));
const cli = join(root, 'systemia/organism/goal-cli.mjs');
const work = 'synthetic-review';
const provider = 'lab-reference-provider';
const dir = mkdtempSync(join(tmpdir(), 'eo-systemia-native-'));
const {privateKey, publicKey} = generateKeyPairSync('ed25519');
const publicPem = publicKey.export({type: 'spki', format: 'pem'});
// Independent serialization of the native signing contract, not its signer helper.
const fields = ['schema','scope','mission_key','goal_key','work_key','attempt',
  'attempt_key','provider_key','outcome','source_method','upstream_receipt_ref',
  'upstream_response_sha256','observed_at','expires_at'];
const hash = x => createHash('sha256').update(x).digest('hex');
const env = Object.fromEntries(['PATH','LANG','LC_ALL','SYSTEMROOT']
  .filter(k => process.env[k]).map(k => [k, process.env[k]]));

function invoke(args, configured = true) {
  const result = spawnSync(process.execPath, [cli, ...args], {
    cwd: dir, encoding: 'utf8', timeout: 10000, maxBuffer: 65536,
    env: {...env, ...(configured ? {
      EVERCRAFT_SYSTEMIA_PROVIDER_OBSERVER_PUBLIC_KEY_PEM: publicPem,
      EVERCRAFT_SYSTEMIA_PROVIDER_OBSERVER_PROVIDER_KEY: provider,
    } : {})},
  });
  assert.equal(result.error, undefined);
  return {command: args[0], exit_code: result.status,
    response: JSON.parse(result.status === 0 ? result.stdout : result.stderr)};
}
function signClaims(claims) {
  const message = Buffer.from('evercraft.systemia.provider-observation.v1\n' +
    JSON.stringify(Object.fromEntries(fields.map(k => [k, claims[k]]))));
  return {schema: 'evercraft.systemia.provider-observation-envelope.v1',
    key_id: 'evercraft-provider-observer-v1', claims,
    signature_base64: sign(null, message, privateKey).toString('base64')};
}
function assertHeld(state) {
  const task = state.tasks[0];
  assert.equal(task.status, 'blocked');
  assert.equal(task.attempt, 1);
  assert.equal(task.recovery_hold.effect_state, 'unknown');
  assert.equal(task.recovery_hold.auto_replay_allowed, false);
  assert.equal(task.recovery_hold.producer_outcome_verified, false);
  assert.deepEqual(state.next_work_keys, []);
  return {work_status: task.status, effect_state: task.recovery_hold.effect_state,
    auto_replay_allowed: false, producer_outcome_verified: false,
    next_work_keys: state.next_work_keys};
}

try {
  const t0 = new Date(Date.now() - 120000);
  let state = runtime.createGoalState({goalKey: 'lab-goal', missionKey: 'lab-mission',
    objective: 'Test evidence and authority boundaries using synthetic state', now: t0});
  state = runtime.admitGoalPlan({state, now: t0, plan: [
    {work_key: work, work_type: 'research', provider_key: provider},
    {work_key: 'dependent-review', work_type: 'verify', dependency_keys: [work]},
  ]});
  state = runtime.startGoalWork({state, workKey: work, now: t0});
  const baseFile = join(dir, 'base.json');
  await store.createGoalStateFile(baseFile, state);
  const hold = invoke(['recovery-hold', baseFile, work, '1', t0.toISOString(), '60000']);
  assert.equal(hold.exit_code, 0);
  const held = await store.readGoalState(baseFile);
  assertHeld(held);
  const stamp = Date.now();
  // Controller-owned oracle, created independently of the observer statement.
  // No provider effect or lookup is executed in this native CLI experiment.
  const oracle = {schema: 'lab.synthetic.effect-oracle.v1', effects: [], provider_calls: 0};
  const oracleBytes = JSON.stringify(oracle);
  const claims = {
    schema: 'evercraft.systemia.provider-observation-claims.v1',
    scope: 'systemia.goal.recovery.observe', mission_key: held.mission_key,
    goal_key: held.goal_key, work_key: work, attempt: 1,
    attempt_key: held.tasks[0].attempt_key, provider_key: provider, outcome: 'completed',
    source_method: 'authenticated_provider_refetch', upstream_receipt_ref: 'synthetic:oracle:empty',
    upstream_response_sha256: 'sha256:' + hash(oracleBytes),
    observed_at: new Date(stamp).toISOString(), expires_at: new Date(stamp + 300000).toISOString(),
  };
  const cases = [
    {id: 'signed_completed_without_effect', patch: {}, admitted: true, truth: 'CONTRADICTED_BY_SYNTHETIC_ORACLE'},
    {id: 'signed_not_found', patch: {outcome: 'not_found'}, admitted: true},
    {id: 'signed_unknown', patch: {outcome: 'unknown'}, admitted: true},
    ...Object.entries({mission_key: 'other-mission', goal_key: 'other-goal', work_key: 'other-work',
      attempt: 2, attempt_key: 'other-attempt', provider_key: 'other-provider'})
      .map(([key, value]) => ({id: 'wrong_' + key, patch: {[key]: value}, admitted: false})),
    {id: 'expired', patch: {observed_at: new Date(stamp - 120000).toISOString(),
      expires_at: new Date(stamp - 60000).toISOString()}, admitted: false},
    {id: 'altered_after_signing', patch: {}, admitted: false, tamper: true},
    {id: 'observer_not_configured', patch: {}, admitted: false, configured: false},
    {id: 'lab_envelope_is_not_native', envelope: sessions.none.observations[0].envelope, admitted: false},
    {id: 'duplicate_reconciliation', patch: {}, admitted: true, replay: true},
  ];
  const records = [];
  for (const item of cases) {
    const file = join(dir, item.id + '.json');
    const observationFile = join(dir, item.id + '-observation.json');
    writeFileSync(file, JSON.stringify(held), {mode: 0o600});
    const observation = item.envelope || signClaims({...claims, ...item.patch});
    if (item.tamper) observation.claims.outcome = 'unknown';
    writeFileSync(observationFile, JSON.stringify(observation), {mode: 0o600});
    const before = readFileSync(file, 'utf8');
    const calls = [invoke(['recovery-observe', file, work, '1', observationFile], item.configured !== false)];
    assert.equal(calls[0].exit_code, item.admitted ? 0 : 1, item.id);
    if (!item.admitted) assert.equal(readFileSync(file, 'utf8'), before);
    const after = await store.readGoalState(file);
    const boundary = assertHeld(after);
    if (item.admitted) {
      assert.equal(after.tasks[0].recovery_hold.reconciliation.observer_signature_verified, true);
      assert.equal(after.tasks[0].recovery_hold.reconciliation.external_effect_verified_by_systemia, false);
      assert.equal(after.tasks[0].recovery_hold.reconciliation.retry_authorized, false);
      assert.equal(after.tasks[0].recovery_hold.reconciliation.dispatch_authorized, false);
    }
    if (item.replay) {
      const replay = invoke(['recovery-observe', file, work, '1', observationFile]);
      assert.equal(replay.exit_code, 1);
      assert.match(replay.response.error, /already recorded/);
      calls.push(replay);
    }
    for (const action of ['complete', 'retry']) {
      const denied = invoke(['outcome', file, work, action, '1', 'synthetic:claim:only']);
      assert.equal(denied.exit_code, 1);
      assert.match(denied.response.error, /authoritative reconciliation/);
      calls.push(denied);
    }
    const restart = invoke(['start', file, work]);
    const completion = invoke(['receipt', file, 'synthetic:claim:only']);
    assert.equal(restart.exit_code, 1);
    assert.equal(completion.exit_code, 1);
    calls.push(restart, completion);
    assert.deepEqual(await store.readGoalState(file), after);
    records.push({id: item.id, observation, admitted: item.admitted,
      claim_truth: item.truth || 'NOT_ESTABLISHED', native_boundary: boundary,
      state_before: held, state_after: after, rejected_mutations_preserve_state: true,
      calls});
  }
  console.log(JSON.stringify({schema: 'EO-SYSTEMIA-NATIVE/0.1.0', public_key_pem: publicPem,
    setup_hold: hold, oracle, oracle_bytes: oracleBytes, cases: records,
    live_model_execution: false, provider_execution: false}));
} finally {
  rmSync(dir, {recursive: true, force: true});
}
