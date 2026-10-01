"""Tests for the worker runner."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import worker_gateway, worker_runner
from tools.claude_code_adapter import ClaudeCodeError

WRITER = (
    "import pathlib, sys\n"
    "prompt = sys.stdin.read()\n"
    "pathlib.Path('out.txt').write_text(prompt, encoding='utf-8')\n"
    "print('written')\n")


class WorkerRunnerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workdir = Path(self._tmp.name) / "wt"
        self.workdir.mkdir()
        self.envelope = {
            "goal": "Add a constant", "workdir": str(self.workdir),
            "allowed_paths": ["src/"],
            "test_command": ["python", "-m", "unittest"]}

    def script(self, body):
        path = Path(self._tmp.name) / "worker.py"
        path.write_text(body, "utf-8")
        return [sys.executable, str(path)]

    def test_command_runs_in_the_workdir_with_the_prompt_on_stdin(self):
        worker = {"id": "codex", "timeout": 60, "command": self.script(WRITER)}
        result = worker_runner.run_worker(worker, self.envelope)
        self.assertEqual((result.exit_code, result.stdout.strip()), (0, "written"))
        prompt = (self.workdir / "out.txt").read_text("utf-8")
        self.assertIn("Add a constant", prompt)
        self.assertIn("src/", prompt)
        self.assertIn("python -m unittest", prompt)

    def test_nonzero_exit_and_stderr_are_reported(self):
        worker = {"id": "codex", "command": self.script(
            "import sys\nsys.stderr.write('429 Too Many Requests')\nsys.exit(3)\n")}
        result = worker_runner.run_worker(worker, self.envelope)
        self.assertEqual(result.exit_code, 3)
        self.assertEqual(worker_gateway.classify(result), "quota")

    def test_secrets_are_not_passed_to_the_worker(self):
        worker = {"id": "codex", "command": self.script(
            "import os\nprint(os.environ.get('LINEAR_API_KEY', 'absent'))\n")}
        with mock.patch.dict("os.environ", {"LINEAR_API_KEY": "secret-value"}):
            result = worker_runner.run_worker(worker, self.envelope)
        self.assertEqual(result.stdout.strip(), "absent")

    def test_timeout_is_transient(self):
        def run(*args, **kwargs):
            raise subprocess.TimeoutExpired("worker", 5)

        result = worker_runner.run_worker(
            {"id": "codex", "timeout": 5, "command": ["worker"]}, self.envelope,
            run=run)
        self.assertTrue(result.timed_out)
        self.assertEqual(worker_gateway.classify(result), "transient")

    def test_missing_binary_or_command_is_transient_so_fallback_applies(self):
        missing = worker_runner.run_worker(
            {"id": "codex", "command": ["definitely-not-a-real-binary-xyz"]},
            self.envelope)
        unconfigured = worker_runner.run_worker({"id": "hermes"}, self.envelope)
        for result in (missing, unconfigured):
            self.assertEqual(result.exit_code, worker_runner.EXIT_UNAVAILABLE)
            self.assertEqual(worker_gateway.classify(result), "transient")

    def test_missing_workdir_fails_without_running_anything(self):
        calls = []
        result = worker_runner.run_worker(
            {"id": "codex", "command": ["x"]}, {"goal": "g"}, run=calls.append)
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(calls, [])

    def test_adapter_worker_uses_claude_in_edit_mode(self):
        requests = []

        def claude(request):
            requests.append(request)
            return SimpleNamespace(result="edited")

        worker = {"id": "claude_code", "adapter": "tools.claude_code_adapter",
                  "timeout": 120}
        result = worker_runner.run_worker(worker, self.envelope, claude=claude)
        self.assertEqual((result.exit_code, result.stdout), (0, "edited"))
        self.assertEqual(requests[0].mode, "edit")
        self.assertEqual(requests[0].timeout_s, 120)
        self.assertEqual(requests[0].cwd, self.workdir)

    def test_adapter_error_is_reported_as_a_failed_run(self):
        def claude(request):
            raise ClaudeCodeError("Claude Code timed out after 120 seconds")

        worker = {"id": "claude_code", "adapter": "tools.claude_code_adapter"}
        result = worker_runner.run_worker(worker, self.envelope, claude=claude)
        self.assertEqual(result.exit_code, 1)
        self.assertTrue(result.timed_out)


if __name__ == "__main__":
    unittest.main()
