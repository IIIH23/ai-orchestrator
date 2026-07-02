#!/usr/bin/env python3
"""Safe, testable subprocess adapter for Claude Code."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from typing import Any


class ClaudeCodeError(RuntimeError):
    """Raised when Claude Code cannot be invoked or returns an invalid result."""


@dataclasses.dataclass(frozen=True)
class ModePolicy:
    permission_mode: str
    allowed_tools: tuple[str, ...]
    disallowed_tools: tuple[str, ...]


MODE_POLICIES: dict[str, ModePolicy] = {
    "review": ModePolicy(
        permission_mode="plan",
        allowed_tools=("Read", "Glob", "Grep"),
        disallowed_tools=("Edit", "Write", "Bash"),
    ),
    "plan": ModePolicy(
        permission_mode="plan",
        allowed_tools=("Read", "Glob", "Grep"),
        disallowed_tools=("Edit", "Write", "Bash"),
    ),
    "edit": ModePolicy(
        permission_mode="acceptEdits",
        allowed_tools=(
            "Read",
            "Glob",
            "Grep",
            "Edit",
            "Write",
            "Bash(git status:*)",
            "Bash(git diff:*)",
            "Bash(python -m pytest:*)",
        ),
        disallowed_tools=(
            "Bash(git push:*)",
            "Bash(git reset:*)",
            "Bash(git clean:*)",
            "Bash(rm:*)",
            "Bash(gh:*)",
        ),
    ),
}

SENSITIVE_ENV_VARS = {
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AZURE_CLIENT_SECRET",
    "CLOUDFLARE_API_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "LINEAR_API_KEY",
    "OPENAI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
}
ANTHROPIC_AUTH_VARS = {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"}
SENSITIVE_ENV_SUFFIXES = ("_TOKEN", "_SECRET", "_PASSWORD", "_PRIVATE_KEY")


@dataclasses.dataclass(frozen=True)
class ClaudeRequest:
    prompt: str
    cwd: pathlib.Path
    mode: str = "review"
    model: str | None = None
    max_turns: int = 6
    timeout_s: int = 600
    resume_session_id: str | None = None

    def validate(self) -> None:
        if not self.prompt.strip():
            raise ClaudeCodeError("Prompt must not be empty")
        if self.mode not in MODE_POLICIES:
            raise ClaudeCodeError(f"Unsupported mode: {self.mode}")
        if not self.cwd.resolve().is_dir():
            raise ClaudeCodeError(f"Working directory does not exist: {self.cwd}")
        if not 1 <= self.max_turns <= 50:
            raise ClaudeCodeError("max_turns must be between 1 and 50")
        if self.timeout_s < 1:
            raise ClaudeCodeError("timeout_s must be positive")


@dataclasses.dataclass(frozen=True)
class ClaudeResult:
    success: bool
    result: str
    session_id: str | None
    cost_usd: float | None
    duration_ms: int | None
    num_turns: int | None
    subtype: str | None
    stderr: str = ""

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def find_claude(executable: str | None = None) -> str:
    candidate = executable or os.environ.get("CLAUDE_CODE_BIN") or shutil.which("claude")
    if not candidate:
        raise ClaudeCodeError(
            "Claude Code executable not found; install it or set CLAUDE_CODE_BIN"
        )
    return candidate


def sanitized_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Preserve runtime variables and Anthropic auth while removing unrelated secrets."""
    environment = dict(source if source is not None else os.environ)
    for name in tuple(environment):
        normalized = name.upper()
        if normalized in ANTHROPIC_AUTH_VARS:
            continue
        if normalized in SENSITIVE_ENV_VARS or normalized.endswith(
            SENSITIVE_ENV_SUFFIXES
        ):
            environment.pop(name, None)
    if os.name == "nt" and not environment.get("CLAUDE_CODE_GIT_BASH_PATH"):
        candidates = (
            pathlib.Path(r"C:\Program Files\Git\bin\bash.exe"),
            pathlib.Path(r"C:\Program Files\Git\usr\bin\bash.exe"),
        )
        git_bash = next((path for path in candidates if path.is_file()), None)
        if git_bash:
            environment["CLAUDE_CODE_GIT_BASH_PATH"] = str(git_bash)
    return environment


def build_command(request: ClaudeRequest, executable: str) -> list[str]:
    request.validate()
    policy = MODE_POLICIES[request.mode]
    command = [
        executable,
        "-p",
        "--output-format",
        "json",
        "--permission-mode",
        policy.permission_mode,
        "--max-turns",
        str(request.max_turns),
        "--allowedTools",
        *policy.allowed_tools,
        "--disallowedTools",
        *policy.disallowed_tools,
    ]
    if request.model:
        command.extend(("--model", request.model))
    if request.resume_session_id:
        command.extend(("--resume", request.resume_session_id))
    return command


def parse_result(stdout: str, stderr: str = "", returncode: int = 0) -> ClaudeResult:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ClaudeCodeError("Claude Code returned malformed JSON") from exc
    if not isinstance(payload, dict) or payload.get("type") != "result":
        raise ClaudeCodeError("Claude Code response is not a result object")

    success = returncode == 0 and not bool(payload.get("is_error"))
    result = ClaudeResult(
        success=success,
        result=str(payload.get("result", "")),
        session_id=payload.get("session_id"),
        cost_usd=payload.get("total_cost_usd"),
        duration_ms=payload.get("duration_ms"),
        num_turns=payload.get("num_turns"),
        subtype=payload.get("subtype"),
        stderr=stderr.strip(),
    )
    if not success:
        detail = result.result or result.stderr or f"exit code {returncode}"
        raise ClaudeCodeError(f"Claude Code execution failed: {detail}")
    return result


def run_claude(
    request: ClaudeRequest,
    *,
    executable: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> ClaudeResult:
    """Run Claude with the prompt on stdin so it is absent from process arguments."""
    claude = find_claude(executable)
    command = build_command(request, claude)
    try:
        completed = subprocess.run(
            command,
            input=request.prompt,
            text=True,
            cwd=request.cwd.resolve(),
            capture_output=True,
            timeout=request.timeout_s,
            env=sanitized_environment(environment),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClaudeCodeError(
            f"Claude Code timed out after {request.timeout_s} seconds"
        ) from exc
    except OSError as exc:
        raise ClaudeCodeError(f"Could not start Claude Code: {exc}") from exc
    return parse_result(completed.stdout, completed.stderr, completed.returncode)


def append_audit_event(
    path: pathlib.Path, request: ClaudeRequest, result: ClaudeResult
) -> None:
    """Append metadata only. Prompts and model output are intentionally excluded."""
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
        "cwd": str(request.cwd.resolve()),
        "mode": request.mode,
        "model": request.model,
        "max_turns": request.max_turns,
        "success": result.success,
        "session_id": result.session_id,
        "cost_usd": result.cost_usd,
        "duration_ms": result.duration_ms,
        "num_turns": result.num_turns,
    }
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")


def _read_prompt(value: str | None) -> str:
    return value if value is not None else sys.stdin.read()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health", help="Check whether Claude Code is installed")

    run = subparsers.add_parser("run", help="Execute a bounded Claude Code task")
    run.add_argument("prompt", nargs="?", help="Prompt; stdin is used when omitted")
    run.add_argument("--cwd", type=pathlib.Path, default=pathlib.Path.cwd())
    run.add_argument("--mode", choices=tuple(MODE_POLICIES), default="review")
    run.add_argument("--model")
    run.add_argument("--max-turns", type=int, default=6)
    run.add_argument("--timeout", type=int, default=600)
    run.add_argument("--resume")
    run.add_argument("--audit-log", type=pathlib.Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        executable = find_claude()
        if args.command == "health":
            environment = sanitized_environment()
            completed = subprocess.run(
                [executable, "--version"],
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
                env=environment,
            )
            if completed.returncode:
                raise ClaudeCodeError(completed.stderr.strip() or "health check failed")
            auth = subprocess.run(
                [executable, "auth", "status"],
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
                env=environment,
            )
            try:
                auth_payload = json.loads(auth.stdout)
            except json.JSONDecodeError:
                auth_payload = {}
            authenticated = auth.returncode == 0 and bool(auth_payload.get("loggedIn"))
            print(
                json.dumps(
                    {
                        "installed": True,
                        "authenticated": authenticated,
                        "available": authenticated,
                        "version": completed.stdout.strip(),
                        "auth_method": auth_payload.get("authMethod", "none"),
                    }
                )
            )
            return 0 if authenticated else 1

        request = ClaudeRequest(
            prompt=_read_prompt(args.prompt),
            cwd=args.cwd,
            mode=args.mode,
            model=args.model,
            max_turns=args.max_turns,
            timeout_s=args.timeout,
            resume_session_id=args.resume,
        )
        result = run_claude(request, executable=executable)
        if args.audit_log:
            append_audit_event(args.audit_log, request, result)
        print(json.dumps(result.as_dict(), ensure_ascii=False))
        return 0
    except ClaudeCodeError as exc:
        print(json.dumps({"success": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
