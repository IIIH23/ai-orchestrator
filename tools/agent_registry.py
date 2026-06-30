#!/usr/bin/env python3
"""Agent registry for the Pulse of Earth autonomous orchestrator."""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "config" / "agent-registry.yaml"


@dataclasses.dataclass(frozen=True)
class AgentDefinition:
    id: str
    name: str
    role: str
    capabilities: tuple[str, ...]
    risk_level: str = "low"
    cost_class: str = "standard"
    available: bool = True
    fallback: str | None = None


def _parse_registry_blocks(path: pathlib.Path = REGISTRY_PATH) -> list[dict[str, Any]]:
    """Small YAML subset parser for the checked-in registry shape."""

    if not path.exists():
        return []
    agents: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    active_list: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- id:"):
            if current is not None:
                agents.append(current)
            current = {"id": stripped.split(":", 1)[1].strip().strip('"'), "capabilities": []}
            active_list = None
            continue
        if current is None:
            continue
        if stripped.endswith(":"):
            key = stripped[:-1]
            active_list = key if key in {"capabilities", "allowed_actions", "forbidden_actions"} else None
            if active_list:
                current.setdefault(active_list, [])
            continue
        if active_list and stripped.startswith("-"):
            current.setdefault(active_list, []).append(stripped[1:].strip().strip('"'))
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            active_list = None
            value = value.strip().strip('"')
            if value.lower() in {"true", "false"}:
                current[key] = value.lower() == "true"
            elif value.lower() == "null":
                current[key] = None
            else:
                current[key] = value
    if current is not None:
        agents.append(current)
    return agents


def load_agents(path: pathlib.Path = REGISTRY_PATH) -> dict[str, AgentDefinition]:
    agents: dict[str, AgentDefinition] = {}
    for item in _parse_registry_blocks(path):
        agent_id = str(item.get("id", "")).strip()
        if not agent_id:
            continue
        agents[agent_id] = AgentDefinition(
            id=agent_id,
            name=str(item.get("name", agent_id)),
            role=str(item.get("role", item.get("type", "worker"))),
            capabilities=tuple(str(capability) for capability in item.get("capabilities", [])),
            risk_level=str(item.get("risk_level", "low")),
            cost_class=str(item.get("cost_class", "standard")),
            available=bool(item.get("available", True)),
            fallback=item.get("fallback"),
        )
    return agents


TASK_ROUTES = {
    "plan": ("planner", "hermes"),
    "planning": ("planner", "hermes"),
    "devops": ("devops", "codex", "hermes"),
    "code": ("coder_codex", "codex", "hermes"),
    "coding": ("coder_codex", "codex", "hermes"),
    "review": ("reviewer_claude", "claude_code", "hermes"),
    "architecture": ("reviewer_claude", "claude_code", "hermes"),
    "rag": ("rag_librarian", "hermes"),
    "verify": ("verifier", "hermes"),
    "budget": ("budget_model_router", "hermes"),
}


def select_agent(task_type: str, *, registry: dict[str, AgentDefinition] | None = None) -> AgentDefinition | None:
    registry = registry or load_agents()
    for agent_id in TASK_ROUTES.get(task_type.lower(), ("hermes",)):
        agent = registry.get(agent_id)
        if agent and agent.available:
            return agent
    return next((agent for agent in registry.values() if agent.available), None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the Pulse of Earth agent registry")
    parser.add_argument("task_type", nargs="?", default="plan")
    args = parser.parse_args()
    agent = select_agent(args.task_type)
    print(json.dumps(dataclasses.asdict(agent) if agent else {"error": "no_available_agent"}, indent=2))
    return 0 if agent else 1


if __name__ == "__main__":
    raise SystemExit(main())
