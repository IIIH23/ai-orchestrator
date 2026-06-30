#!/usr/bin/env python3
"""Agent router — selects appropriate worker for each task type."""

from __future__ import annotations

import json
import os
import pathlib
from typing import Any

REGISTRY_PATH = pathlib.Path(__file__).parent.parent / "config" / "agent-registry.yaml"


def _load_registry() -> list[dict[str, Any]]:
    """Load agent registry (simplified YAML parsing without PyYAML)."""
    if not REGISTRY_PATH.exists():
        return []
    # Minimal YAML-like parser for our known structure
    content = REGISTRY_PATH.read_text()
    agents: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- id:"):
            if current:
                agents.append(current)
            current = {"id": stripped.split(":", 1)[1].strip()}
        elif current and stripped.startswith("type:"):
            current["type"] = stripped.split(":", 1)[1].strip()
        elif current and stripped.startswith("name:"):
            current["name"] = stripped.split(":", 1)[1].strip().strip('"')
        elif current and stripped.startswith("available:"):
            val = stripped.split(":", 1)[1].strip().lower()
            current["available"] = val in ("true", "yes")
        elif current and stripped.startswith("risk_level:"):
            current["risk_level"] = stripped.split(":", 1)[1].strip()
        elif current and stripped.startswith("cost_class:"):
            current["cost_class"] = stripped.split(":", 1)[1].strip()
    if current:
        agents.append(current)
    return agents


def select_worker(task_type: str, risk_level: str = "low") -> dict[str, Any] | None:
    """Select appropriate worker based on task type and risk level."""
    agents = _load_registry()

    # Filter available agents
    available = [a for a in agents if a.get("available", False)]

    # Routing rules
    coding_tasks = {"code", "test", "debug", "refactor", "implement", "fix", "repair"}
    review_tasks = {"review", "security", "architecture", "audit", "second_opinion"}
    research_tasks = {"research", "analysis", "discovery", "documentation"}
    integration_tasks = {"integration", "deploy", "sync", "configure"}

    if task_type in coding_tasks and risk_level in ("low", "medium"):
        # Prefer Codex for coding
        for a in available:
            if a["id"] == "codex":
                return a

    if task_type in review_tasks or risk_level in ("medium", "high"):
        # Prefer Claude Code for review/high-risk
        for a in available:
            if a["id"] == "claude_code":
                return a
        # Fallback to Codex if Claude unavailable
        for a in available:
            if a["id"] == "codex":
                return a

    if task_type in research_tasks:
        for a in available:
            if a["id"] == "owl_alpha":
                return a

    if task_type in integration_tasks:
        for a in available:
            if a["id"] == "codex":
                return a

    # Default: Hermes
    for a in available:
        if a["id"] == "hermes":
            return a

    return available[0] if available else None


def should_request_repair(task_type: str, attempt: int, max_attempts: int = 2) -> bool:
    """Determine if repair should be attempted or escalated."""
    if attempt >= max_attempts:
        return False  # Escalate to owner/independent reviewer
    return True


def should_escalate_to_owner(risk_level: str, failure_type: str) -> bool:
    """Determine if owner approval is needed."""
    if risk_level in ("medium", "high"):
        return True
    if failure_type in ("auth", "permission", "external_service", "owner_action"):
        return True
    return False


def main() -> int:
    """CLI for agent routing."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 tools/agent_router.py <task_type> [risk_level]")
        return 1

    task_type = sys.argv[1]
    risk_level = sys.argv[2] if len(sys.argv) > 2 else "low"

    worker = select_worker(task_type, risk_level)
    if worker:
        print(json.dumps({
            "task_type": task_type,
            "risk_level": risk_level,
            "selected_worker": worker["id"],
            "worker_name": worker.get("name", worker["id"]),
            "cost_class": worker.get("cost_class", "unknown"),
        }, indent=2))
        return 0
    else:
        print(json.dumps({"error": "No available worker", "task_type": task_type}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
