from __future__ import annotations

import pathlib
import subprocess
import sys
from types import SimpleNamespace

from tools.agent_runtime import collect_availability, probe_agent, resolve_route


def test_probe_uses_current_python_for_registry_python_command():
    captured = {}

    def runner(command, **kwargs):
        captured["command"] = command
        return SimpleNamespace(returncode=0, stdout="healthy\n", stderr="")

    status = probe_agent(
        {"id": "claude_code", "healthcheck": "python tools/adapter.py health"},
        runner=runner,
    )

    assert captured["command"][0] == sys.executable
    assert status.available
    assert status.detail == "healthy"


def test_probe_fails_closed_on_timeout():
    def runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 2)

    status = probe_agent(
        {"id": "codex", "healthcheck": "codex --version"},
        timeout_s=2,
        runner=runner,
    )

    assert not status.available
    assert status.detail == "healthcheck timed out after 2 seconds"


def test_probe_rejects_missing_healthcheck():
    status = probe_agent({"id": "broken"})
    assert not status.available
    assert status.detail == "healthcheck is not configured"


def test_collect_availability_returns_evidence_for_every_agent():
    def runner(command, **kwargs):
        return SimpleNamespace(
            returncode=0 if command[0] == "ok" else 1,
            stdout="ready" if command[0] == "ok" else "",
            stderr="offline" if command[0] != "ok" else "",
        )

    statuses = collect_availability(
        [
            {"id": "one", "healthcheck": "ok"},
            {"id": "two", "healthcheck": "bad"},
        ],
        runner=runner,
    )

    assert statuses.availability == {"one": True, "two": False}
    assert statuses.statuses["two"].detail == "offline"


def test_probe_runs_without_shell():
    captured = {}

    def runner(command, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    probe_agent({"id": "one", "healthcheck": "tool --version"}, runner=runner)
    assert captured["shell"] is False


def test_resolve_route_uses_observed_health_instead_of_static_flag(tmp_path):
    registry = tmp_path / "agents.yaml"
    registry.write_text(
        """
agents:
  - id: codex
    available: true
    healthcheck: codex --version
  - id: claude_code
    available: true
    healthcheck: claude --version
""",
        encoding="utf-8",
    )

    def runner(command, **kwargs):
        return SimpleNamespace(
            returncode=0 if command[0] == "codex" else 1,
            stdout="ready" if command[0] == "codex" else "",
            stderr="not authenticated" if command[0] == "claude" else "",
        )

    resolution = resolve_route(
        "implement", "high", registry_path=registry, runner=runner
    )

    assert resolution.health.availability == {
        "codex": True,
        "claude_code": False,
    }
    assert resolution.route.blocked_reason == "required Claude Code review is unavailable"
