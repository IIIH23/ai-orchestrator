#!/usr/bin/env python3
"""Save, list, and restore AI Orchestrator container releases."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path


IMAGE_REPOSITORY = os.getenv(
    "AI_ORCHESTRATOR_IMAGE",
    "ghcr.io/iiih23/ai-orchestrator",
)
HEALTH_URL = "http://127.0.0.1:8080/health"
COMMAND_TIMEOUT_SECONDS = 60
HEALTH_WAIT_SECONDS = 5


def _running_as_root() -> bool:
    """Return whether the current process is root on a POSIX platform."""
    get_effective_user_id = getattr(os, "geteuid", None)
    return get_effective_user_id is not None and get_effective_user_id() == 0


def default_state_dir() -> Path:
    """Return the release-state directory for the current user."""
    if _running_as_root():
        return Path("/opt/ai-orchestrator/releases")
    return Path.home() / ".ai-orchestrator" / "releases"


def default_compose_file() -> Path:
    """Return the Compose file path for the current user."""
    if _running_as_root():
        return Path("/opt/ai-orchestrator/compose.yaml")
    return Path.cwd() / "compose.yaml"


def default_log_file() -> Path:
    """Return the rollback log path for the current user."""
    if _running_as_root():
        return Path("/opt/ai-orchestrator/logs/rollback.log")
    return Path.home() / ".ai-orchestrator" / "logs" / "rollback.log"


def utc_timestamp(compact: bool = False) -> str:
    """Return the current UTC timestamp in release or log format."""
    now = datetime.now(UTC)
    return now.strftime("%Y%m%dT%H%M%SZ" if compact else "%Y-%m-%dT%H:%M:%SZ")


def log_action(message: str, log_file: Path, dry_run: bool = False) -> None:
    """Print an action and append it to the rollback log."""
    line = f"[{utc_timestamp()}] {message}"
    print(line)
    if dry_run:
        return
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as stream:
        stream.write(f"{line}\n")


def run_command(
    command: Sequence[str],
    *,
    dry_run: bool = False,
    timeout: int = COMMAND_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Run a command with captured text output and a finite timeout."""
    if dry_run:
        print(f"[dry-run] {subprocess.list2cmdline(list(command))}")
        return subprocess.CompletedProcess(command, 0, "", "")
    return subprocess.run(
        list(command),
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout,
    )


def _docker_command(
    arguments: Sequence[str], *, dry_run: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run a Docker command."""
    return run_command(["docker", *arguments], dry_run=dry_run)


def _compose_command(
    compose_file: Path,
    arguments: Sequence[str],
    *,
    dry_run: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a Docker Compose command for the configured project."""
    return _docker_command(
        ["compose", "-f", str(compose_file), *arguments],
        dry_run=dry_run,
    )


def _extract_tag(output: str) -> str:
    """Extract the first image tag from Docker Compose JSON output."""
    records: list[object] = []
    try:
        decoded = json.loads(output)
        records.extend(decoded if isinstance(decoded, list) else [decoded])
    except json.JSONDecodeError:
        for line in output.splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    for record in records:
        if not isinstance(record, dict):
            continue
        for key in ("tag", "Tag"):
            tag = record.get(key)
            if isinstance(tag, str) and tag:
                return tag
    raise RuntimeError("docker compose images returned no image tag")


def release_current(
    compose_file: Path,
    state_dir: Path,
    log_file: Path,
    *,
    dry_run: bool = False,
) -> bool:
    """Save the first current Compose image tag as the last good release."""
    state_file = state_dir / "last-good-release.txt"
    if dry_run:
        _compose_command(compose_file, ["images", "--format", "json"], dry_run=True)
        print(f"[dry-run] write RELEASE_TAG and TIMESTAMP to {state_file}")
        log_action(f"Current state would be saved to {state_file}", log_file, True)
        return True

    completed = _compose_command(compose_file, ["images", "--format", "json"])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise RuntimeError(f"unable to inspect current images: {detail}")

    tag = _extract_tag(completed.stdout)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        f"RELEASE_TAG={tag}\nTIMESTAMP={utc_timestamp(compact=True)}\n",
        encoding="utf-8",
    )
    log_action(f"Current state saved to {state_file}", log_file)
    return True


def release_list(*, dry_run: bool = False) -> bool:
    """Print staging and up to ten locally available SHA release tags."""
    print("Available releases:")
    print("  staging (current)")
    completed = _docker_command(
        ["image", "ls", IMAGE_REPOSITORY, "--format", "{{.Tag}}"],
        dry_run=dry_run,
    )
    if dry_run:
        return True
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise RuntimeError(f"unable to list releases: {detail}")

    tags = (line.strip() for line in completed.stdout.splitlines())
    for tag in [tag for tag in tags if tag.startswith("sha-")][:10]:
        print(tag)
    return True


def rollback_to(
    tag: str,
    compose_file: Path,
    state_dir: Path,
    log_file: Path,
    *,
    dry_run: bool = False,
) -> bool:
    """Save the current state, restart Compose, and verify service health."""
    release_current(compose_file, state_dir, log_file, dry_run=dry_run)
    log_action(f"Rolling back to tag: {tag}", log_file, dry_run)

    for arguments, failure in (
        (["pull"], "pull failed"),
        (["up", "-d"], "up failed"),
    ):
        completed = _compose_command(compose_file, arguments, dry_run=dry_run)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or f"exit code {completed.returncode}"
            raise RuntimeError(f"{failure}: {detail}")

    if dry_run:
        run_command(["curl", "-fsS", HEALTH_URL], dry_run=True)
        log_action("Rollback health check would be performed", log_file, True)
        return True

    time.sleep(HEALTH_WAIT_SECONDS)
    health = run_command(["curl", "-fsS", HEALTH_URL], timeout=15)
    if health.returncode != 0:
        detail = health.stderr.strip() or f"exit code {health.returncode}"
        raise RuntimeError(f"health check failed after rollback: {detail}")

    log_action("Rollback successful: health check passing", log_file)
    return True


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse rollback command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=default_state_dir())
    parser.add_argument("--compose-file", type=Path, default=default_compose_file())
    parser.add_argument("--log-file", type=Path, default=default_log_file())
    parser.add_argument(
        "--dry-run", action="store_true", help="show actions without executing them"
    )
    parser.add_argument(
        "--exit-zero", action="store_true", help="always return a successful exit code"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("current", help="save the current image tag")
    subparsers.add_parser("list", help="list available image tags")
    rollback_parser = subparsers.add_parser(
        "rollback", help="pull and restart a release"
    )
    rollback_parser.add_argument("tag", nargs="?", default="staging")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch the requested rollback action and return a process exit code."""
    args = parse_args(argv)
    try:
        if args.command == "current":
            release_current(
                args.compose_file,
                args.state_dir,
                args.log_file,
                dry_run=args.dry_run,
            )
        elif args.command == "list":
            release_list(dry_run=args.dry_run)
        else:
            rollback_to(
                args.tag,
                args.compose_file,
                args.state_dir,
                args.log_file,
                dry_run=args.dry_run,
            )
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        try:
            log_action(f"ERROR: {error}", args.log_file, args.dry_run)
        except OSError:
            print(f"ERROR: {error}", file=sys.stderr)
        return 0 if args.exit_zero else 1


if __name__ == "__main__":
    raise SystemExit(main())
