'use strict';
let labBundle, labWorker = null, labTimer, labReport = null, labRunId = 0;
const labCopy = {
  'false-green':['Recorded false-green','Ollama llama3 generated this AP-005 candidate. The historical public test passed; independent gates rejected it. Run the same Python checks now.'],
  repair:['Recorded bounded repair','Ollama generated this replacement after receiving failed-gate evidence. Check whether the same verifier accepts it.'],
  nemotron:['NVIDIA Nemotron · Nebius Token Factory','An actual NVIDIA Nemotron 3 Super candidate from Phase 12. Execute its public tests and stale-response verifier in your browser.'],
  failure:['Preserved AP-001 failure','The model claimed success, but the recorded candidate failed. The result remains in the ledger.'],
  'drop-inactive':['Fault: dropped inactive rows','An intentionally faulty control removes rows whose active flag is false.'],
  'coerce-zero':['Fault: zero becomes null','An intentionally faulty control uses a truthiness fallback and turns a valid zero into None.'],
  'collapse-note':['Fault: empty notes collapse','An intentionally faulty control fails to preserve the distinction between an empty string and a missing note.'],
  'mutate-input':['Fault: input rows change','An intentionally faulty control mutates the source rows while producing its result.'],
  'known-bad':['Known-bad baseline','The original faulty fixture is a qualification control, not a new model attempt.'],
  reference:['Reference implementation','The qualified verifier must accept the known-correct reference before we trust its failures.']
};
function updateLabCandidate(){
  const key=$('lab-candidate').value, variant=labBundle.variants[key];
  $('lab-title').textContent=labCopy[key][0];$('lab-context').textContent=labCopy[key][1];
  $('lab-code').textContent=variant.source;
  $('lab-source').href=`https://github.com/kaulastudies/ai-evaluation-lab/tree/${labBundle.evidence_commit}/${variant.path}`;
  document.querySelectorAll('[data-lab-preset]').forEach(b=>b.classList.toggle('selected',b.dataset.labPreset===key));
  $('lab-output').innerHTML='<div class="lab-empty"><h3>Ready to execute this candidate.</h3><p>No result is assumed. Click Run Python checks.</p></div>';
  $('lab-status').textContent='Ready. No model inference will be called.';
  $('lab-runtime-label').textContent='NOT RUN';$('lab-report-actions').hidden=true;$('lab-raw').hidden=true;labReport=null;
}
function labBusy(busy){
  $('lab-run').disabled=busy;$('lab-controls').disabled=busy;$('lab-candidate').disabled=busy;
  document.querySelectorAll('[data-lab-preset]').forEach(b=>b.disabled=busy);
  $('lab-cancel').hidden=!busy;
}
function stopLab(){
  if(labWorker) labWorker.terminate();labWorker=null;clearTimeout(labTimer);labBusy(false);
}
function renderLabReports(data){
  labReport={...data,completed_at:new Date().toISOString(),report_scope:'Bundled Python verifier re-execution. No new model inference; not historical source-exact replay.'};
  const reports=data.reports;
  if(reports.length>1){
    const accepted=reports.filter(r=>r.final_verdict==='VERIFIED_PASS').length;
    $('lab-output').innerHTML=`<div class="lab-verdict good"><strong>${reports.length} controls executed</strong><span>${accepted} accepted · ${reports.length-accepted} rejected. Inspect every result below.</span></div><div class="table-wrap"><table><thead><tr><th>Control</th><th>Public</th><th>Independent verdict</th><th>Failed gates</th></tr></thead><tbody>${reports.map(r=>`<tr><td>${esc(r.variant)}</td><td>${yes(r.public_tests_passed)}</td><td class="${tone(r.final_verdict)}">${esc(r.final_verdict)}</td><td>${esc(r.gates.filter(g=>!g.passed).map(g=>g.id).join(', ')||'None')}</td></tr>`).join('')}</tbody></table></div>`;
  } else {
    const r=reports[0];
    $('lab-output').innerHTML=`<div class="lab-compare"><div><small>PUBLIC TESTS</small><strong class="${r.public_tests_passed?'good':'bad'}">${yes(r.public_tests_passed)}</strong><span>${r.public_tests_run ?? 0} test(s) executed</span></div><div><small>INDEPENDENT VERDICT</small><strong class="${tone(r.final_verdict)}">${esc(r.final_verdict.replace('VERIFIED_',''))}</strong><span>${r.gates.filter(g=>g.passed).length} / ${r.gates.length} gates passed</span></div></div>${r.false_green?'<div class="false-green-alert">False-green caught: ordinary tests passed, but the task contract failed.</div>':''}<div>${r.gates.map(g=>`<div class="gate"><span class="gate-icon ${g.passed?'good':''}">${g.passed?'✓':'×'}</span><div><b>${esc(g.id)}</b><p>${esc(g.diagnostic)}</p></div><span class="gate-status ${g.passed?'good':'bad'}">${g.passed?'PASS':'FAIL'}</span></div>`).join('')}</div><p class="small">Check execution: ${r.check_duration_ms} ms · Python ${esc(r.python_version)} · ${esc(r.candidate_kind.replaceAll('_',' '))}</p>`;
  }
  $('lab-runtime-label').textContent='EXECUTED IN PYTHON';
  $('lab-status').textContent='Completed. These results came from executing the Python code in this browser.';
  $('lab-report-actions').hidden=false;$('lab-raw').textContent=JSON.stringify(labReport,null,2);
}
function runLab(controlSuite=false){
  if(labWorker)return;
  if(controlSuite){$('lab-candidate').value='reference';updateLabCandidate();$('lab-title').textContent='AP-005 · verifier qualification';$('lab-context').textContent='Reference, known-bad baseline and four deliberate mutations. These are fixed qualification controls; no model is invoked.';}
  labBusy(true);labReport=null;$('lab-report-actions').hidden=true;$('lab-raw').hidden=true;
  $('lab-runtime-label').textContent='RUNNING';$('lab-status').textContent='Starting disposable Python worker…';
  $('lab-output').innerHTML='<div class="lab-empty"><div class="loading-line"></div><h3>Running the Python checks.</h3><p>Loading the pinned Python runtime, checking artifact hashes and running public tests plus the independent verifier.</p></div>';
  const runId=++labRunId;
  labTimer=setTimeout(()=>{stopLab();$('lab-status').textContent='Execution timed out after 60 seconds. No result is claimed. Retry when the runtime has downloaded.';$('lab-runtime-label').textContent='TIMED OUT';},60000);
  try {
    labWorker=new Worker('lab-worker.mjs',{type:'module'});
    labWorker.onmessage=({data})=>{if(runId!==labRunId)return;if(data.status==='complete'){renderLabReports(data);stopLab();}else if(data.status==='error'){stopLab();$('lab-status').textContent=`Execution failed: ${data.message}`;$('lab-runtime-label').textContent='ERROR';$('lab-output').textContent='No successful result is claimed. Use the local workbench if browser Python is unavailable.';}else{$('lab-status').textContent=data.message;}};
    labWorker.onerror=event=>{stopLab();$('lab-status').textContent='Python worker could not start. Check that the browser runtime assets were installed.';$('lab-runtime-label').textContent='ERROR';};
    labWorker.postMessage({variant:$('lab-candidate').value,controlSuite});
  }catch(error){stopLab();$('lab-status').textContent=error.message;}
}
(async()=>{
  try{
    const response=await fetch('browser-evidence.json');if(!response.ok)throw Error('Browser evidence bundle unavailable.');labBundle=await response.json();
    $('lab-candidate').addEventListener('change',updateLabCandidate);
    document.querySelectorAll('[data-lab-preset]').forEach(b=>b.addEventListener('click',()=>{$('lab-candidate').value=b.dataset.labPreset;updateLabCandidate();}));
    $('lab-run').addEventListener('click',()=>runLab());$('lab-controls').addEventListener('click',()=>runLab(true));
    $('lab-cancel').addEventListener('click',()=>{++labRunId;stopLab();$('lab-status').textContent='Cancelled. Worker terminated; no completed result.';$('lab-runtime-label').textContent='CANCELLED';});
    $('lab-show-raw').addEventListener('click',()=>{$('lab-raw').hidden=!$('lab-raw').hidden;});
    $('lab-export').addEventListener('click',()=>{if(!labReport)return;const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(labReport,null,2)],{type:'application/json'}));a.download='proofgate-browser-execution.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});
    updateLabCandidate();
  }catch(error){$('lab-status').textContent=error.message;$('lab-run').disabled=true;$('lab-controls').disabled=true;}
})();
