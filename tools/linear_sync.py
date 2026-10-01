#!/usr/bin/env python3
"""Synchronize numbered ROADMAP.md stages to Linear issues."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROADMAP_PATH = REPO_ROOT / "ROADMAP.md"
DEFAULT_STATE_PATH = REPO_ROOT / ".linear-sync-state.json"
LINEAR_API_URL = "https://api.linear.app/graphql"
MIN_REQUEST_INTERVAL = 2.0
MAX_ATTEMPTS = 3

STAGE_HEADING = re.compile(r"^## (?P<number>\d+)\.\s+(?P<name>.+?)\s*$")
H2_HEADING = re.compile(r"^##\s+.+$", re.MULTILINE)
FIELD_LINE = re.compile(
    r"^- (?P<field>Objectives|Success criteria|Estimated effort|Status):"
    r"\s*(?P<value>.*)$",
    re.MULTILINE,
)

WITH_ISSUE_SEARCH = """\
query withIssueSearch($query: String!, $projectId: String!) {
  issueSearch(query: $query, first: 20, includeArchived: false) {
    nodes {
      id
      identifier
      title
      description
      project { id }
    }
  }
  project(id: $projectId) {
    id
    teams(first: 10) {
      nodes {
        id
        states(first: 50) { nodes { id name } }
        labels(first: 100) { nodes { id name } }
      }
    }
    initiatives(first: 50) { nodes { id name } }
  }
}
"""

CREATE_ISSUE = """\
mutation createIssue($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue { id identifier title }
  }
}
"""

UPDATE_ISSUE = """\
mutation updateIssue($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue { id identifier title }
  }
}
"""

STAGE_CLASSIFICATION: dict[int, tuple[tuple[str, ...], str]] = {
    1: (("discovery",), "Discovery"),
    2: (("backend",), "Development"),
    3: (("architecture",), "Architecture"),
    4: (("architecture",), "Architecture"),
    5: (("backend", "devops"), "Development"),
    6: (("devops",), "Operations"),
    7: (("testing",), "Development"),
    8: (("documentation", "devops"), "Operations"),
    9: (("discovery",), "Discovery"),
}


class LinearSyncError(RuntimeError):
    """Describe a recoverable synchronization failure."""


@dataclass(frozen=True)
class Stage:
    """A numbered stage parsed from the roadmap."""

    number: int
    name: str
    objective: str
    success_criteria: str
    estimated_effort: str
    status: str


@dataclass
class _Runtime:
    api_key: str = ""
    project_id: str = ""
    team_id: str = ""
    state_ids: dict[str, str] | None = None
    label_ids: dict[str, str] | None = None
    initiative_names: set[str] | None = None
    last_request_at: float | None = None


_runtime = _Runtime()


def _read_roadmap(source: str | Path) -> str:
    """Return markdown from a path or directly supplied markdown text."""
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if "\n" not in source:
        candidate = Path(source)
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    return source


def parse_roadmap(source: str | Path) -> list[Stage]:
    """Parse numbered level-two stage headings from roadmap markdown."""
    markdown = _read_roadmap(source)
    headings = list(H2_HEADING.finditer(markdown))
    stages: list[Stage] = []

    for index, heading in enumerate(headings):
        match = STAGE_HEADING.fullmatch(heading.group(0))
        if match is None:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        body = markdown[heading.end() : end]
        fields = {
            field_match.group("field"): field_match.group("value").strip()
            for field_match in FIELD_LINE.finditer(body)
        }
        stages.append(
            Stage(
                number=int(match.group("number")),
                name=match.group("name").strip(),
                objective=fields.get("Objectives", ""),
                success_criteria=fields.get("Success criteria", ""),
                estimated_effort=fields.get("Estimated effort", ""),
                status=fields.get("Status", "Not started"),
            )
        )
    return stages


def _classification(stage_number: int) -> tuple[tuple[str, ...], str]:
    """Return issue label names and initiative name for a stage."""
    return STAGE_CLASSIFICATION.get(
        stage_number, (("documentation",), "Operations")
    )


def _priority(effort: str) -> int:
    """Map roadmap effort to a Linear priority value."""
    return {"L": 2, "M": 3, "S": 4}.get(effort.strip().upper(), 0)


def _external_id(stage_number: int) -> str:
    """Return the stable external identifier for a roadmap stage."""
    return f"pulse-of-earth-stage-{stage_number}"


def build_issue_payload(stage: Stage) -> dict[str, Any]:
    """Build a canonical logical Linear payload for *stage*."""
    labels, initiative = _classification(stage.number)
    external_id = _external_id(stage.number)
    status = stage.status or "Not started"
    state = "Done" if "done" in status.casefold() else "Todo"
    description = f"""\
<!-- pulse-of-earth-external-id: {external_id} -->

## Objective

{stage.objective or "Not specified."}

## Success criteria

{stage.success_criteria or "Not specified."}

## Estimated effort

{stage.estimated_effort or "Not specified."}

## Status

{status}

## Planning metadata

- Roadmap stage: {stage.number}
- Initiative: {initiative}
- External ID: `{external_id}`
"""
    return {
        "externalId": external_id,
        "title": f"Stage {stage.number}: {stage.name}",
        "description": description,
        "state": state,
        "priority": _priority(stage.estimated_effort),
        "labels": list(labels),
        "initiative": initiative,
    }


def load_state(path: Path) -> dict[str, dict[str, str]]:
    """Load and validate the local synchronization state."""
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LinearSyncError(f"cannot read state file {path}: {error}") from error
    if not isinstance(value, dict):
        raise LinearSyncError(f"state file {path} must contain a JSON object")

    state: dict[str, dict[str, str]] = {}
    for stage_number, entry in value.items():
        if not isinstance(stage_number, str) or not isinstance(entry, dict):
            raise LinearSyncError(f"state file {path} has an invalid entry")
        required = ("issue_id", "issue_identifier", "last_sync_hash")
        if not all(isinstance(entry.get(field), str) for field in required):
            raise LinearSyncError(f"state file {path} has an invalid stage {stage_number}")
        state[stage_number] = {field: entry[field] for field in required}
    return state


def save_state(path: Path, state: Mapping[str, Mapping[str, str]]) -> None:
    """Atomically write synchronization state as formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise LinearSyncError(f"cannot write state file {path}: {error}") from error


def _wait_for_request_slot() -> None:
    """Enforce the configured request interval."""
    if _runtime.last_request_at is not None:
        remaining = MIN_REQUEST_INTERVAL - (
            time.monotonic() - _runtime.last_request_at
        )
        if remaining > 0:
            time.sleep(remaining)


def _request(query: str, variables: Mapping[str, Any]) -> dict[str, Any]:
    """Send one GraphQL operation, retrying transient failures."""
    if not _runtime.api_key:
        raise LinearSyncError("LINEAR_API_KEY is required for synchronization")
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        _wait_for_request_slot()
        request = urllib.request.Request(
            LINEAR_API_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {_runtime.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            _runtime.last_request_at = time.monotonic()
            with urllib.request.urlopen(request, timeout=30) as response:
                raw_response = response.read()
            result = json.loads(raw_response.decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 401:
                raise LinearSyncError(
                    "Linear authorization failed; LINEAR_API_KEY is missing or invalid"
                ) from error
            if error.code == 429 and attempt < MAX_ATTEMPTS:
                retry_after = error.headers.get("Retry-After")
                try:
                    delay = max(MIN_REQUEST_INTERVAL, float(retry_after or 0))
                except ValueError:
                    delay = MIN_REQUEST_INTERVAL
                time.sleep(delay)
                continue
            raise LinearSyncError(f"Linear API returned HTTP {error.code}") from error
        except urllib.error.URLError as error:
            if attempt < MAX_ATTEMPTS:
                time.sleep(MIN_REQUEST_INTERVAL)
                continue
            raise LinearSyncError(f"Linear network error: {error.reason}") from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise LinearSyncError("Linear API returned invalid JSON") from error

        if not isinstance(result, dict):
            raise LinearSyncError("Linear API returned an invalid response")
        errors = result.get("errors")
        if errors:
            messages = [
                item.get("message", "unknown GraphQL error")
                for item in errors
                if isinstance(item, dict)
            ]
            raise LinearSyncError(
                f"Linear GraphQL error: {'; '.join(messages) or 'unknown error'}"
            )
        data = result.get("data")
        if not isinstance(data, dict):
            raise LinearSyncError("Linear API response has no data object")
        return data

    raise LinearSyncError("Linear request failed after retries")


def _capture_project_metadata(project: Any) -> None:
    """Validate and cache IDs needed to create and update issues."""
    if not isinstance(project, dict) or project.get("id") != _runtime.project_id:
        raise LinearSyncError(f"Linear project {_runtime.project_id!r} was not found")
    teams = project.get("teams", {}).get("nodes", [])
    if not isinstance(teams, list) or len(teams) != 1 or not isinstance(teams[0], dict):
        raise LinearSyncError("the Linear project must have exactly one team")
    team = teams[0]
    _runtime.team_id = str(team.get("id", ""))
    _runtime.state_ids = {
        item["name"].casefold(): item["id"]
        for item in team.get("states", {}).get("nodes", [])
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("name"), str)
    }
    _runtime.label_ids = {
        item["name"].casefold(): item["id"]
        for item in team.get("labels", {}).get("nodes", [])
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("name"), str)
    }
    _runtime.initiative_names = {
        item["name"].casefold()
        for item in project.get("initiatives", {}).get("nodes", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if not _runtime.team_id:
        raise LinearSyncError("the Linear project team has no ID")


def search_existing_issue(title: str) -> dict[str, str] | None:
    """Search for an issue by deterministic external ID.

    ``title`` is retained as the public argument name required by the Stage 4
    interface; callers pass the external ID, not the human-readable title.
    """
    data = _request(
        WITH_ISSUE_SEARCH,
        {"query": title, "projectId": _runtime.project_id},
    )
    _capture_project_metadata(data.get("project"))
    marker = f"<!-- pulse-of-earth-external-id: {title} -->"
    search = data.get("issueSearch", {})
    nodes = search.get("nodes", []) if isinstance(search, dict) else []
    for issue in nodes:
        if not isinstance(issue, dict):
            continue
        project = issue.get("project")
        description = issue.get("description")
        if (
            isinstance(project, dict)
            and project.get("id") == _runtime.project_id
            and isinstance(description, str)
            and marker in description
            and isinstance(issue.get("id"), str)
        ):
            return {
                "id": issue["id"],
                "identifier": str(issue.get("identifier", "")),
                "title": str(issue.get("title", "")),
            }
    return None


def _api_payload(payload: Mapping[str, Any], *, creating: bool) -> dict[str, Any]:
    """Resolve a logical payload to Linear GraphQL input."""
    if (
        _runtime.state_ids is None
        or _runtime.label_ids is None
        or _runtime.initiative_names is None
    ):
        raise LinearSyncError("Linear project metadata has not been loaded")
    state_name = str(payload["state"])
    state_id = _runtime.state_ids.get(state_name.casefold())
    if state_id is None:
        raise LinearSyncError(f"Linear workflow state {state_name!r} was not found")

    label_ids: list[str] = []
    for label in payload["labels"]:
        label_id = _runtime.label_ids.get(str(label).casefold())
        if label_id is None:
            raise LinearSyncError(f"Linear issue label {label!r} was not found")
        label_ids.append(label_id)

    initiative = str(payload["initiative"])
    if initiative.casefold() not in _runtime.initiative_names:
        raise LinearSyncError(
            f"Linear project is not associated with initiative {initiative!r}"
        )

    result = {
        "title": payload["title"],
        "description": payload["description"],
        "priority": payload["priority"],
        "projectId": _runtime.project_id,
        "stateId": state_id,
        "labelIds": label_ids,
    }
    if creating:
        result["teamId"] = _runtime.team_id
    return result


def _mutation_issue(data: Mapping[str, Any], field: str) -> dict[str, str]:
    """Validate and return an issue from a mutation response."""
    mutation = data.get(field)
    if not isinstance(mutation, dict) or mutation.get("success") is not True:
        raise LinearSyncError(f"Linear {field} mutation was unsuccessful")
    issue = mutation.get("issue")
    if not isinstance(issue, dict) or not isinstance(issue.get("id"), str):
        raise LinearSyncError(f"Linear {field} response has no issue")
    return {
        "id": issue["id"],
        "identifier": str(issue.get("identifier", "")),
        "title": str(issue.get("title", "")),
    }


def create_issue(payload: Mapping[str, Any]) -> dict[str, str]:
    """Create and return one Linear issue."""
    data = _request(CREATE_ISSUE, {"input": _api_payload(payload, creating=True)})
    return _mutation_issue(data, "issueCreate")


def update_issue(issue_id: str, payload: Mapping[str, Any]) -> dict[str, str]:
    """Update and return one Linear issue."""
    data = _request(
        UPDATE_ISSUE,
        {"id": issue_id, "input": _api_payload(payload, creating=False)},
    )
    return _mutation_issue(data, "issueUpdate")


def _payload_hash(payload: Mapping[str, Any]) -> str:
    """Return a stable digest for a logical issue payload."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sync(
    roadmap_path: str | Path,
    *,
    api_key: str | None = None,
    project_id: str | None = None,
    state_file: str | Path = DEFAULT_STATE_PATH,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Synchronize roadmap stages and return a JSON-serializable summary."""
    stages = parse_roadmap(roadmap_path)
    if not stages:
        raise LinearSyncError("roadmap contains no numbered stage headings")
    payloads = [(stage, build_issue_payload(stage)) for stage in stages]

    if dry_run:
        return {
            "dry_run": True,
            "actions": [
                {
                    "stage_number": stage.number,
                    "action": "plan",
                    "payload": payload,
                }
                for stage, payload in payloads
            ],
        }

    resolved_api_key = api_key if api_key is not None else os.environ.get(
        "LINEAR_API_KEY", ""
    )
    if not resolved_api_key:
        raise LinearSyncError("LINEAR_API_KEY is required for synchronization")
    if not project_id:
        raise LinearSyncError("--project-id is required for synchronization")

    state_path = Path(state_file)
    state = load_state(state_path)
    _runtime.api_key = resolved_api_key
    _runtime.project_id = project_id
    _runtime.team_id = ""
    _runtime.state_ids = None
    _runtime.label_ids = None
    _runtime.initiative_names = None
    _runtime.last_request_at = None

    actions: list[dict[str, Any]] = []
    for stage, payload in payloads:
        existing = search_existing_issue(str(payload["externalId"]))
        if existing is None:
            issue = create_issue(payload)
            action = "created"
        else:
            issue = update_issue(existing["id"], payload)
            action = "updated"
        state[str(stage.number)] = {
            "issue_id": issue["id"],
            "issue_identifier": issue["identifier"],
            "last_sync_hash": _payload_hash(payload),
        }
        actions.append(
            {
                "stage_number": stage.number,
                "action": action,
                "issue_id": issue["id"],
                "issue_identifier": issue["identifier"],
            }
        )

    save_state(state_path, state)
    return {"dry_run": False, "actions": actions, "state_file": str(state_path)}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roadmap",
        nargs="?",
        type=Path,
        default=DEFAULT_ROADMAP_PATH,
        help="roadmap file (default: ROADMAP.md in the repository)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the issue plan without API calls or state writes",
    )
    parser.add_argument("--api-key", help="override LINEAR_API_KEY")
    parser.add_argument(
        "--project-id",
        help="Linear project UUID (required unless --dry-run)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="idempotency state file (default: .linear-sync-state.json)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run synchronization and return a process exit code."""
    args = parse_args(argv)
    try:
        result = sync(
            args.roadmap,
            api_key=args.api_key,
            project_id=args.project_id,
            state_file=args.state_file,
            dry_run=args.dry_run,
        )
    except (LinearSyncError, OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, sort_keys=True))
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
