from __future__ import annotations

import pathlib

import pytest

from tools.agent_router import load_registry, route_task


REGISTRY = """
agents:
  - id: hermes
    available: true
  - id: codex
    available: true
  - id: claude_code
    available: true
  - id: owl_alpha
    available: true
"""


@pytest.fixture
def registry(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "agents.yaml"
    path.write_text(REGISTRY, encoding="utf-8")
    return path


def test_low_risk_implementation_routes_to_codex(registry):
    decision = route_task("implement", "low", registry_path=registry)
    assert decision.primary["id"] == "codex"
    assert decision.reviewers == ()
    assert not decision.requires_owner_approval


def test_medium_risk_implementation_requires_owner_but_avoids_unneeded_review(registry):
    decision = route_task("implement", "medium", registry_path=registry)
    assert decision.primary["id"] == "codex"
    assert decision.reviewers == ()
    assert decision.requires_owner_approval


def test_high_risk_work_is_blocked_when_claude_is_unavailable(registry):
    decision = route_task(
        "implement",
        "high",
        registry_path=registry,
        availability={"claude_code": False},
    )
    assert decision.primary["id"] == "codex"
    assert decision.blocked_reason == "required Claude Code review is unavailable"


def test_security_review_routes_directly_to_claude(registry):
    decision = route_task("security", "low", registry_path=registry)
    assert decision.primary["id"] == "claude_code"
    assert decision.blocked_reason is None


def test_research_routes_to_owl(registry):
    assert route_task("research", registry_path=registry).primary["id"] == "owl_alpha"


def test_invalid_risk_is_rejected(registry):
    with pytest.raises(ValueError, match="risk_level"):
        route_task("code", "critical", registry_path=registry)


def test_duplicate_registry_ids_are_rejected(tmp_path):
    path = tmp_path / "duplicate.yaml"
    path.write_text(
        "agents:\n  - id: codex\n  - id: codex\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_registry(path)
