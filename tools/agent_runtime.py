#!/usr/bin/env python3
"""Runtime health adapter for agents declared in the registry."""

from __future__ import annotations

import dataclasses
import pathlib
import shlex
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from typing import Any

from tools.agent_router import REGISTRY_PATH, RouteDecision, load_registry, route_task


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclasses.dataclass(frozen=True)
class AgentHealth:
    agent_id: str
    available: bool
    detail: str
    duration_ms: int


@dataclasses.dataclass(frozen=True)
class RuntimeHealth:
    statuses: dict[str, AgentHealth]

    @property
    def availability(self) -> dict[str, bool]:
        return {
            agent_id: status.available
            for agent_id, status in self.statuses.items()
        }


@dataclasses.dataclass(frozen=True)
class RouteResolution:
    route: RouteDecision
    health: RuntimeHealth


def _health_command(value: str) -> list[str]:
    command = shlex.split(value, posix=sys.platform != "win32")
    if command and command[0].lower() in {"python", "python3"}:
        command[0] = sys.executable
    return command


def probe_agent(
    agent: dict[str, Any],
    *,
    timeout_s: int = 10,
    runner: Runner = subprocess.run,
) -> AgentHealth:
    agent_id = str(agent.get("id", "<unknown>"))
    healthcheck = agent.get("healthcheck")
    if not isinstance(healthcheck, str) or not healthcheck.strip():
        return AgentHealth(agent_id, False, "healthcheck is not configured", 0)

    command = _health_command(healthcheck)
    if not command:
        return AgentHealth(agent_id, False, "healthcheck command is empty", 0)

    started = time.monotonic()
    try:
        completed = runner(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        detail = f"healthcheck timed out after {timeout_s} seconds"
        available = False
    except OSError as exc:
        detail = f"healthcheck could not start: {exc}"
        available = False
    else:
        output = completed.stdout.strip() or completed.stderr.strip()
        detail = output.splitlines()[0] if output else f"exit code {completed.returncode}"
        available = completed.returncode == 0

    duration_ms = round((time.monotonic() - started) * 1000)
    return AgentHealth(agent_id, available, detail, duration_ms)


def collect_availability(
    agents: Sequence[dict[str, Any]],
    *,
    timeout_s: int = 10,
    runner: Runner = subprocess.run,
) -> RuntimeHealth:
    statuses = {
        str(agent.get("id", "<unknown>")): probe_agent(
            agent, timeout_s=timeout_s, runner=runner
        )
        for agent in agents
    }
    return RuntimeHealth(statuses)


def resolve_route(
    task_type: str,
    risk_level: str = "low",
    *,
    registry_path: pathlib.Path = REGISTRY_PATH,
    timeout_s: int = 10,
    runner: Runner = subprocess.run,
) -> RouteResolution:
    agents = load_registry(registry_path)
    health = collect_availability(agents, timeout_s=timeout_s, runner=runner)
    route = route_task(
        task_type,
        risk_level,
        registry_path=registry_path,
        availability=health.availability,
    )
    return RouteResolution(route=route, health=health)
