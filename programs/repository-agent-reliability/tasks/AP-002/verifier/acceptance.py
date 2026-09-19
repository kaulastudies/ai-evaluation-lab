from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

TASK_ID="AP-002"
TASK_VERSION="0.1.0"
VERIFIER_VERSION="0.1.0"

def load_policy(root: Path):
    source=root/"app"/"workspace_policy.py"
    if not source.is_file(): raise FileNotFoundError(f"Missing candidate source: {source}")
    spec=importlib.util.spec_from_file_location("rarb_ap002_candidate",source)
    if spec is None or spec.loader is None: raise RuntimeError(f"Unable to load candidate: {source}")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module,"WorkspacePolicy"): raise RuntimeError("Candidate does not define WorkspacePolicy")
    return module.WorkspacePolicy()

def gate(i,p,d): return {"id":i,"passed":bool(p),"diagnostic":d}

def evaluate(root: Path):
    policy=load_policy(root)
    document={"workspace_id":"workspace-a","owner_id":"shared-user"}
    local_editor={"id":"editor-a","workspace_id":"workspace-a","role":"editor"}
    local_admin={"id":"admin-a","workspace_id":"workspace-a","role":"admin"}
    local_viewer={"id":"viewer-a","workspace_id":"workspace-a","role":"viewer"}
    foreign_editor={"id":"editor-b","workspace_id":"workspace-b","role":"editor"}
    foreign_admin={"id":"admin-b","workspace_id":"workspace-b","role":"admin"}
    collision={"id":"shared-user","workspace_id":"workspace-b","role":"viewer"}
    g01=policy.can_update(local_editor,document) is True and policy.can_update(local_admin,document) is True
    g02=policy.can_update(local_viewer,document) is False
    g03=policy.can_update(foreign_editor,document) is False and policy.can_update(foreign_admin,document) is False
    g04=policy.can_update(collision,document) is False
    gates=[
      gate("AP002-G01",g01,"same-workspace editor/admin update access preserved" if g01 else "same-workspace editor/admin access regressed"),
      gate("AP002-G02",g02,"same-workspace viewer denied update access" if g02 else "same-workspace viewer gained update access"),
      gate("AP002-G03",g03,"cross-workspace privileged roles denied" if g03 else "cross-workspace editor/admin bypassed workspace isolation"),
      gate("AP002-G04",g04,"cross-workspace owner-id collision denied" if g04 else "owner-id collision bypassed workspace isolation"),
    ]
    return {"task_id":TASK_ID,"task_version":TASK_VERSION,"verifier_version":VERIFIER_VERSION,"candidate":str(root),"gates":gates,"status":"VERIFIED_PASS" if all(x["passed"] for x in gates) else "VERIFIED_FAIL"}

def main():
    p=argparse.ArgumentParser(); p.add_argument("candidate",type=Path); p.add_argument("--json",action="store_true"); a=p.parse_args()
    r=evaluate(a.candidate.resolve())
    if a.json: print(json.dumps(r,ensure_ascii=False))
    else:
      print(f"{r['status']}  task={TASK_ID} verifier={VERIFIER_VERSION}")
      for x in r['gates']: print(f"  {x['id']}: {'PASS' if x['passed'] else 'FAIL'} - {x['diagnostic']}")
    return 0 if r['status']=="VERIFIED_PASS" else 1
if __name__=="__main__": raise SystemExit(main())
