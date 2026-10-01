"""Tests for per-task worktrees, the task verifier and the JSONL ledger."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import task_verifier, workspace
from tools.dispatcher import Task
from tools.ledger import JsonlLedger

PASSING_TEST = (
    "import unittest\n\n\nclass T(unittest.TestCase):\n"
    "    def test_ok(self):\n        self.assertTrue(True)\n")
FAILING_TEST = PASSING_TEST.replace("assertTrue(True)", "assertTrue(False)")
TEST_COMMAND = ["python", "-m", "unittest", "discover", "-s", "tests", "-q"]


def git(cwd, *args):
    subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t.invalid",
         *args], check=True, capture_output=True, text=True)


class RepoCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.repo = self.root / "repo"
        (self.repo / "tests").mkdir(parents=True)
        (self.repo / "src").mkdir()
        (self.repo / "tests" / "test_sample.py").write_text(PASSING_TEST, "utf-8")
        (self.repo / "src" / "app.py").write_text("VALUE = 1\n", "utf-8")
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")

    def worktree(self, attempt=1):
        return workspace.prepare(self.repo, "t1", attempt, self.root / "worktrees")

    def task(self, workdir, **overrides):
        fields = dict(
            id="t1", project="demo", task_type="code", risk_level="low",
            envelope={"workdir": str(workdir), "test_command": TEST_COMMAND},
            allowed_paths=["src/"], repo=str(self.repo))
        fields.update(overrides)
        return Task(**fields)


class WorkspaceTests(RepoCase):
    def test_clean_repo_is_clean(self):
        self.assertTrue(workspace.repo_is_clean(self.repo))

    def test_modified_or_untracked_repo_is_dirty(self):
        (self.repo / "new.txt").write_text("x", "utf-8")
        self.assertFalse(workspace.repo_is_clean(self.repo))

    def test_missing_or_non_git_directory_is_not_clean(self):
        self.assertFalse(workspace.repo_is_clean(self.root / "missing"))
        self.assertFalse(workspace.repo_is_clean(""))
        plain = self.root / "plain"
        plain.mkdir()
        self.assertFalse(workspace.repo_is_clean(plain))

    def test_prepare_isolates_changes_from_the_baseline(self):
        workdir = self.worktree()
        (workdir / "src" / "app.py").write_text("VALUE = 2\n", "utf-8")
        self.assertTrue(workspace.repo_is_clean(self.repo))
        self.assertEqual(workspace.changed_paths(workdir), ["src/app.py"])

    def test_prepare_rejects_unsafe_ids_and_existing_worktrees(self):
        with self.assertRaises(workspace.WorkspaceError):
            workspace.prepare(self.repo, "../evil", 1, self.root / "worktrees")
        self.worktree()
        with self.assertRaises(workspace.WorkspaceError):
            self.worktree()

    def test_commit_records_changes_on_the_task_branch(self):
        workdir = self.worktree()
        (workdir / "src" / "new.py").write_text("X = 1\n", "utf-8")
        sha = workspace.commit(workdir, "task t1")
        self.assertEqual(len(sha), 40)
        self.assertEqual(workspace.changed_paths(workdir), [])
        self.assertTrue(workspace.repo_is_clean(self.repo))

    def test_commit_without_changes_raises(self):
        with self.assertRaises(workspace.WorkspaceError):
            workspace.commit(self.worktree(), "empty")


class VerifierTests(RepoCase):
    def change(self, workdir, relative="src/app.py", content="VALUE = 2\n"):
        target = workdir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, "utf-8")

    def test_in_scope_change_with_passing_tests_is_ok(self):
        workdir = self.worktree()
        self.change(workdir)
        verdict = task_verifier.verify(self.task(workdir))
        self.assertTrue(verdict.ok, verdict.reason)

    def test_no_changes_is_a_failure(self):
        verdict = task_verifier.verify(self.task(self.worktree()))
        self.assertEqual((verdict.ok, verdict.reason), (False, "no_changes"))

    def test_change_outside_allowed_paths_is_a_failure(self):
        workdir = self.worktree()
        self.change(workdir)
        self.change(workdir, "README.md", "x")
        verdict = task_verifier.verify(self.task(workdir))
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.reason, "out_of_scope: README.md")

    def test_prefix_lookalike_directory_is_out_of_scope(self):
        workdir = self.worktree()
        self.change(workdir, "src_evil/app.py", "x")
        self.assertFalse(task_verifier.verify(self.task(workdir)).ok)

    def test_failing_tests_are_a_failure(self):
        workdir = self.worktree()
        self.change(workdir)
        self.change(workdir, "tests/test_sample.py", FAILING_TEST)
        verdict = task_verifier.verify(
            self.task(workdir, allowed_paths=["src/", "tests/"]))
        self.assertFalse(verdict.ok)
        self.assertTrue(verdict.reason.startswith("tests_failed"))

    def test_missing_configuration_fails_closed(self):
        workdir = self.worktree()
        self.change(workdir)
        cases = {
            "no_workdir": self.task(workdir, envelope={"test_command": TEST_COMMAND}),
            "no_allowed_paths": self.task(workdir, allowed_paths=[]),
            "test_command_not_allowed": self.task(
                workdir, envelope={"workdir": str(workdir)}),
        }
        for reason, task in cases.items():
            with self.subTest(reason=reason):
                verdict = task_verifier.verify(task)
                self.assertEqual((verdict.ok, verdict.reason), (False, reason))

    def test_only_allowlisted_test_runners_are_executed(self):
        workdir = self.worktree()
        self.change(workdir)
        calls = []
        for command in (["bash", "-c", "true"], ["python", "-c", "pass"],
                        ["python", "-m", "http.server"], "python -m pytest"):
            task = self.task(
                workdir, envelope={"workdir": str(workdir), "test_command": command})
            verdict = task_verifier.verify(task, run=calls.append)
            self.assertEqual(verdict.reason, "test_command_not_allowed")
        self.assertEqual(calls, [])

    def test_pytest_is_an_accepted_runner(self):
        self.assertIsNotNone(task_verifier._normalized_test_command(
            ["python", "-m", "pytest", "-q"]))

    def test_test_timeout_is_a_failure(self):
        workdir = self.worktree()
        self.change(workdir)

        def run(*args, **kwargs):
            raise subprocess.TimeoutExpired("python", 1)

        verdict = task_verifier.verify(self.task(workdir), run=run)
        self.assertEqual((verdict.ok, verdict.reason), (False, "tests_timeout"))


class LedgerTests(unittest.TestCase):
    def test_events_are_appended_with_a_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = JsonlLedger(Path(tmp) / "state" / "ledger.jsonl",
                                 now=lambda: "2026-10-01T00:00:00+00:00")
            ledger({"event": "run", "worker": "codex"})
            ledger({"event": "verdict", "ok": True})
            events = list(ledger.read())
        self.assertEqual([event["event"] for event in events], ["run", "verdict"])
        self.assertEqual(events[0]["ts"], "2026-10-01T00:00:00+00:00")
        self.assertEqual(events[0]["worker"], "codex")

    def test_reading_a_missing_ledger_yields_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = JsonlLedger(Path(tmp) / "ledger.jsonl")
            self.assertEqual(list(ledger.read()), [])


if __name__ == "__main__":
    unittest.main()
