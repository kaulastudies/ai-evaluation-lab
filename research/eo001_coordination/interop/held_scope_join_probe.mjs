#!/usr/bin/env node
/** Independent, synthetic review of ONE pinned pure Forge metadata function.
 * No vendored Forge code, package installation, host probe or stop operation.
 * Usage: node held_scope_join_probe.mjs [--proposed-guards] /reviewed/Forge/module.mjs
 * Exit 0: every stated expectation matched; 2: findings; 3: setup/source refusal.
 */
import fs from 'node:fs';
import {createHash} from 'node:crypto';

const REV='70510dbc18a326c8846e5a7005aa7198a9744987';
const BLOB='612f993ff555cccbe52088ed5abcbed407141bc2';
const SHA='5141a6cc02505c63d98d2fad9c4d1b77aeeff51022f3b5900f5ecb585df99361';
const PROPOSED_SHA='d8af39653800975c1bf82471ab2b42bb8bbcdbc5a8a7235a02874ba701320815';
const U='eo001-g1-synthetic-'+'a'.repeat(32)+'.scope';
const P='/user.slice/user-1000.slice/user@1000.service/app.slice/'+U;
const BOOT='12345678-1234-4123-8123-123456789abc';
const hash=x=>createHash('sha256').update(x).digest('hex');
const STATE='MATCHING_LOCAL_CGROUP_KILL_METADATA_REVIEW_ONLY';
const FLAGS=['kernel_write_permission_proven','actual_original_cgroup_fd_attested',
  'independently_authenticated_host','independent_lab_observation',
  'manager_unit_incarnation_verified','live_detached_child_verified',
  'exact_resource_limits_verified','method_frozen_by_lab',
  'owner_and_reviewer_approvals_valid','old_stop_permit_reusable',
  'actual_kernel_write_performed','physical_scope_cleanup_proven',
  'source_and_host_execution_admitted','model_execution_authorized',
  'production_execution_authorized'];

// Lab-authored protocol fixtures, not captured host data or production approvals.
function fixture(){
  return {
    proposal:{
      schema:'evercraft.eo001.gate1.exact-scope-stop-review.v1',
      state:'FIXED_SYNTHETIC_STOP_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW',
      requires_fresh_explicit_owner_approval:true,execution_authorized:false,
      actual_stop_performed:false,executable_implementation_reviewed:false,
      resource_policy:'SYNTHETIC_ONLY_ZERO_SWAP',reviewed_source_revision:REV,
      scope_unit:U,cgroup_path:P
    },
    candidate:{
      schema:'evercraft.eo001.gate1.held-cgroup-kill-review.v1',
      state:'HELD_SCOPE_CGROUP_KILL_CANDIDATE_SOURCE_REVIEW_ONLY',
      target_lookup_rule:'ONLY_RELATIVE_TO_HELD_ORIGINAL_SCOPE_FD',
      candidate_kernel_control_file:'cgroup.kill',candidate_single_write_value:'1',
      candidate_signal_semantics:'SIGKILL_WHOLE_CGROUP_SUBTREE',
      name_based_systemd_stop_used:false,control_file_opened:false,
      kernel_write_attempted:false,production_execution_authorized:false,
      model_execution_authorized:false,current_owner_and_reviewer_permit_usable:false,
      separate_protocol_review_required:true,separate_owner_and_lab_approval_required:true,
      kernel_write_permission_proven:false,original_scope_handle_proven_authentic:false,
      scope_replacement_race_eliminated_in_real_host:false,
      physical_descendant_death_proven:false,poststop_subtree_empty_independently_verified:false,
      cgroup_path_sha256:hash(P),scope_unit:U,source_revision:REV,
      expected_original_cgroup_device:'31',expected_original_cgroup_inode:'987654321',
      expected_boot_id:BOOT
    },
    survey:{
      schema:'evercraft.eo001.gate1.cgroup-kill-readonly-survey.v1',
      state:'LOCAL_CGROUP_KILL_METADATA_OBSERVED_REVIEW_REQUIRED',
      record_provenance:'INJECTED_TEST_READ_ONLY_UNATTESTED',
      cgroup2_filesystem_metadata_matched:true,cgroup_type:'domain',
      observed_populated_at_survey:true,cgroup_kill_entry_present:true,
      cgroup_kill_file_opened:false,cgroup_kill_write_attempted:false,
      scope_stop_requested:false,observer_outside_scope_at_survey:true,
      kernel_permission_to_write_verified:false,manager_unit_incarnation_verified:false,
      live_detached_child_verified:false,exact_resource_limits_verified:false,
      independently_authenticated_host:false,separately_reviewed_stop_method:false,
      owner_and_lab_approvals_present:false,model_execution_authorized:false,
      execution_authorized:false,scope_path_sha256:hash(P),scope_unit:U,
      source_revision:REV,original_scope_device:'31',original_scope_inode:'987654321',
      boot_id:BOOT,cgroup_kill_mode_has_owner_write_bit:true
    }
  };
}
function replaceClaimedPath(f,path){
  f.proposal.cgroup_path=path;
  f.candidate.cgroup_path_sha256=hash(path);
  f.survey.scope_path_sha256=hash(path);
}
const cases=[
  ['matching_metadata','existing_boundary','ACCEPT_REVIEW_ONLY',()=>{}],
  ['boot_mismatch','existing_boundary','REJECT',f=>{f.survey.boot_id='ffffffff-ffff-4fff-8fff-ffffffffffff';}],
  ['source_mismatch','existing_boundary','REJECT',f=>{f.survey.source_revision='b'.repeat(40);}],
  ['inode_mismatch','existing_boundary','REJECT',f=>{f.survey.original_scope_inode='987654322';}],
  ['old_stop_permit','existing_boundary','REJECT',f=>{f.candidate.current_owner_and_reviewer_permit_usable=true;}],
  ['name_based_target','existing_boundary','REJECT',f=>{f.candidate.target_lookup_rule='RESOLVE_BY_NAME';}],
  ['kernel_write_claim','existing_boundary','REJECT',f=>{f.candidate.kernel_write_attempted=true;}],
  ['hardware_attestation_claim','existing_boundary','REJECT',f=>{f.survey.independently_authenticated_host=true;}],
  ['effective_permission_claim','existing_boundary','REJECT',f=>{f.survey.kernel_permission_to_write_verified=true;}],
  ['old_method_write_value','existing_boundary','REJECT',f=>{f.candidate.candidate_single_write_value='0';}],
  ['fabricated_lab_approval','existing_boundary','REJECT',f=>{f.survey.owner_and_lab_approvals_present=true;}],
  ['unbounded_resource_policy','existing_boundary','REJECT',f=>{f.proposal.resource_policy='UNBOUNDED';}],
  ['numeric_device_and_inode','proposed_input_hardening','REJECT',f=>{
    f.candidate.expected_original_cgroup_device=31; f.survey.original_scope_device=31;
    f.candidate.expected_original_cgroup_inode=987654321; f.survey.original_scope_inode=987654321;
  }],
  ['relative_path_agreed_by_both_views','proposed_input_hardening','REJECT',f=>{
    replaceClaimedPath(f,'relative/'+U);
  }],
  ['dotdot_path_agreed_by_both_views','proposed_input_hardening','REJECT',f=>{
    replaceClaimedPath(f,'/user.slice/../'+U);
  }]
];

function readPinnedSource(path){
  if(process.platform!=='linux'||!fs.constants.O_NOFOLLOW)throw Error('LINUX_SOURCE_REVIEW_REQUIRED');
  const fd=fs.openSync(path,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{
    const stat=fs.fstatSync(fd);
    if(!stat.isFile()||stat.size>65536)throw Error('SOURCE_SIZE_OR_KIND');
    const data=fs.readFileSync(fd);
    if(data.length>65536||data.length!==stat.size)throw Error('SOURCE_SIZE_CHANGED');
    const blob=createHash('sha1').update(Buffer.from('blob '+data.length+'\0')).update(data).digest('hex');
    if(blob!==BLOB||hash(data)!==SHA)throw Error('SOURCE_PIN_MISMATCH');
    return data;
  }finally{fs.closeSync(fd);}
}
// Optional LAB PROPOSAL only. This is the exact adjacent patch applied in
// memory to the verified original bytes; it never modifies a Forge checkout.
function proposedGuards(bytes){
  let code=bytes.toString('utf8');
  const helper="const validPath=value=>typeof value==='string'&&\n"+
    "  value.startsWith('/user.slice/')&&value.length<=512&&\n"+
    "  !value.includes('//')&&!value.includes('..')&&\n"+
    "  !value.split('/').some(p=>p==='.'||p==='..');\n";
  code=code.replace('const sha=v=>',helper+'const sha=v=>')
    .replace("typeof proposal.cgroup_path==='string'&&","validPath(proposal.cgroup_path)&&")
    .replace("need(NUM.test(candidate.expected_original_cgroup_device||'')&&",
      "need(typeof candidate.expected_original_cgroup_device==='string'&&\n"+
      "    typeof candidate.expected_original_cgroup_inode==='string'&&\n"+
      "    NUM.test(candidate.expected_original_cgroup_device||'')&&");
  const changed=Buffer.from(code);
  if(hash(changed)!==PROPOSED_SHA)throw Error('PROPOSED_PATCH_BYTES_MISMATCH');
  return changed;
}
async function main(){
  const args=process.argv.slice(2);
  const proposed=args[0]==='--proposed-guards';
  if(proposed)args.shift();
  if(args.length!==1)throw Error('ONE_PINNED_SOURCE_FILE_REQUIRED');
  const original=readPinnedSource(args[0]);
  const bytes=proposed?proposedGuards(original):original;
  // Import verified bytes, not a second path lookup. The pinned module imports
  // only node:crypto; unrelated Forge modules and top-level code are not loaded.
  const {joinHeldScopeKillSurveyForReview:join}=await import(
    'data:text/javascript;base64,'+bytes.toString('base64'));
  const results=cases.map(([id,group,expected,mutate])=>{
    const f=fixture(); mutate(f);
    // Test serialized JSON objects, not getters, inherited properties or aliases.
    const input=JSON.parse(JSON.stringify(f));
    let actual,reason=null,boundaries=null;
    try{
      const output=join(input);
      boundaries=FLAGS.every(k=>output[k]===false)&&output.metadata_agreement_only===true&&
        output.source_view_count===2&&!JSON.stringify(output).includes(input.proposal.cgroup_path);
      actual=output.state===STATE&&boundaries?'ACCEPT_REVIEW_ONLY':'UNEXPECTED_OUTPUT';
    }catch(e){
      const known=typeof e?.code==='string'&&/^CGKILL_JOIN_[A-Z_]+$/.test(e.code);
      actual=known?'REJECT':'UNEXPECTED_EXCEPTION';
      reason=known?e.code:'UNCLASSIFIED_ERROR';
    }
    return {id,group,expected,actual,expectation_matched:actual===expected,
      reason,returned_authority_flags_false:boundaries};
  });
  const issues=results.filter(r=>!r.expectation_matched);
  const summary={
    schema:'LAB-EO001-PINNED-JOIN-PROBE/0.1.0',
    state:issues.length?'INPUT_HARDENING_REVIEW_REQUIRED':'STATED_EXPECTATIONS_MATCHED',
    source_revision:REV,source_git_blob:BLOB,source_sha256:SHA,
    source_variant:proposed?'LAB_PROPOSED_GUARDS_NOT_UPSTREAM':'UPSTREAM_PINNED',
    tested_module_sha256:hash(bytes),
    runtime:process.version,case_count:results.length,
    existing_boundary_checks_matched:results.filter(r=>r.group==='existing_boundary'&&r.expectation_matched).length,
    proposed_hardening_expectations_not_met:issues.filter(r=>r.group==='proposed_input_hardening').length,
    all_returned_results_kept_authority_false:results.filter(r=>r.returned_authority_flags_false!==null)
      .every(r=>r.returned_authority_flags_false===true),
    actual_host_control_executed:false,model_execution_performed:false,
    production_exploit_demonstrated:false,proposed_hardening_is_jointly_approved:false,
    notes:'Direct pure-function JSON inputs. Does not show upstream factories emit these malformed records. No original receipt, kernel probe, host stop, model or field acceptance.',
    cases:results
  };
  console.log(JSON.stringify(summary,null,2));
  return issues.length?2:0;
}
try{process.exitCode=await main();}
catch{console.error('PINNED_JOIN_PROBE_BLOCKED');process.exitCode=3;}
