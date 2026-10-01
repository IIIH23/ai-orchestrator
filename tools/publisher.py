#!/usr/bin/env python3
"""Publishes a verified task branch as a pull request.

Only `task/...` branches are pushed, never with force, and the result is a
pull request: merging stays a human decision behind CI and branch
protection.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable

_TASK_BRANCH = re.compile(r"^task/[A-Za-z0-9][A-Za-z0-9._-]*$")
_PR_URL = re.compile(r"https://\S+/pull/\d+")

Runner = Callable[..., subprocess.CompletedProcess[str]]


class PublishError(RuntimeError):
    """Raised when a task branch cannot be pushed or the PR cannot be opened."""


def _run(run: Runner, command: list[str], cwd: str | Path,
         what: str) -> subprocess.CompletedProcess[str]:
    try:
        completed = run(command, cwd=str(cwd), capture_output=True, text=True,
                        timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PublishError(f"{what} could not run: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[:300]
        raise PublishError(f"{what} failed: {detail}")
    return completed


def publish(workdir: str | Path, branch: str, *, title: str, body: str,
            base: str | None = None, draft: bool = True,
            run: Runner = subprocess.run) -> str:
    """Push the branch to origin, open a pull request and return its URL."""
    if not _TASK_BRANCH.match(branch):
        raise PublishError(f"refusing to publish a non-task branch: {branch!r}")
    _run(run, ["git", "remote", "get-url", "origin"], workdir, "git remote")
    _run(run, ["git", "push", "--set-upstream", "origin", branch], workdir, "git push")

    command = ["gh", "pr", "create", "--head", branch, "--title", title,
               "--body", body]
    if base:
        command += ["--base", base]
    if draft:
        command.append("--draft")
    created = _run(run, command, workdir, "gh pr create")
    match = _PR_URL.search(created.stdout)
    if not match:
        raise PublishError("gh pr create did not return a pull request URL")
    return match.group()
