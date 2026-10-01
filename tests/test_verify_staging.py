"""Tests for the staging verification adapter and its host configuration."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from tools import verify_staging

REPO_ROOT = Path(__file__).resolve().parent.parent
CODE_DIRS = ("tools", "tests", "scripts", "config", "orchestrator_api")
CODE_SUFFIXES = {".py", ".sh", ".yaml", ".yml", ".json"}
PUBLIC_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
ALLOWED_IPV4_PREFIXES = (
    "127.", "0.0.0.0", "10.", "192.168.",
    "192.0.2.", "198.51.100.", "203.0.113.",  # RFC 5737 documentation ranges
)


class StagingHostConfigurationTests(unittest.TestCase):
    def test_missing_host_fails_closed_without_connecting(self):
        with mock.patch.dict("os.environ", {}, clear=False) as env, \
                mock.patch.object(subprocess, "run") as run:
            env.pop("STAGING_HOST", None)
            exit_code = verify_staging.main()
        self.assertNotEqual(exit_code, 0)
        run.assert_not_called()

    def test_host_is_read_from_environment(self):
        completed = subprocess.CompletedProcess([], 0, stdout="deploy\n", stderr="")
        with mock.patch.dict("os.environ", {"STAGING_HOST": "203.0.113.10"}), \
                mock.patch.object(subprocess, "run", return_value=completed) as run:
            self.assertTrue(verify_staging.verify_ssh())
        self.assertIn("deploy@203.0.113.10", run.call_args.args[0])


class NoHardcodedHostsTests(unittest.TestCase):
    def test_code_contains_no_public_ip_literals(self):
        offenders = []
        for directory in CODE_DIRS:
            for path in sorted((REPO_ROOT / directory).rglob("*")):
                if path.suffix not in CODE_SUFFIXES or not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for match in PUBLIC_IPV4.finditer(text):
                    if not match.group().startswith(ALLOWED_IPV4_PREFIXES):
                        offenders.append(
                            f"{path.relative_to(REPO_ROOT).as_posix()}: {match.group()}")
        self.assertEqual(offenders, [])


class FailClosedTests(unittest.TestCase):
    """main() must not report success for an unhealthy staging host."""

    def run_main(self, **overrides):
        checks = {
            "verify_ssh": mock.Mock(return_value=True),
            "verify_docker": mock.Mock(return_value={
                "docker_version": "Docker 27", "compose_version": "v2"}),
            "verify_containers": mock.Mock(return_value=[]),
            "verify_health_endpoint": mock.Mock(return_value={
                "healthy": True, "response": "ok"}),
            "verify_disk_usage": mock.Mock(return_value={"usage_percent": "10%"}),
        }
        checks.update(overrides)
        with mock.patch.dict("os.environ", {"STAGING_HOST": "203.0.113.10"}), \
                mock.patch.multiple(verify_staging, **checks):
            return verify_staging.main()

    def test_all_checks_healthy_passes(self):
        self.assertEqual(self.run_main(), 0)

    def test_unhealthy_endpoint_fails(self):
        unhealthy = mock.Mock(return_value={"healthy": False, "response": "FAIL"})
        self.assertNotEqual(self.run_main(verify_health_endpoint=unhealthy), 0)

    def test_container_check_error_fails(self):
        broken = mock.Mock(side_effect=verify_staging.StagingVerificationError("x"))
        self.assertNotEqual(self.run_main(verify_containers=broken), 0)

    def test_disk_check_error_fails(self):
        broken = mock.Mock(side_effect=verify_staging.StagingVerificationError("x"))
        self.assertNotEqual(self.run_main(verify_disk_usage=broken), 0)

    def test_ssh_timeout_fails_instead_of_crashing(self):
        timeout = mock.Mock(side_effect=subprocess.TimeoutExpired("ssh", 15))
        self.assertEqual(self.run_main(verify_ssh=timeout), 1)


if __name__ == "__main__":
    unittest.main()
