#!/usr/bin/env python3
"""GitHub sync checker — compare local state with remote tracking branch."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# Allow ``python tools/github_sync.py`` as well as ``python -m tools.github_sync``.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).parent.parent))


def _run_git(args: Sequence[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the completed process."""
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def detect_default_branch(repo_dir: str | None = None) -> str:
    """Detect the default branch name from remote HEAD, fallback to 'master'."""
    result = _run_git(["symbolic-ref", "refs/remotes/origin/HEAD"], cwd=repo_dir)
    if result.returncode == 0:
        ref = result.stdout.strip()
        # refs/remotes/origin/master -> master
        return ref.rsplit("/", 1)[-1]
    return "master"


def get_ahead_behind(branch: str, repo_dir: str | None = None) -> tuple[int, int]:
    """Return (ahead, behind) counts relative to origin/<branch>."""
    result = _run_git(
        ["rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"],
        cwd=repo_dir,
    )
    if result.returncode != 0:
        return (0, 0)
    parts = result.stdout.strip().split()
    if len(parts) == 2:
        ahead, behind = int(parts[0]), int(parts[1])
    else:
        ahead, behind = 0, 0
    return ahead, behind


def get_local_branch(repo_dir: str | None = None) -> str:
    """Return the current local branch name."""
    result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"


def count_status(repo_dir: str | None = None) -> tuple[int, int]:
    """Return (uncommitted, untracked) file counts from git status --porcelain."""
    result = _run_git(["status", "--porcelain"], cwd=repo_dir)
    if result.returncode != 0:
        return (0, 0)
    lines = [line for line in result.stdout.strip().splitlines() if line.strip()]
    uncommitted = sum(1 for line in lines if line[0] in "MADRC")
    untracked = sum(1 for line in lines if line.startswith("??"))
    return uncommitted, untracked


def check_sync(repo_dir: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Check sync state and return a dict with results."""
    # Verify we're in a git repo
    result = _run_git(["rev-parse", "--git-dir"], cwd=repo_dir)
    if result.returncode != 0:
        return {
            "error": "not a git repository",
            "branch": "unknown",
            "ahead": 0,
            "behind": 0,
            "uncommitted": 0,
            "untracked": 0,
            "in_sync": False,
        }

    branch = get_local_branch(repo_dir)
    default_branch = detect_default_branch(repo_dir)

    if not dry_run:
        # Fetch to get latest remote state
        _run_git(["fetch", "--quiet", "origin", default_branch], cwd=repo_dir)

    ahead, behind = get_ahead_behind(default_branch, repo_dir)
    uncommitted, untracked = count_status(repo_dir)

    in_sync = ahead == 0 and behind == 0 and uncommitted == 0 and untracked == 0

    return {
        "branch": branch,
        "ahead": ahead,
        "behind": behind,
        "uncommitted": uncommitted,
        "untracked": untracked,
        "in_sync": in_sync,
    }


def format_report(state: dict[str, Any]) -> str:
    """Format sync state as a human-readable report."""
    if "error" in state:
        return f"ERROR: {state['error']}"

    lines = [
        f"Branch: {state['branch']}",
        f"Ahead of origin: {state['ahead']}",
        f"Behind origin: {state['behind']}",
        f"Uncommitted files: {state['uncommitted']}",
        f"Untracked files: {state['untracked']}",
    ]
    if state["in_sync"]:
        lines.append("Status: IN SYNC")
    else:
        lines.append("Status: DRIFT DETECTED")
    return "\n".join(lines)


def cmd_check(args: argparse.Namespace) -> int:
    """Execute the check command."""
    state = check_sync(repo_dir=args.repo_dir, dry_run=args.dry_run)

    if "error" in state:
        print(json.dumps(state) if args.json else f"ERROR: {state['error']}")
        return 2

    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print(format_report(state))

    return 0 if state["in_sync"] else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Execute the status command."""
    state = check_sync(repo_dir=args.repo_dir, dry_run=args.dry_run)

    if "error" in state:
        print("ERROR")
        return 2

    if state["in_sync"]:
        print("IN SYNC")
        return 0
    else:
        reasons = []
        if state["ahead"] > 0:
            reasons.append(f"{state['ahead']} commit(s) ahead")
        if state["behind"] > 0:
            reasons.append(f"{state['behind']} commit(s) behind")
        if state["uncommitted"] > 0:
            reasons.append(f"{state['uncommitted']} uncommitted file(s)")
        if state["untracked"] > 0:
            reasons.append(f"{state['untracked']} untracked file(s)")
        print(f"DRIFT: {', '.join(reasons)}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="github_sync",
        description="GitHub sync checker — compare local state with remote.",
    )
    parser.add_argument("--repo-dir", help="Path to git repository (default: cwd)")
    parser.add_argument("--dry-run", action="store_true", help="Skip network operations")

    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Full sync check with report")
    check_parser.add_argument("--json", action="store_true", help="Output JSON")
    check_parser.set_defaults(func=cmd_check)

    status_parser = subparsers.add_parser("status", help="Short sync status")
    status_parser.set_defaults(func=cmd_status)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
