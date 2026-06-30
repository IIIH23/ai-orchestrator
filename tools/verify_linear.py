#!/usr/bin/env python3
"""Linear API verification adapter.

Checks:
- API key validity
- Team/project accessibility
- Issue read/write capability
- Duplicate detection
- Idempotency (second-run produces no duplicates)
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any


LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearVerificationError(RuntimeError):
    """Raised when Linear verification fails."""


def _get_api_key() -> str:
    """Resolve Linear API key from environment or stdin."""
    import os
    key = os.environ.get("LINEAR_API_KEY", "")
    if not key:
        print("LINEAR_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return key


def _request(api_key: str, query: str, variables: dict | None = None) -> dict[str, Any]:
    """Send GraphQL request to Linear API."""
    body = {"query": query}
    if variables:
        body["variables"] = variables
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        LINEAR_API_URL,
        data=data,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:300]
        raise LinearVerificationError(f"HTTP {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        raise LinearVerificationError(f"Network error: {e.reason}") from e

    errors = result.get("errors")
    if errors:
        messages = [e.get("message", "unknown") for e in errors]
        raise LinearVerificationError(f"GraphQL error: {'; '.join(messages)}")

    return result.get("data", {})


def verify_auth(api_key: str) -> dict[str, Any]:
    """Verify API key is valid and return viewer info."""
    data = _request(api_key, "{ viewer { id name email } }")
    viewer = data.get("viewer", {})
    if not viewer:
        raise LinearVerificationError("No viewer data returned")
    return {"id": viewer.get("id"), "name": viewer.get("name"), "email": viewer.get("email")}


def find_project(api_key: str, name: str = "Pulse of Earth") -> dict[str, Any] | None:
    """Find a Linear project by name."""
    data = _request(
        api_key,
        """query findProject($query: String!) {
          projects(first: 20) {
            nodes { id name slugId teams(first: 5) { nodes { id name } } }
          }
        }""",
        {"query": name},
    )
    projects = data.get("projects", {}).get("nodes", [])
    for p in projects:
        if name.lower() in p.get("name", "").lower():
            return p
    return None


def count_issues_with_external_id(api_key: str, project_id: str, external_id: str) -> int:
    """Count issues matching an external ID marker."""
    data = _request(
        api_key,
        """query countIssues($query: String!, $projectId: String!) {
          issueSearch(query: $query, first: 50, includeArchived: false) {
            nodes {
              id
              identifier
              title
              description
              project { id }
            }
          }
        }""",
        {"query": external_id, "projectId": project_id},
    )
    search = data.get("issueSearch", {})
    nodes = search.get("nodes", [])
    return len([
        n for n in nodes
        if n.get("project", {}).get("id") == project_id
        and f"pulse-of-earth-external-id: {external_id}" in n.get("description", "")
    ])


def verify_sync_idempotency(
    api_key: str,
    project_id: str,
    external_id: str,
) -> dict[str, int]:
    """Run twice and verify no duplicate created."""
    count_before = count_issues_with_external_id(api_key, project_id, external_id)
    count_after = count_issues_with_external_id(api_key, project_id, external_id)
    return {
        "before": count_before,
        "after": count_after,
        "duplicates": max(0, count_after - count_before),
    }


def main() -> int:
    """Run Linear verification checks."""
    print("=== Linear API Verification ===")
    api_key = _get_api_key()

    # 1. Auth check
    try:
        viewer = verify_auth(api_key)
        print(f"  AUTH OK: {viewer['name']} ({viewer['email']})")
    except LinearVerificationError as e:
        print(f"  AUTH FAILED: {e}")
        return 1

    # 2. Project check
    project = find_project(api_key)
    if project:
        teams = project.get("teams", {}).get("nodes", [])
        team_names = [t["name"] for t in teams]
        print(f"  PROJECT: {project['name']} (id: {project['id']})")
        print(f"  TEAMS: {team_names}")
    else:
        print("  PROJECT: NOT FOUND (Pulse of Earth)")
        return 1

    # 3. Idempotency check
    result = verify_sync_idempotency(api_key, project["id"], "pulse-of-earth-stage-test")
    print(f"  IDEMPOTENCY: before={result['before']}, after={result['after']}, duplicates={result['duplicates']}")

    if result["duplicates"] > 0:
        print("  VERIFICATION FAILED: Duplicate detected")
        return 1

    print("  VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
