'use strict';
const $ = id => document.getElementById(id);
const descriptions = {
  revocation: 'Queue an authorized action, revoke its grant, then deliver and retry. No write should commit.',
  delegation: 'Queue through a child grant, revoke the parent, then retry. Delegation must not preserve withdrawn authority.',
  continuation: 'Queue action A, revoke unrelated grant B, then deliver the same A. No fresh approval is issued.',
  duplicate: 'Deliver the same immutable queued action twice. The receiver should store one effect.',
  ack_loss: 'Commit a write but discard its reply at the caller boundary. A fresh connection retries the same action.',
  committed: 'Commit first, then revoke authority. The old effect remains; a later attempt cannot add another write.',
  rollback: 'Inject an exception after the effect insert but before event recording. Inspect the rollback before retrying.',
  contention: 'A separate connection attempts delivery while a revocation transaction holds the write lock, then retries after revocation commits.'
};
const mutations = {revocation:'Broken: check only when queued', delegation:'Broken: ignore parent revocation', continuation:'Broken: invalidate every grant'};
let python, bootPromise, manifest, lastState, busy=false;

function element(tag, text, className) { const el=document.createElement(tag); el.textContent=String(text); if(className) el.className=className; return el; }
function choose() {
  const name=$('case').value;
  $('description').textContent=descriptions[name];
  $('implementation').replaceChildren(new Option('Commit-time enforcement','correct'));
  if(mutations[name]) $('implementation').add(new Option(mutations[name],'broken'));
  $('control-note').textContent=mutations[name] ? 'Compare a deliberately broken implementation under the same expectation.' : 'This boundary check uses the unchanged receiver implementation.';
  lastState=null; $('next').disabled=true; $('run').disabled=true; $('export').disabled=true;
  $('verdict').className='verdict neutral'; $('verdict').replaceChildren(element('strong','Scenario selected'), element('span','Start a fresh experiment to execute this selection.'));
  $('effects-count').textContent='—'; $('expected-count').textContent='—'; $('integrity').textContent='—'; $('step').textContent='NOT RUN';
  renderRows('effects',[],3);renderRows('grants',[],4);$('timeline').replaceChildren(element('li','No steps executed.','empty'));$('raw').textContent='{}';
}
function setBusy(value) {busy=value; $('start').disabled=value; $('case').disabled=value; $('implementation').disabled=value; $('next').disabled=value||!lastState||lastState.done; $('run').disabled=$('next').disabled; $('export').disabled=value||!lastState;}
async function fetchText(url) {const r=await fetch(url);if(!r.ok)throw new Error(`Cannot load ${url}: HTTP ${r.status}`);return r.text();}
async function sha(text) {return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),n=>n.toString(16).padStart(2,'0')).join('');}
async function boot() {
  if(!bootPromise) bootPromise=(async()=>{
    $('runtime').textContent='Loading Python + SQLite. The first download may take a moment…';
    await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.js';script.onload=resolve;script.onerror=()=>reject(new Error('Python runtime download failed. Check network access and try again.'));document.head.append(script);});
    python=await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/'});
    manifest=JSON.parse(await fetchText('sources.json'));
    python.FS.mkdirTree('/experiment/baseline');
    for(const [path, expected] of Object.entries(manifest.files)) {
      const source=await fetchText('../'+path);
      if(await sha(source)!==expected)throw new Error(`Source hash mismatch: ${path}. Execution stopped.`);
      const target='/experiment/'+(path==='web/engine.py'?'engine.py':path);
      python.FS.writeFile(target,source,{encoding:'utf8'});
    }
    await python.runPythonAsync("import sys\nsys.path.insert(0, '/experiment')\nfrom engine import command_json\nimport sqlite3");
    $('runtime').textContent='Ready · Python '+python.runPython('sys.version.split()[0]')+' / SQLite '+python.runPython('sqlite3.sqlite_version')+' · source hashes checked';
  })().catch(error=>{bootPromise=null;throw error;});
  return bootPromise;
}
function renderRows(id, rows, columns) {
  const body=$(id);body.replaceChildren();
  if(!rows.length){const tr=document.createElement('tr'),td=element('td',id==='effects'?'No committed effects.':'No grants yet.','empty');td.colSpan=columns;tr.append(td);body.append(tr);return;}
  for(const row of rows){const tr=document.createElement('tr');for(const value of row){const td=document.createElement('td');if(value instanceof Node)td.append(value);else td.textContent=String(value??'—');tr.append(td);}body.append(tr);}
}
function render(state) {
  lastState=state;
  $('step').textContent=`STEP ${state.step} / ${state.total_steps}`;
  const v=$('verdict');v.className='verdict '+(state.done?(state.contract_met?'pass':'fail'):'neutral');
  const title=state.done?(state.contract_met?'Contract met':state.broken?'Contract violated — control detected':'Contract violated'):'Execution in progress';
  const note=state.done?(state.contract_met?'Observed committed state and delivery results match the fixed expectations.':state.broken?'The deliberately broken implementation failed the same expectation. This is the intended negative-control result.':'Observed state does not match the fixed contract. This run is a failure.'):(state.next_step||'Ready');
  v.replaceChildren(element('strong',title),element('span',note));
  $('effects-count').textContent=state.effects.length; $('expected-count').textContent=state.expected_rows.length;
  $('integrity').textContent=state.event_chain_valid&&state.integrity==='ok'?'VALID · LOCAL':'INVALID';
  renderRows('effects',state.effects,3);
  renderRows('grants',state.grants.map(g=>[g[0]+' / '+g[1],g[2],g[3],element('span',g[4]?'REVOKED':'ACTIVE','badge'+(g[4]?' revoked':''))]),4);
  const timeline=$('timeline');timeline.replaceChildren();
  for(const h of state.history){const li=document.createElement('li');li.append(element('strong',h.label),element('span',`${h.result} · ${h.effects.length} committed effect${h.effects.length===1?'':'s'}`));timeline.append(li);}
  if(!state.history.length)timeline.append(element('li','No steps executed.','empty'));
  $('next-label').textContent=state.next_step?'Next: '+state.next_step:'Complete · inspect or export the evidence';
  $('raw').textContent=JSON.stringify({queue:state.queue,delivery_results:state.delivery_results,expected_deliveries:state.expected_deliveries,events:state.events},null,2);
}
async function execute(action) {
  if(busy)return;setBusy(true);
  try {
    await boot();
    const cmd=action==='reset'?{action,case:$('case').value,broken:$('implementation').value==='broken'}:{action};
    python.globals.set('demo_command',JSON.stringify(cmd));
    render(JSON.parse(await python.runPythonAsync('command_json(demo_command)')));
  } catch(error) {
    $('verdict').className='verdict fail';$('verdict').replaceChildren(element('strong','Run could not complete'),element('span',error.message));
    lastState=null;$('runtime').textContent='Execution stopped. No result is claimed.';
  } finally {setBusy(false);}
}
$('case').addEventListener('change',choose);
$('implementation').addEventListener('change',()=>{const selected=$('implementation').value;choose();$('implementation').value=selected;});
$('start').addEventListener('click',()=>execute('reset'));
$('next').addEventListener('click',()=>execute('next'));
$('run').addEventListener('click',()=>execute('run'));
$('export').addEventListener('click',()=>{if(!lastState)return;const data={executed_at_utc:new Date().toISOString(),runtime:'Pyodide 314.0.7',scope:'Synthetic receiver in browser memory; not live TIP/Harmonic or external attestation',source_manifest:manifest,result:lastState};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)+'\n'],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`authority-${lastState.case}-${lastState.broken?'broken':'correct'}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  
