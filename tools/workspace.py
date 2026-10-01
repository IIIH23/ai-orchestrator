#!/usr/bin/env python3
"""Per-task git worktrees.

Each attempt runs in its own worktree on its own branch, outside the
repository directory. The baseline checkout is never modified, so a failed
attempt cannot leave it dirty for the next task.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_COMMITTER = ("-c", "user.name=Hermes Orchestrator",
              "-c", "user.email=hermes@orchestrator.invalid")


class WorkspaceError(RuntimeError):
    """Raised when a worktree cannot be prepared or committed."""


def _git(cwd: str | Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True,
                          text=True, timeout=120, check=False)


def repo_is_clean(repo: str | Path) -> bool:
    """True only for a git work tree without changes. Anything else is False."""
    if not repo or not Path(repo).is_dir():
        return False
    result = _git(repo, "status", "--porcelain")
    return result.returncode == 0 and not result.stdout.strip()


def prepare(repo: str | Path, task_id: str, attempt: int, root: str | Path) -> Path:
    """Create a worktree for one attempt and return its path."""
    if not _SAFE_ID.match(task_id):
        raise WorkspaceError(f"unsafe task id: {task_id!r}")
    name = f"{task_id}-a{attempt}"
    path = Path(root) / name
    if path.exists():
        raise WorkspaceError(f"worktree already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    result = _git(repo, "worktree", "add", "-b", f"task/{name}", str(path), "HEAD")
    if result.returncode != 0:
        raise WorkspaceError(f"git worktree add failed: {result.stderr.strip()[:300]}")
    return path


def changed_paths(workdir: str | Path) -> list[str]:
    """Paths changed in the worktree, relative and POSIX-style."""
    result = _git(workdir, "status", "--porcelain", "-uall")
    if result.returncode != 0:
        raise WorkspaceError(f"git status failed: {result.stderr.strip()[:300]}")
    paths = []
    for line in result.stdout.splitlines():
        entry = line[3:]
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        paths.append(entry.strip().strip('"'))
    return paths


def commit(workdir: str | Path, message: str) -> str:
    """Commit every change in the worktree and return the commit sha."""
    steps = {"add": ("add", "-A"), "commit": (*_COMMITTER, "commit", "-m", message)}
    for name, args in steps.items():
        result = _git(workdir, *args)
        if result.returncode != 0:
            raise WorkspaceError(
                f"git {name} failed: {(result.stderr or result.stdout).strip()[:300]}")
    return _git(workdir, "rev-parse", "HEAD").stdout.strip()
