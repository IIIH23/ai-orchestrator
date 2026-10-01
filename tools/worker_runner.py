#!/usr/bin/env python3
"""Runs a worker process for one task and reports a RunResult.

The command comes from the agent registry (`command`), never from the task.
The prompt goes to the worker on stdin, the worktree is its working
directory, and unrelated secrets are removed from its environment.
"""

from __future__ import annotations

import pathlib
import subprocess
from typing import Any, Callable, Mapping

from tools.claude_code_adapter import (
    ClaudeCodeError,
    ClaudeRequest,
    run_claude,
    sanitized_environment,
)
from tools.worker_gateway import RunResult

EXIT_UNAVAILABLE = 127


def build_prompt(envelope: Mapping[str, Any]) -> str:
    """Render the task envelope as the worker's instructions."""
    allowed = ", ".join(envelope.get("allowed_paths") or []) or "(none)"
    test_command = " ".join(envelope.get("test_command") or []) or "(none)"
    lines = [
        f"Task: {envelope.get('goal', '')}",
        "",
        f"Change files only under: {allowed}",
        f"The result is verified with: {test_command}",
        "Do not commit, push, or modify anything outside the allowed paths.",
    ]
    context = envelope.get("context")
    if context:
        lines += ["", "Context:", str(context)]
    return "\n".join(lines)


def _unavailable(detail: str) -> RunResult:
    return RunResult(EXIT_UNAVAILABLE, "", f"worker unavailable: {detail}")


def run_worker(worker: Mapping[str, Any], envelope: Mapping[str, Any], *,
               run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
               claude: Callable[[ClaudeRequest], Any] = run_claude) -> RunResult:
    workdir = envelope.get("workdir")
    if not workdir or not pathlib.Path(workdir).is_dir():
        return RunResult(1, "", "task has no workdir")
    prompt = build_prompt(envelope)
    timeout_s = int(worker.get("timeout") or 600)
    command = worker.get("command")

    if not command and worker.get("adapter") == "tools.claude_code_adapter":
        try:
            result = claude(ClaudeRequest(prompt=prompt, cwd=pathlib.Path(workdir),
                                          mode="edit", timeout_s=timeout_s))
        except ClaudeCodeError as exc:
            return RunResult(1, "", str(exc), timed_out="timed out" in str(exc))
        return RunResult(0, result.result, "")

    if not isinstance(command, list) or not command:
        return _unavailable(f"no command configured for {worker.get('id')}")

    try:
        completed = run([str(part) for part in command], input=prompt, text=True,
                        cwd=workdir, capture_output=True, timeout=timeout_s,
                        env=sanitized_environment(), check=False)
    except subprocess.TimeoutExpired:
        return RunResult(124, "", f"timed out after {timeout_s} seconds",
                         timed_out=True)
    except OSError as exc:
        return _unavailable(str(exc))
    return RunResult(completed.returncode, completed.stdout, completed.stderr)
