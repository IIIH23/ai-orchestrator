#!/usr/bin/env python3
"""Task verifier — the only component that may declare a task successful.

A verdict is ok only when the worker changed something, every change is
inside the task's allowed_paths, and the task's own test command passes.
Every other outcome, including a missing configuration, is a failure.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable

from tools import workspace
from tools.dispatcher import Task

# Runners the verifier is willing to execute; everything else is rejected.
ALLOWED_TEST_MODULES = ("unittest", "pytest")


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str


def _normalized_test_command(command: Any) -> list[str] | None:
    if not isinstance(command, list) or not all(isinstance(a, str) for a in command):
        return None
    if len(command) < 3 or command[0] not in ("python", "python3"):
        return None
    if command[1] != "-m" or command[2] not in ALLOWED_TEST_MODULES:
        return None
    return [sys.executable, *command[1:]]


def _in_scope(path: str, allowed_paths: list[str]) -> bool:
    for allowed in allowed_paths:
        prefix = allowed.replace("\\", "/")
        if path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/"):
            return True
    return False


def verify(task: Task, result: Any = None, *, timeout_s: int = 900,
           run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
           ) -> Verdict:
    workdir = task.envelope.get("workdir")
    if not workdir:
        return Verdict(False, "no_workdir")
    if not task.allowed_paths:
        return Verdict(False, "no_allowed_paths")
    command = _normalized_test_command(task.envelope.get("test_command"))
    if command is None:
        return Verdict(False, "test_command_not_allowed")

    changed = workspace.changed_paths(workdir)
    if not changed:
        return Verdict(False, "no_changes")
    outside = [path for path in changed if not _in_scope(path, task.allowed_paths)]
    if outside:
        return Verdict(False, f"out_of_scope: {', '.join(sorted(outside)[:5])}")

    try:
        completed = run(command, cwd=workdir, capture_output=True, text=True,
                        timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired:
        return Verdict(False, "tests_timeout")
    if completed.returncode != 0:
        return Verdict(False, f"tests_failed: exit {completed.returncode}")
    return Verdict(True, "tests_passed")
