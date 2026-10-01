"""End-to-end tests: a queued task through real queue, gateway, worktree,
worker process, verifier and ledger. Only the worker itself is a script."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml

from tools import orchestrator_daemon as daemon
from tools import workspace

PASSING_TEST = (
    "import unittest\n\n\nclass T(unittest.TestCase):\n"
    "    def test_ok(self):\n        self.assertTrue(True)\n")
WORKERS = {
    "ok": "import pathlib\npathlib.Path('src/app.py').write_text('VALUE = 2\\n')\n",
    "out_of_scope": "import pathlib\npathlib.Path('README.md').write_text('x')\n",
    "quota": "import sys\nsys.stderr.write('429 Too Many Requests')\nsys.exit(1)\n",
}
LIMITS = {"project:demo": 100, "worker:codex": 100, "worker:claude_code": 100}


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t.invalid",
         *args], check=True, capture_output=True, text=True).stdout


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class EndToEndCase(unittest.TestCase):
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
        self.clock = FakeClock()
        self.notes = []
        self.reviews = []

    def worker(self, name):
        path = self.root / f"worker_{name}.py"
        path.write_text(WORKERS[name], "utf-8")
        return [sys.executable, str(path)]

    def build(self, *, codex="ok", claude="ok", limits=None, review="approve",
              publish_mode="none", publish_runner=subprocess.run):
        registry = self.root / "agents.yaml"
        registry.write_text(yaml.safe_dump({"agents": [
            {"id": "codex", "available": True, "cost_class": "premium",
             "timeout": 60, "healthcheck": "python -c pass",
             "fallback": "claude_code", "command": self.worker(codex)},
            {"id": "claude_code", "available": True, "cost_class": "premium",
             "timeout": 60, "healthcheck": "python -c pass", "fallback": None,
             "command": self.worker(claude)},
        ]}), "utf-8")
        settings = daemon.Settings(
            state_dir=self.root / "state", defer_seconds=600,
            costs={"premium": 10}, limits=limits or LIMITS,
            publish_mode=publish_mode)

        def reviewer(request):
            self.reviews.append(request)
            return SimpleNamespace(
                result=json.dumps({"verdict": review, "summary": "reviewed",
                                   "findings": []}),
                session_id="s1", cost_usd=0.0)

        orchestrator = daemon.Orchestrator(
            settings, registry_path=registry, reviewer=reviewer,
            notifier=self.notes.append, clock=self.clock,
            publish_runner=publish_runner)
        self.addCleanup(orchestrator.close)
        return orchestrator

    def spec(self, **overrides):
        spec = {"id": "t1", "project": "demo", "task_type": "code",
                "goal": "Bump VALUE", "repo": str(self.repo),
                "allowed_paths": ["src/"],
                "test_command": ["python", "-m", "unittest", "discover", "-s",
                                 "tests", "-q"]}
        spec.update(overrides)
        return daemon.task_from_spec(spec)

    @staticmethod
    def events(orchestrator, kind):
        return [e for e in orchestrator.ledger.read() if e["event"] == kind]


class HappyPathTests(EndToEndCase):
    def test_task_ends_as_a_commit_on_its_own_branch(self):
        orchestrator = self.build()
        orchestrator.queue.enqueue(self.spec())

        self.assertEqual(orchestrator.tick(), "done")

        self.assertEqual(orchestrator.queue.status("t1"), ("done", None))
        commit = self.events(orchestrator, "commit")[0]
        self.assertEqual(commit["branch"], "task/t1-a1")
        self.assertEqual(
            git(self.repo, "show", "task/t1-a1:src/app.py"), "VALUE = 2\n")
        self.assertEqual(git(self.repo, "show", "main:src/app.py"), "VALUE = 1\n")
        self.assertTrue(workspace.repo_is_clean(self.repo))
        self.assertTrue(self.events(orchestrator, "verdict")[0]["ok"])
        self.assertEqual(self.events(orchestrator, "route")[0]["primary"], "codex")
        self.assertEqual(self.notes, [])
        self.assertEqual(orchestrator.tick(), "idle")

    def test_state_lives_outside_the_repository(self):
        orchestrator = self.build()
        orchestrator.queue.enqueue(self.spec())
        orchestrator.tick()
        state = self.root / "state"
        self.assertTrue((state / "queue.sqlite3").is_file())
        self.assertTrue((state / "ledger.jsonl").is_file())
        self.assertTrue((state / "worktrees" / "t1-a1").is_dir())


class FailurePathTests(EndToEndCase):
    def test_out_of_scope_change_retries_then_fails_without_a_commit(self):
        orchestrator = self.build(codex="out_of_scope")
        orchestrator.queue.enqueue(self.spec())

        self.assertEqual(orchestrator.tick(), "retry")
        self.assertEqual(orchestrator.tick(), "failed")

        status, reason = orchestrator.queue.status("t1")
        self.assertEqual(status, "failed")
        self.assertEqual(reason, "out_of_scope: README.md")
        self.assertEqual(self.events(orchestrator, "commit"), [])
        self.assertTrue(workspace.repo_is_clean(self.repo))

    def test_quota_falls_back_to_the_next_worker_and_says_so(self):
        orchestrator = self.build(codex="quota")
        orchestrator.queue.enqueue(self.spec())

        self.assertEqual(orchestrator.tick(), "done")

        substitution = self.events(orchestrator, "substitution")[0]
        self.assertEqual(
            (substitution["from"], substitution["to"], substitution["reason"]),
            ("codex", "claude_code", "quota"))
        verdict = self.events(orchestrator, "verdict")[0]
        self.assertEqual(verdict["worker"], "claude_code")
        self.assertEqual(verdict["substituted_from"], "codex")
        self.assertEqual(len(self.notes), 1)

    def test_exhausted_fallback_chain_waits_for_the_owner(self):
        orchestrator = self.build(codex="quota", claude="quota")
        orchestrator.queue.enqueue(self.spec())

        self.assertEqual(orchestrator.tick(), "needs_owner")
        self.assertEqual(orchestrator.queue.status("t1")[0], "needs_owner")

    def test_dirty_baseline_blocks_the_task(self):
        orchestrator = self.build()
        (self.repo / "stray.txt").write_text("x", "utf-8")
        orchestrator.queue.enqueue(self.spec())

        self.assertEqual(orchestrator.tick(), "blocked")
        self.assertEqual(
            orchestrator.queue.status("t1"), ("failed", "dirty_baseline"))

    def test_exhausted_budget_defers_and_the_task_runs_later(self):
        orchestrator = self.build(limits={**LIMITS, "worker:codex": 10})
        orchestrator.queue.enqueue(self.spec())
        orchestrator.queue.enqueue(self.spec(id="t2"))

        self.assertEqual(orchestrator.tick(), "done")
        self.assertEqual(orchestrator.tick(), "deferred")
        self.assertEqual(orchestrator.tick(), "idle")

        self.clock.now += 86401
        self.assertEqual(orchestrator.tick(), "done")


class OwnerAndReviewTests(EndToEndCase):
    def test_high_risk_task_waits_for_approval_then_requires_review(self):
        orchestrator = self.build()
        orchestrator.queue.enqueue(self.spec(risk_level="high"))

        self.assertEqual(orchestrator.tick(), "needs_owner")
        self.assertEqual(self.reviews, [])
        self.assertTrue(orchestrator.queue.approve("t1"))
        self.assertEqual(orchestrator.tick(), "done")

        self.assertEqual(len(self.reviews), 1)
        self.assertEqual(self.reviews[0].mode, "review")
        self.assertEqual(self.events(orchestrator, "review")[0]["verdict"], "approve")

    def test_rejected_review_is_not_committed(self):
        orchestrator = self.build(review="request_changes")
        orchestrator.queue.enqueue(self.spec(risk_level="high", max_attempts=1))
        orchestrator.tick()
        orchestrator.queue.approve("t1")

        self.assertEqual(orchestrator.tick(), "failed")
        self.assertEqual(
            orchestrator.queue.status("t1"), ("failed", "review_request_changes"))
        self.assertEqual(self.events(orchestrator, "commit"), [])


class FakeGh:
    """Runs git for real and stands in for the gh CLI."""

    def __init__(self, returncode=0):
        self.calls = []
        self._returncode = returncode

    def __call__(self, command, **kwargs):
        if command[0] != "gh":
            return subprocess.run(command, **kwargs)
        self.calls.append(command)
        return subprocess.CompletedProcess(
            command, self._returncode,
            "https://github.com/example/demo/pull/7" if not self._returncode else "",
            "not authorized" if self._returncode else "")


class PublishTests(EndToEndCase):
    def setUp(self):
        super().setUp()
        self.origin = self.root / "origin.git"
        git(self.root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        git(self.repo, "remote", "add", "origin", str(self.origin))
        git(self.repo, "push", "-q", "origin", "main")

    def test_publishing_is_off_by_default(self):
        gh = FakeGh()
        orchestrator = self.build(publish_runner=gh)
        orchestrator.queue.enqueue(self.spec())
        self.assertEqual(orchestrator.tick(), "done")
        self.assertEqual(gh.calls, [])
        self.assertNotIn("task/t1-a1", git(self.origin, "branch", "--list"))

    def test_verified_task_is_pushed_and_opened_as_a_draft_pr(self):
        gh = FakeGh()
        orchestrator = self.build(publish_mode="draft_pr", publish_runner=gh)
        orchestrator.queue.enqueue(self.spec())

        self.assertEqual(orchestrator.tick(), "done")

        self.assertIn("task/t1-a1", git(self.origin, "branch", "--list"))
        self.assertEqual(
            git(self.origin, "show", "main:src/app.py").strip(), "VALUE = 1")
        published = self.events(orchestrator, "published")[0]
        self.assertEqual(published["url"], "https://github.com/example/demo/pull/7")
        command = gh.calls[0]
        self.assertIn("--draft", command)
        body = command[command.index("--body") + 1]
        for expected in ("Bump VALUE", "tests_passed", "codex", "src/"):
            self.assertIn(expected, body)

    def test_failed_task_is_never_published(self):
        gh = FakeGh()
        orchestrator = self.build(codex="out_of_scope", publish_mode="draft_pr",
                                  publish_runner=gh)
        orchestrator.queue.enqueue(self.spec(max_attempts=1))
        self.assertEqual(orchestrator.tick(), "failed")
        self.assertEqual(gh.calls, [])
        self.assertNotIn("task/t1-a1", git(self.origin, "branch", "--list"))

    def test_publish_failure_keeps_the_result_and_tells_the_owner(self):
        orchestrator = self.build(publish_mode="draft_pr",
                                  publish_runner=FakeGh(returncode=1))
        orchestrator.queue.enqueue(self.spec())

        self.assertEqual(orchestrator.tick(), "done")

        self.assertEqual(orchestrator.queue.status("t1"), ("done", None))
        self.assertEqual(len(self.events(orchestrator, "commit")), 1)
        self.assertEqual(len(self.events(orchestrator, "sync_error")), 1)
        self.assertEqual(self.events(orchestrator, "published"), [])
        self.assertEqual(len(self.notes), 1)
        self.assertIn("t1", self.notes[0])


class RestartTests(EndToEndCase):
    def test_spent_budget_is_remembered_after_a_restart(self):
        limits = {**LIMITS, "worker:codex": 10}
        first = self.build(limits=limits)
        first.queue.enqueue(self.spec())
        self.assertEqual(first.tick(), "done")
        first.close()

        second = self.build(limits=limits)
        second.queue.enqueue(self.spec(id="t2"))
        self.assertEqual(second.tick(), "deferred")


class ConfigurationTests(unittest.TestCase):
    def test_state_dir_is_required(self):
        with self.assertRaises(daemon.ConfigurationError):
            daemon.load_settings(environ={})

    def test_shipped_settings_keep_publishing_off(self):
        settings = daemon.load_settings(
            environ={daemon.STATE_DIR_ENV: "/var/lib/orchestrator"})
        self.assertEqual(settings.publish_mode, "none")

    def test_unknown_publish_mode_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "orchestrator.yaml"
            path.write_text(yaml.safe_dump({"publish": {"mode": "auto_merge"}}),
                            "utf-8")
            with self.assertRaises(daemon.ConfigurationError):
                daemon.load_settings(path, environ={daemon.STATE_DIR_ENV: tmp})

    def test_shipped_settings_load(self):
        settings = daemon.load_settings(
            environ={daemon.STATE_DIR_ENV: "/var/lib/orchestrator"})
        self.assertEqual(settings.lease_seconds, 900)
        self.assertEqual(settings.costs["premium"], 10)
        self.assertIn("worker:codex", settings.limits)

    def test_task_spec_requires_scope_and_test_command(self):
        with self.assertRaises(daemon.ConfigurationError):
            daemon.task_from_spec({"id": "t1", "project": "demo",
                                   "task_type": "code", "goal": "g", "repo": "/r"})

    def test_non_low_risk_spec_requires_owner_approval(self):
        base = {"id": "t1", "project": "demo", "task_type": "code", "goal": "g",
                "repo": "/r", "allowed_paths": ["src/"],
                "test_command": ["python", "-m", "pytest"]}
        self.assertFalse(daemon.task_from_spec(base).requires_owner_approval)
        self.assertTrue(daemon.task_from_spec(
            {**base, "risk_level": "medium"}).requires_owner_approval)


if __name__ == "__main__":
    unittest.main()
