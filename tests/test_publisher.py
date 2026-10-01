"""Tests for publishing a verified task branch as a pull request."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import publisher

PR_URL = "https://github.com/example/demo/pull/7"


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t.invalid",
         *args], check=True, capture_output=True, text=True).stdout


class FakeGh:
    """Runs git for real and stands in for the gh CLI."""

    def __init__(self, returncode=0, stdout=PR_URL + "\n", stderr=""):
        self.calls = []
        self._result = (returncode, stdout, stderr)

    def __call__(self, command, **kwargs):
        if command[0] != "gh":
            return subprocess.run(command, **kwargs)
        self.calls.append(command)
        returncode, stdout, stderr = self._result
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.origin = root / "origin.git"
        git(root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.repo = root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "app.py").write_text("VALUE = 1\n", "utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        git(self.repo, "remote", "add", "origin", str(self.origin))
        git(self.repo, "push", "-q", "origin", "main")
        git(self.repo, "switch", "-q", "-c", "task/t1-a1")
        (self.repo / "app.py").write_text("VALUE = 2\n", "utf-8")
        git(self.repo, "commit", "-q", "-am", "task t1")

    def publish(self, gh, **overrides):
        options = dict(title="task t1: bump", body="evidence", run=gh)
        options.update(overrides)
        return publisher.publish(self.repo, "task/t1-a1", **options)

    def test_pushes_the_task_branch_and_returns_the_pr_url(self):
        gh = FakeGh()
        self.assertEqual(self.publish(gh), PR_URL)
        self.assertIn("task/t1-a1", git(self.origin, "branch", "--list"))
        command = gh.calls[0]
        self.assertEqual(command[:3], ["gh", "pr", "create"])
        self.assertEqual(command[command.index("--head") + 1], "task/t1-a1")
        self.assertEqual(command[command.index("--title") + 1], "task t1: bump")
        self.assertIn("--draft", command)

    def test_draft_can_be_turned_off_and_base_set(self):
        gh = FakeGh()
        self.publish(gh, draft=False, base="main")
        command = gh.calls[0]
        self.assertNotIn("--draft", command)
        self.assertEqual(command[command.index("--base") + 1], "main")

    def test_only_task_branches_are_published(self):
        gh = FakeGh()
        for branch in ("main", "feature/x", "task/../main"):
            with self.subTest(branch=branch), \
                    self.assertRaises(publisher.PublishError):
                publisher.publish(self.repo, branch, title="t", body="b", run=gh)
        self.assertEqual(gh.calls, [])

    def test_never_force_pushes(self):
        commands = []

        def run(command, **kwargs):
            commands.append(command)
            return FakeGh()(command, **kwargs)

        self.publish(run)
        pushes = [c for c in commands if "push" in c]
        self.assertTrue(pushes)
        for command in pushes:
            self.assertFalse({"--force", "-f", "--force-with-lease"} & set(command))

    def test_missing_remote_is_an_error_before_anything_is_pushed(self):
        git(self.repo, "remote", "remove", "origin")
        gh = FakeGh()
        with self.assertRaises(publisher.PublishError):
            self.publish(gh)
        self.assertEqual(gh.calls, [])

    def test_gh_failure_is_reported(self):
        gh = FakeGh(returncode=1, stdout="", stderr="GraphQL: not authorized")
        with self.assertRaises(publisher.PublishError) as raised:
            self.publish(gh)
        self.assertIn("not authorized", str(raised.exception))

    def test_gh_output_without_a_url_is_an_error(self):
        with self.assertRaises(publisher.PublishError):
            self.publish(FakeGh(stdout="created\n"))


if __name__ == "__main__":
    unittest.main()
