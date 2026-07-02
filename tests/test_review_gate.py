from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from tools.claude_code_adapter import ClaudeResult
from tools.agent_runtime import AgentHealth, RuntimeHealth
from tools.review_gate import ReviewGateError, main, run_review_gate


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


def claude_result(payload: object) -> ClaudeResult:
    return ClaudeResult(
        success=True,
        result=json.dumps(payload),
        session_id="session-42",
        cost_usd=0.03,
        duration_ms=500,
        num_turns=2,
        subtype="success",
    )


def test_low_risk_implementation_skips_review(registry, tmp_path):
    called = False

    def reviewer(request):
        nonlocal called
        called = True

    result = run_review_gate(
        "implement",
        "low",
        "Review changes",
        tmp_path,
        registry_path=registry,
        availability={"codex": True, "claude_code": True},
        reviewer=reviewer,
    )

    assert result.status == "not_required"
    assert result.verdict is None
    assert not called


def test_high_risk_implementation_returns_structured_verdict(registry, tmp_path):
    captured = {}

    def reviewer(request):
        captured["request"] = request
        return claude_result(
            {
                "verdict": "request_changes",
                "summary": "Unsafe migration",
                "findings": ["Rollback is missing"],
            }
        )

    result = run_review_gate(
        "implement",
        "high",
        "Review migration",
        tmp_path,
        registry_path=registry,
        availability={"codex": True, "claude_code": True},
        reviewer=reviewer,
    )

    assert captured["request"].mode == "review"
    assert result.status == "completed"
    assert result.verdict.value == "request_changes"
    assert result.findings == ("Rollback is missing",)
    assert result.session_id == "session-42"


def test_required_review_fails_closed_when_claude_is_unavailable(registry, tmp_path):
    with pytest.raises(ReviewGateError, match="required Claude Code review"):
        run_review_gate(
            "deploy",
            "high",
            "Review deployment",
            tmp_path,
            registry_path=registry,
            availability={"codex": True, "claude_code": False},
        )


def test_gate_uses_runtime_availability_provider_when_not_supplied(registry, tmp_path):
    captured = {}

    def availability_provider(path):
        captured["path"] = path
        return {"claude_code": False}

    with pytest.raises(ReviewGateError, match="required Claude Code review"):
        run_review_gate(
            "security",
            "high",
            "Review security",
            tmp_path,
            registry_path=registry,
            availability_provider=availability_provider,
        )

    assert captured["path"] == registry


def test_gate_preserves_runtime_health_evidence(registry, tmp_path):
    health = RuntimeHealth(
        {
            "codex": AgentHealth("codex", True, "ready", 4),
            "claude_code": AgentHealth("claude_code", True, "ready", 5),
        }
    )
    result = run_review_gate(
        "implement",
        "low",
        "No review needed",
        tmp_path,
        registry_path=registry,
        availability_provider=lambda path: health,
    )
    assert result.health is health


def test_cli_fails_closed_with_json_error(capsys, tmp_path):
    def failing_gate(*args, **kwargs):
        raise ReviewGateError("required reviewer unavailable")

    exit_code = main(
        ["security", "high", "--prompt", "Review security", "--cwd", str(tmp_path)],
        gate=failing_gate,
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().err) == {
        "status": "error",
        "error": "required reviewer unavailable",
    }


def test_direct_script_entrypoint_can_load_tools_package():
    repository = pathlib.Path(__file__).parent.parent
    completed = subprocess.run(
        [sys.executable, "tools/review_gate.py", "--help"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "ModuleNotFoundError" not in completed.stderr


@pytest.mark.parametrize("verdict", ["approve", "request_changes", "blocked"])
def test_accepts_only_defined_verdicts(verdict, registry, tmp_path):
    result = run_review_gate(
        "security",
        "high",
        "Review security",
        tmp_path,
        registry_path=registry,
        availability={"claude_code": True},
        reviewer=lambda request: claude_result(
            {"verdict": verdict, "summary": "Checked", "findings": []}
        ),
    )
    assert result.verdict.value == verdict


@pytest.mark.parametrize(
    "payload",
    [
        "not JSON",
        json.dumps({"verdict": "maybe", "summary": "Unknown", "findings": []}),
        json.dumps({"verdict": "approve", "findings": []}),
        json.dumps({"verdict": "approve", "summary": "OK", "findings": "none"}),
    ],
)
def test_malformed_verdict_fails_closed(payload, registry, tmp_path):
    result = ClaudeResult(True, payload, None, None, None, None, "success")
    with pytest.raises(ReviewGateError, match="verdict"):
        run_review_gate(
            "security",
            "high",
            "Review security",
            tmp_path,
            registry_path=registry,
            availability={"claude_code": True},
            reviewer=lambda request: result,
        )
