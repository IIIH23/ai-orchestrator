#!/usr/bin/env python3
import argparse, json, os, subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def check_git():
    r = {}
    try:
        r["branch"] = subprocess.run(["git","branch","--show-current"],capture_output=True,text=True,cwd=REPO_ROOT).stdout.strip()
        dirty = subprocess.run(["git","status","--porcelain"],capture_output=True,text=True,cwd=REPO_ROOT).stdout.strip()
        r["dirty"] = bool(dirty)
        r["dirty_files"] = len(dirty.splitlines()) if dirty else 0
        branches = subprocess.run(["git","branch","--list","feat/*","audit/*","fix/*"],capture_output=True,text=True,cwd=REPO_ROOT).stdout.strip().splitlines()
        r["feature_branches"] = [b.strip().strip("* ") for b in branches if b.strip()]
    except Exception as e:
        r["error"] = str(e)
    return r

def check_files():
    required = ["AGENTS.md","ROADMAP.md","ORCHESTRATOR_POLICY.md","scripts/bootstrap-staging.sh","tools/linear_sync.py","tools/telegram_notify.py","tools/rollback.py",".github/workflows/ci.yml",".github/workflows/smoke.yml"]
    return {"missing":[f for f in required if not(REPO_ROOT/f).exists()]}

def check_cron():
    r = {"available":False}
    try:
        out = subprocess.run(["hermes","cron","list"],capture_output=True,text=True)
        if out.returncode==0:
            r["available"]=True
            r["output"]=out.stdout.strip()
    except Exception as e:
        r["error"]=str(e)
    return r

def check_staging():
    r = {"available":False}
    try:
        out = subprocess.run(["ssh","-i",os.path.expanduser("~/.ssh/deploy_staging_ed25519"),"-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5","deploy@157.180.125.174","df -h / | tail -n1 && free -m | awk '/Mem:/{print \"RAM: \" \"MB\"}' && systemctl is-active fail2ban"],capture_output=True,text=True,timeout=15)
        if out.returncode==0:
            r["available"]=True
            r["info"]=out.stdout.strip()
    except Exception as e:
        r["error"]=str(e)
    return r

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--quick",action="store_true")
    p.add_argument("--full",action="store_true")
    p.add_argument("--json",action="store_true")
    p.add_argument("--fix-safe",action="store_true")
    a = p.parse_args()
    if not a.quick and not a.full:
        a.quick = True
    report = {"timestamp":datetime.utcnow().isoformat()+"Z","mode":"quick"if a.quick else"full"}
    report["git"]=check_git()
    report["files"]=check_files()
    report["cron"]=check_cron()
    if a.full:
        report["staging"]=check_staging()
    if a.json:
        print(json.dumps(report,indent=2))
    else:
        print("=== Orchestrator Self-Audit ===")
        print("Time:",report["timestamp"])
        print("Branch:",report["git"].get("branch","?"))
        print("Dirty:",report["git"].get("dirty",False),"(",report["git"].get("dirty_files",0),"files)")
        print("Feature branches:",len(report["git"].get("feature_branches",[])))
        print("Missing files:",len(report["files"].get("missing",[])))
        for f in report["files"].get("missing",[]):
            print("  -",f)
        if a.full:
            print("Staging:",report.get("staging",{}).get("available",False))
    if a.fix_safe:
        for d in ["artifacts/executions","artifacts/reviews","docs/executions"]:
            (REPO_ROOT/d).mkdir(parents=True,exist_ok=True)
        print("Fix-safe: created directories")

if __name__=="__main__":
    main()
