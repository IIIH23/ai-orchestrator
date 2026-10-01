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


if __name__ == "__main__":
    unittest.main()
