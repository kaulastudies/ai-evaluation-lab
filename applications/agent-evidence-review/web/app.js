"use strict";
const $ = id => document.getElementById(id);
let examples = [], lastReport = null;
function invalidate() { lastReport = null; $("export").disabled = true; $("status").textContent = "INPUT CHANGED · REVIEW AGAIN"; }
function choose() {
  const example = examples[Number($("scenario").value)];
  $("description").textContent = example.description;
  $("trace").value = JSON.stringify(example.trace, null, 2);
  invalidate();
}
function row(label, value, className="") {
  const node = document.createElement("div"); node.className = "metric";
  const key = document.createElement("span"), val = document.createElement("strong");
  key.textContent = label; val.textContent = value; val.className = className;
  node.append(key, val); $("summary").append(node);
}
$("review").addEventListener("click", async () => {
  $("error").textContent = ""; $("review").disabled = true; invalidate();
  try {
    const response = await fetch("/review", {method:"POST", headers:{"Content-Type":"application/json"}, body:$("trace").value});
    const report = await response.json();
    if (!response.ok) throw new Error(report.error || "Review failed");
    lastReport = report; $("export").disabled = false;
    $("status").textContent = report.evidence_status === "INVALID" ? "INVALID EVIDENCE" : report.policy_verdict === "FAIL" ? "FINDINGS DETECTED" : "CHECKS COMPLETE";
    $("summary").replaceChildren();
    row("Evidence format", report.evidence_status, report.evidence_status === "VALID" ? "good" : "bad");
    row("Recorded policy", report.policy_verdict, report.policy_verdict === "FAIL" ? "bad" : "neutral");
    row("Completion", report.completion, report.completion === "UNSUPPORTED" ? "bad" : "neutral");
    row("Observed tool calls", String(report.calls));
    row("Unresolved writes", String(report.unresolved_writes ?? "—"));
    row("Authenticity / completeness", "NOT VERIFIED", "neutral");
    $("findings").replaceChildren();
    for (const finding of report.findings) {
      const node = document.createElement("div"), label = document.createElement("b"), detail = document.createElement("span");
      node.className = "finding"; label.textContent = `${finding.event === null ? "INPUT" : "EVENT " + (finding.event + 1)} · ${finding.code}`;
      detail.textContent = finding.detail; node.append(label, detail); $("findings").append(node);
    }
    if (!report.findings.length) { const node=document.createElement("p"); node.className="clean"; node.textContent="No policy violations detected in these supplied events. This does not establish the safety of unrecorded actions."; $("findings").append(node); }
    $("raw").textContent=JSON.stringify(report,null,2);
  } catch (error) { $("error").textContent=error.message; $("status").textContent="REVIEW ERROR"; $("summary").replaceChildren(); $("findings").replaceChildren(); $("raw").textContent=""; }
  finally { $("review").disabled=false; }
});
$("trace").addEventListener("input", invalidate);
$("scenario").addEventListener("change", choose);
$("file").addEventListener("change", async () => {
  const file=$("file").files[0]; if (!file) return;
  invalidate();
  if (file.size>1000000) { $("error").textContent="Choose a JSON file smaller than 1 MB."; return; }
  $("trace").value=await file.text(); $("description").textContent="Imported file. Only submit records you are authorized to inspect.";
});
$("export").addEventListener("click",()=>{
  if (!lastReport) return;
  const url=URL.createObjectURL(new Blob([JSON.stringify(lastReport,null,2)],{type:"application/json"}));
  const anchor=document.createElement("a"); anchor.href=url; anchor.download="agent-evidence-report.json"; anchor.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});
fetch("/examples.json").then(r=>r.json()).then(data=>{ examples=data; for (const [i, example] of examples.entries()) { const option=document.createElement("option"); option.value=i; option.textContent=example.name; $("scenario").append(option); } choose(); }).catch(()=>{ $("error").textContent="Could not load the synthetic controls."; });
