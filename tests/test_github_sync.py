"""Tests for tools/github_sync.py — GitHub sync checker."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


# Ensure project root is on sys.path so 'from tools import github_sync' works
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import github_sync


def _run_git(args: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _init_git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with one commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-q", "-b", "master"], cwd=str(repo))
    _run_git(["config", "user.email", "test@test.com"], cwd=str(repo))
    _run_git(["config", "user.name", "Test"], cwd=str(repo))
    (repo / "README.md").write_text("# Test repo\n")
    _run_git(["add", "."], cwd=str(repo))
    _run_git(["commit", "-q", "-m", "initial"], cwd=str(repo))
    return repo


def test_check_dry_run_in_sync() -> None:
    """A clean repo with no drift should report in_sync=True, exit 0."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_git_repo(Path(tmp))
        state = github_sync.check_sync(repo_dir=str(repo), dry_run=True)
        assert state["in_sync"] is True
        assert state["ahead"] == 0
        assert state["behind"] == 0
        assert state["uncommitted"] == 0
        assert state["untracked"] == 0


def test_check_dry_run_with_uncommitted() -> None:
    """A repo with uncommitted changes should report in_sync=False."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_git_repo(Path(tmp))
        (repo / "README.md").write_text("modified content\n")
        state = github_sync.check_sync(repo_dir=str(repo), dry_run=True)
        assert state["in_sync"] is False
        assert state["uncommitted"] >= 1


def test_check_dry_run_with_untracked() -> None:
    """A repo with untracked files should report in_sync=False."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_git_repo(Path(tmp))
        (repo / "new_file.txt").write_text("untracked\n")
        state = github_sync.check_sync(repo_dir=str(repo), dry_run=True)
        assert state["in_sync"] is False
        assert state["untracked"] >= 1


def test_check_json_output() -> None:
    """CLI check --dry-run --json should produce valid JSON with expected keys."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_git_repo(Path(tmp))
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.github_sync",
                "--repo-dir",
                str(repo),
                "--dry-run",
                "check",
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "branch" in data
        assert "ahead" in data
        assert "behind" in data
        assert "uncommitted" in data
        assert "untracked" in data
        assert "in_sync" in data
        assert data["in_sync"] is True


def test_status_in_sync() -> None:
    """Status command on a clean repo should print 'IN SYNC'."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_git_repo(Path(tmp))
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.github_sync",
                "--repo-dir",
                str(repo),
                "--dry-run",
                "status",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert "IN SYNC" in result.stdout


def test_status_drift_output() -> None:
    """Status command on a repo with drift should print 'DRIFT'."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_git_repo(Path(tmp))
        (repo / "extra.txt").write_text("drift\n")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.github_sync",
                "--repo-dir",
                str(repo),
                "--dry-run",
                "status",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 1
        assert "DRIFT" in result.stdout


def test_check_no_git_dir() -> None:
    """Running check in a non-git directory should return error dict."""
    with tempfile.TemporaryDirectory() as tmp:
        state = github_sync.check_sync(repo_dir=tmp, dry_run=True)
        assert "error" in state
        assert state["in_sync"] is False


def test_check_cli_no_git_dir() -> None:
    """CLI check in a non-git directory should exit with code 2."""
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.github_sync",
                "--repo-dir",
                tmp,
                "--dry-run",
                "check",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 2


def test_detect_default_branch_fallback() -> None:
    """When no remote HEAD exists, detect_default_branch returns 'master'."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_git_repo(Path(tmp))
        branch = github_sync.detect_default_branch(repo_dir=str(repo))
        assert branch == "master"


def test_get_local_branch() -> None:
    """get_local_branch should return the current branch name."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_git_repo(Path(tmp))
        branch = github_sync.get_local_branch(repo_dir=str(repo))
        assert branch == "master"


def test_format_report_in_sync() -> None:
    """format_report should include 'IN SYNC' for a clean state."""
    state = {
        "branch": "master",
        "ahead": 0,
        "behind": 0,
        "uncommitted": 0,
        "untracked": 0,
        "in_sync": True,
    }
    report = github_sync.format_report(state)
    assert "IN SYNC" in report
    assert "master" in report


def test_format_report_drift() -> None:
    """format_report should include 'DRIFT' for an out-of-sync state."""
    state = {
        "branch": "master",
        "ahead": 2,
        "behind": 0,
        "uncommitted": 1,
        "untracked": 0,
        "in_sync": False,
    }
    report = github_sync.format_report(state)
    assert "DRIFT" in report
    assert "2" in report
