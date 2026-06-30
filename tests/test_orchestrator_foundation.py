from __future__ import annotations

import pathlib

import pytest

from tools.agent_registry import load_agents, select_agent
from tools.model_router import ModelCandidate, ModelFailure, is_rate_limit_failure, select_fallback
from tools.tool_registry import ToolDefinition, requires_owner_approval
from tools.verification_state import mark_completed, record_evidence


def test_model_router_detects_429_and_skips_openrouter_free() -> None:
    failure = ModelFailure(
        provider="openrouter",
        model="openrouter/owl-alpha",
        status_code=429,
        error_code=429,
        message="Rate limit exceeded: free-models-per-day-stealth.",
        retry_count=3,
        headers={"X-RateLimit-Remaining": "0"},
    )
    assert is_rate_limit_failure(failure)

    result = select_fallback(
        failure,
        [
            ModelCandidate(id="openrouter_owl_alpha", provider="openrouter", model="openrouter/owl-alpha", cost_class="free", free_tier=True),
            ModelCandidate(id="paid_codex", provider="openai-codex", model="gpt-5.5", cost_class="paid"),
        ],
    )

    assert result["route"] == "model"
    assert result["candidate"]["id"] == "paid_codex"
    assert result["skipped"] == ["openrouter_owl_alpha"]


@pytest.mark.parametrize(
    ("task_type", "agent"),
    [("code", "codex"), ("architecture", "claude"), ("review", "claude")],
)
def test_model_router_delegates_specialized_tasks(task_type: str, agent: str) -> None:
    result = select_fallback(ModelFailure(provider="openrouter", model="openrouter/owl-alpha"), [], task_type=task_type)
    assert result == {"route": "delegate", "agent": agent, "reason": result["reason"]}


def test_agent_registry_loads_required_roles() -> None:
    agents = load_agents()
    for required in {"planner", "devops", "coder_codex", "reviewer_claude", "rag_librarian", "verifier", "budget_model_router"}:
        assert required in agents
    code_agent = select_agent("code", registry=agents)
    rag_agent = select_agent("rag", registry=agents)
    assert code_agent is not None
    assert rag_agent is not None
    assert code_agent.id == "coder_codex"
    assert rag_agent.id == "rag_librarian"


def test_tool_registry_gates_secrets_cloud_and_medium_writes() -> None:
    cloudflare = ToolDefinition(
        id="cloudflare",
        name="Cloudflare",
        mcp_server="cloudflare",
        capabilities=("dns_record_update",),
        read_access=True,
        write_access=True,
        secret_access=True,
        risk_level="high",
    )
    github = ToolDefinition(
        id="github",
        name="GitHub",
        mcp_server="github",
        capabilities=("environment_secret_update",),
        read_access=True,
        write_access=True,
        secret_access=True,
        risk_level="medium",
    )
    assert requires_owner_approval(cloudflare, "dns_change")
    assert requires_owner_approval(github, "update secret")
    assert not requires_owner_approval(github, "read workflow logs")


def test_verification_state_blocks_completion_without_evidence(tmp_path: pathlib.Path) -> None:
    state_path = tmp_path / "verification_state.json"
    with pytest.raises(ValueError, match="without evidence"):
        mark_completed("task-1", path=state_path)

    state = record_evidence("task-1", "test", "pytest", "unit tests passed", path=state_path)
    assert state.status == "verified"
    completed = mark_completed("task-1", path=state_path)
    assert completed.status == "completed"
    assert completed.completed_at
