#!/usr/bin/env python3
"""MCP-style tool registry and risk gate for Pulse of Earth."""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "config" / "tool-registry.yaml"


@dataclasses.dataclass(frozen=True)
class ToolDefinition:
    id: str
    name: str
    mcp_server: str
    capabilities: tuple[str, ...]
    read_access: bool
    write_access: bool
    secret_access: bool
    risk_level: str
    healthcheck: str | None = None


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "on"}


def _parse_blocks(path: pathlib.Path = REGISTRY_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    tools: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    active_list: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- id:"):
            if current is not None:
                tools.append(current)
            current = {"id": stripped.split(":", 1)[1].strip().strip('"'), "capabilities": []}
            active_list = None
            continue
        if current is None:
            continue
        if stripped.endswith(":"):
            key = stripped[:-1]
            active_list = key if key == "capabilities" else None
            if active_list:
                current.setdefault(active_list, [])
            continue
        if active_list and stripped.startswith("-"):
            current.setdefault(active_list, []).append(stripped[1:].strip().strip('"'))
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            active_list = None
            current[key] = value.strip().strip('"')
    if current is not None:
        tools.append(current)
    return tools


def load_tools(path: pathlib.Path = REGISTRY_PATH) -> dict[str, ToolDefinition]:
    loaded: dict[str, ToolDefinition] = {}
    for item in _parse_blocks(path):
        tool_id = str(item.get("id", "")).strip()
        if not tool_id:
            continue
        loaded[tool_id] = ToolDefinition(
            id=tool_id,
            name=str(item.get("name", tool_id)),
            mcp_server=str(item.get("mcp_server", tool_id)),
            capabilities=tuple(str(capability) for capability in item.get("capabilities", [])),
            read_access=_parse_bool(item.get("read_access", "false")),
            write_access=_parse_bool(item.get("write_access", "false")),
            secret_access=_parse_bool(item.get("secret_access", "false")),
            risk_level=str(item.get("risk_level", "low")),
            healthcheck=item.get("healthcheck"),
        )
    return loaded


def requires_owner_approval(tool: ToolDefinition, operation: str) -> bool:
    """Return true if operation must be stopped for explicit owner approval."""

    op = operation.lower()
    if tool.secret_access and any(marker in op for marker in ("secret", "token", "credential", "key")):
        return True
    if tool.risk_level in {"high", "critical"}:
        return True
    if tool.risk_level == "medium" and any(marker in op for marker in ("write", "create", "update", "delete", "deploy", "apply")):
        return True
    if any(marker in op for marker in ("paid", "hetzner_create", "dns_change", "production_deploy")):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Query tool registry approval requirements")
    parser.add_argument("tool_id")
    parser.add_argument("operation", nargs="?", default="read")
    args = parser.parse_args()
    tool = load_tools().get(args.tool_id)
    if not tool:
        print(json.dumps({"error": "unknown_tool", "tool_id": args.tool_id}, indent=2))
        return 1
    print(json.dumps({"tool": dataclasses.asdict(tool), "approval_required": requires_owner_approval(tool, args.operation)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
