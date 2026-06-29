#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path

def verify_execution(record_path):
    record = json.loads(Path(record_path).read_text())
    errors = []
    for field in ["task_id","title","risk","status"]:
        if field not in record:
  errors.append(f"Missing field: {field}")
    if record.get("status") == "COMPLETED":
        checks = record.get("checks", {})
        if checks.get("unit_tests") != "pass":
            errors.append("COMPLETED but unit_tests not pass")
        if not record.get("commit"):
            errors.append("COMPLETED but no commit")
    gaps = record.get("gaps", [])
    if gaps:
        print(f"WARNING: {len(gaps)} unresolved gaps")
    if errors:
 print("VERIFICATION FAILED:")
     for e in errors:
    print(f"  - {e}")
        return 1
    print("VERIFICATION PASSED")
    return 0

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--execution", required=True)
    a = p.parse_args()
    sys.exit(verify_execution(a.execution))

if __name__ == "__main__":
    main()
