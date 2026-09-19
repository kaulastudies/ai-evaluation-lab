from pathlib import Path
import subprocess, sys
TASK_ROOT=Path(__file__).resolve().parent
def run(cmd,cwd,expected):
    p=subprocess.run(cmd,cwd=cwd)
    if p.returncode!=expected: raise SystemExit(f"Command returned {p.returncode}, expected {expected}: {' '.join(cmd)}")
def main():
    print("=== 1/4 Public tests on vulnerable fixture (must PASS) ===")
    run([sys.executable,"-m","unittest","discover","-s","tests/public","-v"],TASK_ROOT/"fixture",0)
    print("\n=== 2/4 Qualified verifier on vulnerable fixture (must FAIL) ===")
    run([sys.executable,str(TASK_ROOT/"verifier/acceptance.py"),str(TASK_ROOT/"fixture")],TASK_ROOT,1)
    print("\n=== 3/4 Verifier qualification controls (must QUALIFY) ===")
    run([sys.executable,str(TASK_ROOT/"verifier/qualify.py")],TASK_ROOT,0)
    print("\n=== 4/4 Qualified verifier on reference control (must PASS) ===")
    run([sys.executable,str(TASK_ROOT/"verifier/acceptance.py"),str(TASK_ROOT/"controls/reference")],TASK_ROOT,0)
    print("\nAP-002 PHASE 1 GREEN")
    return 0
if __name__=="__main__": raise SystemExit(main())
