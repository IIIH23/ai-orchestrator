from __future__ import annotations

import json
import pathlib
import subprocess
from types import SimpleNamespace

import pytest

from tools.claude_code_adapter import (
    ClaudeCodeError,
    ClaudeRequest,
    append_audit_event,
    build_command,
    parse_result,
    run_claude,
    sanitized_environment,
)


def request(tmp_path: pathlib.Path, **overrides: object) -> ClaudeRequest:
    values = {"prompt": "Review this diff", "cwd": tmp_path}
    values.update(overrides)
    return ClaudeRequest(**values)


def success_payload() -> str:
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "No critical findings.",
            "session_id": "session-1",
            "total_cost_usd": 0.02,
            "duration_ms": 250,
            "num_turns": 2,
        }
    )


def test_review_command_is_read_only_and_prompt_is_not_an_argument(tmp_path):
    item = request(tmp_path)
    command = build_command(item, "claude")

    assert item.prompt not in command
    assert command[command.index("--permission-mode") + 1] == "plan"
    assert "Read" in command
    assert "Bash" in command
    assert command[command.index("--disallowedTools") + 1 :] == [
        "Edit",
        "Write",
        "Bash",
    ]


def test_edit_command_denies_remote_and_destructive_operations(tmp_path):
    command = build_command(request(tmp_path, mode="edit"), "claude")
    assert "Bash(git push:*)" in command
    assert "Bash(git reset:*)" in command
    assert "Bash(rm:*)" in command
    assert "--dangerously-skip-permissions" not in command


def test_run_uses_stdin_sanitized_environment_and_timeout(monkeypatch, tmp_path):
    captured = {}

    def fake_run(command, **kwargs):
        captured.update(command=command, **kwargs)
        return SimpleNamespace(stdout=success_payload(), stderr="", returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = run_claude(
        request(tmp_path, timeout_s=17),
        executable="claude",
        environment={
            "PATH": "bin",
            "ANTHROPIC_API_KEY": "anthropic",
            "GITHUB_TOKEN": "remove-me",
        },
    )

    assert result.success
    assert captured["input"] == "Review this diff"
    assert captured["timeout"] == 17
    assert captured["env"]["ANTHROPIC_API_KEY"] == "anthropic"
    assert "GITHUB_TOKEN" not in captured["env"]


def test_timeout_has_stable_error(monkeypatch, tmp_path):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired("claude", 3)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(ClaudeCodeError, match="timed out after 3 seconds"):
        run_claude(request(tmp_path, timeout_s=3), executable="claude")


@pytest.mark.parametrize("payload", ["not-json", "[]", '{"type":"message"}'])
def test_rejects_invalid_result(payload):
    with pytest.raises(ClaudeCodeError):
        parse_result(payload)


def test_rejects_error_result():
    payload = json.dumps(
        {"type": "result", "is_error": True, "result": "permission denied"}
    )
    with pytest.raises(ClaudeCodeError, match="permission denied"):
        parse_result(payload)


def test_audit_log_excludes_prompt_and_response(tmp_path):
    item = request(tmp_path, prompt="secret prompt")
    result = parse_result(success_payload())
    audit = tmp_path / "audit.jsonl"

    append_audit_event(audit, item, result)
    content = audit.read_text(encoding="utf-8")

    assert "secret prompt" not in content
    assert "No critical findings" not in content
    assert json.loads(content)["session_id"] == "session-1"


def test_sanitized_environment_keeps_runtime_and_anthropic_auth():
    result = sanitized_environment(
        {"PATH": "bin", "ANTHROPIC_API_KEY": "ok", "OPENAI_API_KEY": "remove"}
    )
    assert result["PATH"] == "bin"
    assert result["ANTHROPIC_API_KEY"] == "ok"
    assert "OPENAI_API_KEY" not in result


def test_sanitized_environment_preserves_explicit_git_bash_path():
    result = sanitized_environment(
        {"CLAUDE_CODE_GIT_BASH_PATH": r"D:\Git\bin\bash.exe"}
    )
    assert result["CLAUDE_CODE_GIT_BASH_PATH"] == r"D:\Git\bin\bash.exe"


def test_sanitized_environment_removes_secret_like_names_case_insensitively():
    result = sanitized_environment(
        {
            "custom_password": "remove",
            "Service_Token": "remove",
            "ANTHROPIC_AUTH_TOKEN": "keep",
        }
    )
    assert "custom_password" not in result
    assert "Service_Token" not in result
    assert result["ANTHROPIC_AUTH_TOKEN"] == "keep"
