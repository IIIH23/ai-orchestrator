#!/usr/bin/env python3
"""External verification orchestrator.

Runs all verification adapters and produces a unified report.
"""

from __future__ import annotations

import json
import sys
import pathlib
import datetime
from typing import Any

REPO_ROOT = pathlib.Path(__file__).parent.parent
EXECUTIONS_DIR = REPO_ROOT / "artifacts" / "executions"


def run_verification(name: str, script: str) -> dict[str, Any]:
    """Run a verification script and capture results."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / script)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "name": name,
        "script": script,
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip()[:500] if result.stderr else "",
        "passed": result.returncode == 0,
    }


def main() -> int:
    """Run all verifications and produce report."""
    EXECUTIONS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results = []

    print("=" * 60)
    print("AUTONOMOUS VERIFICATION LOOP — EXTERNAL EVIDENCE")
    print("=" * 60)
    print(f"Timestamp: {timestamp}")
    print()

    # 1. GitHub
    results.append(run_verification("GitHub", "tools/verify_github.py"))

    # 2. Telegram
    results.append(run_verification("Telegram", "tools/verify_telegram.py"))

    # 3. Staging
    results.append(run_verification("Staging", "tools/verify_staging.py"))

    # 4. Linear (may fail if key revoked)
    results.append(run_verification("Linear", "tools/verify_linear.py"))

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['name']} (exit={r['exit_code']})")
        if not r["passed"]:
            all_passed = False
            if r["stderr"]:
                print(f"         stderr: {r['stderr'][:100]}")

    # Save report
    report = {
        "timestamp": timestamp,
        "overall_passed": all_passed,
        "results": results,
    }

    report_path = EXECUTIONS_DIR / f"verification-{datetime.datetime.now().strftime('%Y%m%dT%H%M%SZ')}.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nReport saved: {report_path}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
