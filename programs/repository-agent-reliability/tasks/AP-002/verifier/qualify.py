from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
TASK_ROOT=Path(__file__).resolve().parents[1]
VERIFIER=TASK_ROOT/"verifier"/"acceptance.py"
OUTPUT=TASK_ROOT/"evidence"/"verifier-qualification.json"
CONTROLS=[
 ("reference",TASK_ROOT/"controls/reference","PASS"),
 ("known_bad",TASK_ROOT/"controls/known_bad","FAIL"),
 ("mutation_remove_workspace_guard",TASK_ROOT/"controls/mutations/remove_workspace_guard","FAIL"),
 ("mutation_trust_owner_across_workspace",TASK_ROOT/"controls/mutations/trust_owner_across_workspace","FAIL"),
 ("mutation_deny_local_admin",TASK_ROOT/"controls/mutations/deny_local_admin","FAIL"),
]
def run_control(name,root,expected):
    p=subprocess.run([sys.executable,str(VERIFIER),str(root),"--json"],cwd=TASK_ROOT,text=True,capture_output=True)
    if not p.stdout.strip(): raise RuntimeError(f"{name}: verifier produced no JSON\nstderr:\n{p.stderr}")
    r=json.loads(p.stdout); actual="PASS" if r["status"]=="VERIFIED_PASS" else "FAIL"
    return {"name":name,"candidate":root.relative_to(TASK_ROOT).as_posix(),"expected":expected,"actual":actual,"expectation_met":actual==expected,"failed_gates":[x["id"] for x in r["gates"] if not x["passed"]]}
def main():
    controls=[run_control(*c) for c in CONTROLS]
    record={"task_id":"AP-002","task_version":"0.1.0","verifier_version":"0.1.0","reference_passed":controls[0]["actual"]=="PASS","known_bad_rejected":controls[1]["actual"]=="FAIL","critical_mutations_total":3,"critical_mutations_rejected":sum(1 for x in controls[2:] if x["actual"]=="FAIL"),"controls":controls}
    record["status"]="QUALIFIED" if record["reference_passed"] and record["known_bad_rejected"] and record["critical_mutations_rejected"]==3 and all(x["expectation_met"] for x in controls) else "HOLD"
    OUTPUT.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(record,indent=2)); print(); print(f"Wrote {OUTPUT}")
    return 0 if record["status"]=="QUALIFIED" else 1
if __name__=="__main__": raise SystemExit(main())
