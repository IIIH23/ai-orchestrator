#!/usr/bin/env python3
"""Capability-aware agent routing with explicit high-risk review gates."""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
from collections.abc import Mapping, Sequence
from typing import Any

import yaml

REGISTRY_PATH = pathlib.Path(__file__).parent.parent / "config" / "agent-registry.yaml"

CODING_TASKS = {"code", "test", "debug", "refactor", "implement", "fix", "repair"}
REVIEW_TASKS = {
    "review",
    "security",
    "architecture",
    "audit",
    "infrastructure",
    "permission",
    "rollback",
    "database",
    "second_opinion",
}
RESEARCH_TASKS = {"research", "analysis", "discovery", "documentation", "knowledge"}
INTEGRATION_TASKS = {"integration", "deploy", "sync", "configure"}
MANDATORY_CLAUDE_REVIEW = {
    "security",
    "architecture",
    "infrastructure",
    "permission",
    "rollback",
    "database",
    "deploy",
}


@dataclasses.dataclass(frozen=True)
class RouteDecision:
    task_type: str
    risk_level: str
    primary: dict[str, Any] | None
    reviewers: tuple[dict[str, Any], ...]
    requires_owner_approval: bool
    blocked_reason: str | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "risk_level": self.risk_level,
            "primary": self.primary,
            "reviewers": list(self.reviewers),
            "requires_owner_approval": self.requires_owner_approval,
            "blocked_reason": self.blocked_reason,
            "reason": self.reason,
        }


def load_registry(path: pathlib.Path = REGISTRY_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    agents = payload.get("agents", [])
    if not isinstance(agents, list):
        raise ValueError("agent registry must contain an agents list")
    ids = [agent.get("id") for agent in agents if isinstance(agent, dict)]
    if len(ids) != len(set(ids)):
        raise ValueError("agent registry contains duplicate ids")
    return agents


def _is_available(
    agent: Mapping[str, Any] | None, availability: Mapping[str, bool] | None
) -> bool:
    if not agent:
        return False
    agent_id = str(agent.get("id"))
    if availability is not None and agent_id in availability:
        return availability[agent_id]
    return bool(agent.get("available", False))


def route_task(
    task_type: str,
    risk_level: str = "low",
    *,
    registry_path: pathlib.Path = REGISTRY_PATH,
    availability: Mapping[str, bool] | None = None,
) -> RouteDecision:
    task_type = task_type.strip().lower()
    risk_level = risk_level.strip().lower()
    if risk_level not in {"low", "medium", "high"}:
        raise ValueError("risk_level must be low, medium, or high")

    agents = {agent["id"]: agent for agent in load_registry(registry_path)}

    if task_type in REVIEW_TASKS:
        primary_id, reason = "claude_code", "independent review task"
    elif task_type in CODING_TASKS or task_type in INTEGRATION_TASKS:
        primary_id, reason = "codex", "implementation or integration task"
    elif task_type in RESEARCH_TASKS:
        primary_id, reason = "owl_alpha", "research or knowledge task"
    else:
        primary_id, reason = "hermes", "orchestration fallback"

    primary = agents.get(primary_id)
    reviewers: list[dict[str, Any]] = []
    claude = agents.get("claude_code")
    claude_required = (
        risk_level == "high"
        or task_type in MANDATORY_CLAUDE_REVIEW
    )

    blocked_reason = None
    if not _is_available(primary, availability):
        blocked_reason = f"primary agent {primary_id} is unavailable"
        primary = None

    if claude_required and primary_id != "claude_code":
        if _is_available(claude, availability):
            reviewers.append(claude)
        else:
            blocked_reason = "required Claude Code review is unavailable"
    elif primary_id == "claude_code" and not _is_available(claude, availability):
        blocked_reason = "required Claude Code review is unavailable"

    return RouteDecision(
        task_type=task_type,
        risk_level=risk_level,
        primary=primary,
        reviewers=tuple(reviewers),
        requires_owner_approval=risk_level in {"medium", "high"},
        blocked_reason=blocked_reason,
        reason=reason,
    )


def select_worker(task_type: str, risk_level: str = "low") -> dict[str, Any] | None:
    """Backward-compatible primary-agent selector."""
    return route_task(task_type, risk_level).primary


def should_request_repair(task_type: str, attempt: int, max_attempts: int = 2) -> bool:
    return attempt < max_attempts


def should_escalate_to_owner(risk_level: str, failure_type: str) -> bool:
    return risk_level in {"medium", "high"} or failure_type in {
        "auth",
        "permission",
        "external_service",
        "owner_action",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_type")
    parser.add_argument("risk_level", nargs="?", default="low")
    args = parser.parse_args(argv)
    try:
        decision = route_task(args.task_type, args.risk_level)
    except (ValueError, yaml.YAMLError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    print(json.dumps(decision.as_dict(), indent=2))
    return 1 if decision.blocked_reason else 0


if __name__ == "__main__":
    raise SystemExit(main())
