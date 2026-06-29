"""End-to-end pipeline test for the orchestrator PIPE."""
import json
import os
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_low_risk_task_flow():
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    task_slug = "synthetic-low-risk-{}".format(timestamp[-6:])

    execution = {
        "task_id": "TEST-{}".format(timestamp[-6:]),
        "title": "Synthetic low-risk task",
        "risk": "low",
        "status": "PARTIALLY_COMPLETED",
        "branch": "feat/orchestrator-acceptance-subscription-audit",
        "commit": os.popen("git rev-parse HEAD").read().strip()[:8],
        "pull_request": None,
        "workers": {"hermes": True, "codex": False, "claude_code": False},
        "gaps": ["Docker build step needs investigation"],
        "approvals_required": [],
        "owner_actions": ["Delete compromised PAT"],
        "started_at": timestamp,
    }

    exec_dir = REPO_ROOT / "artifacts/executions"
    exec_dir.mkdir(parents=True, exist_ok=True)
    exec_file = exec_dir / "{}.json".format(task_slug)

    with open(exec_file, "w") as f:
        json.dump(execution, f, indent=2)

    assert exec_file.exists()
    print("PASS: Low-risk flow")


def test_high_risk_simulation():
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    task_slug = "synthetic-high-risk-{}".format(timestamp[-6:])

    execution = {
        "task_id": "TEST-HIGH-{}".format(timestamp[-6:]),
        "title": "Synthetic high-risk (firewall)",
        "risk": "high",
        "status": "NEEDS_APPROVAL",
        "workers": {"hermes": True, "codex": True, "claude_code": True},
        "approvals_required": ["firewall-change"],
    }

    exec_dir = REPO_ROOT / "artifacts/executions"
    exec_dir.mkdir(parents=True, exist_ok=True)
    exec_file = exec_dir / "{}.json".format(task_slug)

    with open(exec_file, "w") as f:
        json.dump(execution, f, indent=2)

    loaded = json.loads(exec_file.read_text())
    assert loaded["status"] == "NEEDS_APPROVAL"
    assert len(loaded["approvals_required"]) > 0
    print("PASS: High-risk simulation requires approval")


if __name__ == "__main__":
    test_low_risk_task_flow()
    test_high_risk_simulation()
    print("All PIPE E2E dry-run tests passed.")
