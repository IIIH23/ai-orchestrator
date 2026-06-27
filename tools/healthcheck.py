#!/usr/bin/env python3
"""Run basic health checks for the Pulse of Earth staging environment."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from typing import Any


CheckResult = tuple[str, bool, str]
CheckFunction = Callable[[], CheckResult]
NamedCheck = tuple[str, CheckFunction]

DISK_USAGE_LIMIT_PERCENT = 80.0
MEMORY_AVAILABLE_MINIMUM_MB = 100.0


def check_disk_usage() -> CheckResult:
    """Check that usage of the root filesystem is below 80 percent."""
    name = "disk usage < 80%"
    try:
        usage = shutil.disk_usage("/")
        if usage.total <= 0:
            return name, False, "root filesystem reported zero total bytes"
        used_percent = (usage.used / usage.total) * 100
    except OSError as error:
        return name, False, f"unable to read disk usage: {error}"

    passed = used_percent < DISK_USAGE_LIMIT_PERCENT
    return name, passed, f"{used_percent:.1f}% used"


def check_memory_available() -> CheckResult:
    """Check that Linux reports more than 100 MB of available memory."""
    name = "memory available > 100MB"
    meminfo_path = "/proc/meminfo"
    if not os.path.isfile(meminfo_path):
        return name, False, f"{meminfo_path} is unavailable"

    try:
        with open(meminfo_path, encoding="utf-8") as meminfo:
            fields = {
                key.rstrip(":"): int(value)
                for line in meminfo
                if len(parts := line.split()) >= 2
                for key, value in [parts[:2]]
                if value.isdigit()
            }
    except (OSError, ValueError) as error:
        return name, False, f"unable to read {meminfo_path}: {error}"

    available_kb = fields.get("MemAvailable")
    if available_kb is None:
        return name, False, "MemAvailable is missing from /proc/meminfo"

    available_mb = available_kb / 1024
    passed = available_mb > MEMORY_AVAILABLE_MINIMUM_MB
    return name, passed, f"{available_mb:.1f} MB available"


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a health-check command without allowing it to hang indefinitely."""
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )


def _command_detail(completed: subprocess.CompletedProcess[str]) -> str:
    """Return a concise first line from command output."""
    output = completed.stdout.strip() or completed.stderr.strip()
    return output.splitlines()[0] if output else f"exit code {completed.returncode}"


def check_docker_running() -> CheckResult:
    """Check that the Docker CLI exists and can contact the Docker daemon."""
    name = "docker running"
    executable = shutil.which("docker")
    if executable is None:
        return name, False, "docker executable not found"

    try:
        completed = _run_command([executable, "info"])
    except (OSError, subprocess.SubprocessError) as error:
        return name, False, f"docker info failed: {error}"

    if completed.returncode != 0:
        return name, False, f"docker info failed: {_command_detail(completed)}"
    return name, True, "docker daemon is reachable"


def check_ufw_active() -> CheckResult:
    """Check that the UFW firewall is installed and active."""
    name = "ufw active"
    executable = shutil.which("ufw")
    if executable is None:
        return name, False, "ufw executable not found"

    try:
        completed = _run_command([executable, "status"])
    except (OSError, subprocess.SubprocessError) as error:
        return name, False, f"ufw status failed: {error}"

    detail = _command_detail(completed)
    if completed.returncode != 0:
        return name, False, f"ufw status failed: {detail}"

    active = any(
        line.strip().lower() == "status: active"
        for line in completed.stdout.splitlines()
    )
    return name, active, "Status: active" if active else detail


DEFAULT_CHECKS: list[NamedCheck] = [
    ("disk usage < 80%", check_disk_usage),
    ("memory available > 100MB", check_memory_available),
    ("docker running", check_docker_running),
    ("ufw active", check_ufw_active),
]


def run_checks(checks: Sequence[NamedCheck] = DEFAULT_CHECKS) -> list[CheckResult]:
    """Execute named checks and convert unexpected exceptions into failures."""
    results: list[CheckResult] = []
    for configured_name, check_function in checks:
        try:
            name, passed, detail = check_function()
        except Exception as error:  # A health runner must report one broken check.
            results.append(
                (configured_name, False, f"check raised {type(error).__name__}: {error}")
            )
            continue
        results.append((name, passed, detail))
    return results


def format_text(results: Sequence[CheckResult], verbose: bool = False) -> str:
    """Format check results and their summary for terminal output."""
    lines: list[str] = []
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        suffix = f": {detail}" if verbose or not passed else ""
        lines.append(f"{status}  {name}{suffix}")

    passed_count = sum(passed for _, passed, _ in results)
    failed_count = len(results) - passed_count
    lines.append(f"Health: {passed_count} PASS, {failed_count} FAIL")
    return "\n".join(lines)


def format_json(results: Sequence[CheckResult]) -> str:
    """Format check results and their summary as JSON."""
    passed_count = sum(passed for _, passed, _ in results)
    failed_count = len(results) - passed_count
    payload: dict[str, Any] = {
        "checks": [
            {"name": name, "passed": passed, "detail": detail}
            for name, passed, detail in results
        ],
        "summary": {
            "passed": passed_count,
            "failed": failed_count,
            "healthy": failed_count == 0,
        },
    }
    return json.dumps(payload, indent=2)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Pulse of Earth staging health checks."
    )
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="show details for passing checks in text output",
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="always exit successfully, even when checks fail",
    )
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    checks: Sequence[NamedCheck] = DEFAULT_CHECKS,
) -> int:
    """Run checks, print results, and return an appropriate process exit code."""
    args = parse_args(argv)
    results = run_checks(checks)
    print(format_json(results) if args.json else format_text(results, args.verbose))

    failed = any(not passed for _, passed, _ in results)
    return 0 if args.exit_zero or not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
