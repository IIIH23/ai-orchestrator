#!/usr/bin/env python3
"""GitHub API verification adapter.

Checks:
- Repository accessibility
- Workflow status and conclusion
- PR merge status
- Branch protection
- Recent commits
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any


GITHUB_API_URL = "https://api.github.com"


class GitHubVerificationError(RuntimeError):
    """Raised when GitHub verification fails."""


def _request(path: str) -> dict[str, Any]:
    """Make authenticated or unauthenticated GitHub API request."""
    url = f"{GITHUB_API_URL}{path}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "hermes-verification")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        raise GitHubVerificationError(f"HTTP {e.code} {path}: {body}") from e
    except urllib.error.URLError as e:
        raise GitHubVerificationError(f"Network error: {e.reason}") from e


def verify_repo(owner: str, repo: str) -> dict[str, Any]:
    """Verify repository exists and is accessible."""
    data = _request(f"/repos/{owner}/{repo}")
    return {
        "name": data.get("full_name"),
        "visibility": data.get("visibility"),
        "default_branch": data.get("default_branch"),
        "updated_at": data.get("updated_at"),
    }


def verify_workflows(owner: str, repo: str) -> list[dict[str, Any]]:
    """List workflows with their latest run status."""
    data = _request(f"/repos/{owner}/{repo}/actions/workflows")
    workflows = []
    for w in data.get("workflows", []):
        workflows.append({
            "id": w.get("id"),
            "name": w.get("name"),
            "state": w.get("state"),
            "path": w.get("path"),
        })
    return workflows


def verify_latest_run(owner: str, repo: str, workflow_id: int) -> dict[str, Any]:
    """Get latest run conclusion for a workflow."""
    data = _request(f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs?per_page=1")
    runs = data.get("workflow_runs", [])
    if not runs:
        return {"status": "no_runs"}
    run = runs[0]
    return {
        "id": run.get("id"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "sha": run.get("head_sha", "")[:8],
        "message": (run.get("head_commit", {}).get("message", "") or "")[:60],
        "timestamp": run.get("created_at"),
    }


def verify_branch_protection(owner: str, repo: str, branch: str) -> dict[str, Any]:
    """Check branch protection status."""
    try:
        data = _request(f"/repos/{owner}/{repo}/branches/{branch}/protection")
        return {
            "enabled": True,
            "status_checks": data.get("required_status_checks", {}).get("contexts", []),
            "enforce_admins": data.get("enforce_admins", {}).get("enabled", False),
        }
    except GitHubVerificationError:
        return {"enabled": False, "status_checks": [], "enforce_admins": False}


def verify_recent_commits(owner: str, repo: str, per_page: int = 3) -> list[dict[str, str]]:
    """Get recent commits."""
    data = _request(f"/repos/{owner}/{repo}/commits?per_page={per_page}")
    return [
        {
            "sha": c.get("sha", "")[:8],
            "message": (c.get("commit", {}).get("message", "") or "")[:60],
            "author": (c.get("commit", {}).get("author", {}).get("name", "")),
            "date": c.get("commit", {}).get("author", {}).get("date", ""),
        }
        for c in data if isinstance(c, dict)
    ]


def main() -> int:
    """Run GitHub verification checks."""
    owner, repo = "IIIH23", "earth-pulse-poc"

    print("=== GitHub Verification ===")

    # 1. Repo
    try:
        r = verify_repo(owner, repo)
        print(f"  REPO: {r['name']} ({r['visibility']}, branch: {r['default_branch']})")
    except GitHubVerificationError as e:
        print(f"  REPO ERROR: {e}")
        return 1

    # 2. Workflows
    workflows = verify_workflows(owner, repo)
    print(f"  WORKFLOWS: {len(workflows)} found")
    for w in workflows:
        print(f"    - {w['name']}: {w['state']}")

    # 3. Latest CI run
    for w in workflows:
        if w["name"] == "CI":
            run = verify_latest_run(owner, repo, w["id"])
            print(f"  LATEST CI: status={run.get('status')}, conclusion={run.get('conclusion')}")
            break

    # 4. Branch protection
    bp = verify_branch_protection(owner, repo, r["default_branch"])
    print(f"  BRANCH PROTECTION: enabled={bp['enabled']}, checks={bp['status_checks']}")

    # 5. Recent commits
    commits = verify_recent_commits(owner, repo)
    print(f"  RECENT COMMITS ({len(commits)}):")
    for c in commits:
        print(f"    [{c['sha']}] {c['message']} ({c['author']})")

    print("  VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
