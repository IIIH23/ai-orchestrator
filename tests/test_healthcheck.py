"""Tests for the staging health-check runner."""

from __future__ import annotations

import json
import subprocess
from collections import namedtuple
from unittest.mock import mock_open, patch

import pytest

from tools import healthcheck


DiskUsage = namedtuple("DiskUsage", "total used free")


def passing_check() -> healthcheck.CheckResult:
    """Return a representative passing result."""
    return "example check", True, "everything is ready"


def failing_check() -> healthcheck.CheckResult:
    """Return a representative failing result."""
    return "broken check", False, "service is unavailable"


@pytest.mark.parametrize(
    ("check_function", "patches"),
    [
        (
            healthcheck.check_disk_usage,
            (
                patch(
                    "tools.healthcheck.shutil.disk_usage",
                    return_value=DiskUsage(100, 50, 50),
                ),
            ),
        ),
        (
            healthcheck.check_memory_available,
            (
                patch("tools.healthcheck.os.path.isfile", return_value=True),
                patch(
                    "builtins.open",
                    mock_open(read_data="MemTotal: 1024000 kB\nMemAvailable: 204800 kB\n"),
                ),
            ),
        ),
        (
            healthcheck.check_docker_running,
            (
                patch("tools.healthcheck.shutil.which", return_value="/usr/bin/docker"),
                patch(
                    "tools.healthcheck.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        ["docker", "info"], 0, "Docker is running\n", ""
                    ),
                ),
            ),
        ),
        (
            healthcheck.check_ufw_active,
            (
                patch("tools.healthcheck.shutil.which", return_value="/usr/sbin/ufw"),
                patch(
                    "tools.healthcheck.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        ["ufw", "status"], 0, "Status: active\n", ""
                    ),
                ),
            ),
        ),
    ],
)
def test_check_functions_return_typed_tuples(check_function, patches):
    with patches[0]:
        if len(patches) == 1:
            result = check_function()
        else:
            with patches[1]:
                result = check_function()

    assert isinstance(result, tuple)
    assert len(result) == 3
    assert isinstance(result[0], str)
    assert isinstance(result[1], bool)
    assert isinstance(result[2], str)


def test_text_output_format_for_passes_and_failures(capsys):
    checks = [("example check", passing_check), ("broken check", failing_check)]

    exit_code = healthcheck.main(["--verbose"], checks)

    assert exit_code == 1
    assert capsys.readouterr().out == (
        "PASS  example check: everything is ready\n"
        "FAIL  broken check: service is unavailable\n"
        "Health: 1 PASS, 1 FAIL\n"
    )


def test_non_verbose_text_hides_passing_detail(capsys):
    healthcheck.main([], [("example check", passing_check)])

    assert capsys.readouterr().out == "PASS  example check\nHealth: 1 PASS, 0 FAIL\n"


def test_json_output_format(capsys):
    exit_code = healthcheck.main(
        ["--json"], [("example check", passing_check), ("broken check", failing_check)]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload == {
        "checks": [
            {
                "name": "example check",
                "passed": True,
                "detail": "everything is ready",
            },
            {
                "name": "broken check",
                "passed": False,
                "detail": "service is unavailable",
            },
        ],
        "summary": {"passed": 1, "failed": 1, "healthy": False},
    }


def test_exit_zero_overrides_failure(capsys):
    exit_code = healthcheck.main(
        ["--exit-zero"], [("broken check", failing_check)]
    )

    assert exit_code == 0
    assert "FAIL  broken check: service is unavailable" in capsys.readouterr().out


def test_all_checks_passing_returns_zero(capsys):
    checks = [("first", passing_check), ("second", passing_check)]

    assert healthcheck.main([], checks) == 0
    assert "Health: 2 PASS, 0 FAIL" in capsys.readouterr().out


def test_mocked_system_failures_are_reported():
    with (
        patch("tools.healthcheck.shutil.which", return_value="/usr/bin/docker"),
        patch(
            "tools.healthcheck.subprocess.run",
            return_value=subprocess.CompletedProcess(
                ["docker", "info"], 1, "", "daemon unavailable"
            ),
        ),
    ):
        name, passed, detail = healthcheck.check_docker_running()

    assert name == "docker running"
    assert passed is False
    assert "daemon unavailable" in detail
