"""RED contract tests for tools/dispatcher.py (SPEC-001 §3).

unittest-style on purpose: runs under pytest (CI) and under
``python -m unittest`` (the loop verifier allowlist accepts unittest only).
The queue is a fake: the durable SQLite queue lives in Gen 2 and its real
interface must be reconciled after the VPS audit (SPEC-001 §6).
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from tools import dispatcher


def make_task(**overrides):
    fields = dict(
        id="t1", project="demo", task_type="code", risk_level="low",
        envelope={"project": "demo", "goal": "x"}, allowed_paths=["tools/"],
        repo="/srv/demo", attempt=1, max_attempts=2,
        requires_owner_approval=False, approved=False)
    fields.update(overrides)
    return dispatcher.Task(**fields)


class FakeQueue:
    def __init__(self, task=None):
        self.task = task
        self.calls = []

    def claim_next(self, lease_seconds):
        self.calls.append(("claim_next", lease_seconds))
        return self.task

    def _record(name):  # noqa: N805 - tiny helper to build recorders
        def method(self, task, reason=None):
            self.calls.append((name, task.id, reason))
        return method

    complete = _record("complete")
    defer = _record("defer")
    retry = _record("retry")
    fail = _record("fail")
    needs_owner = _record("needs_owner")

    def transitions(self):
        return [call[0] for call in self.calls if call[0] != "claim_next"]


class Harness:
    def __init__(self, task=None, *, gateway_status="ok", verdict_ok=True,
                 clean=True, verifier_raises=False, sync_raises=False):
        self.queue = FakeQueue(task)
        self.ledger = []
        self.gateway_calls = []
        self.verifier_calls = []
        self.sync_calls = []
        self._gateway_status = gateway_status
        self._verdict_ok = verdict_ok
        self._clean = clean
        self._verifier_raises = verifier_raises
        self._sync_raises = sync_raises

    def _route(self, task):
        return "codex"

    def _invoke(self, worker_id, envelope):
        self.gateway_calls.append(worker_id)
        return SimpleNamespace(status=self._gateway_status, worker_id=worker_id,
                               substituted_from=None, output="")

    def _verify(self, task, result):
        self.verifier_calls.append(task.id)
        if self._verifier_raises:
            raise RuntimeError("verifier crashed")
        return SimpleNamespace(ok=self._verdict_ok, reason="tests")

    def _sync(self, task, outcome):
        self.sync_calls.append((task.id, outcome))
        if self._sync_raises:
            raise RuntimeError("linear down")

    def tick(self, **extra):
        return dispatcher.tick(
            queue=self.queue, route=self._route,
            gateway=SimpleNamespace(invoke=self._invoke),
            verify=self._verify, ledger=self.ledger.append, sync=self._sync,
            repo_is_clean=lambda repo: self._clean, lease_seconds=900, **extra)

    def events(self, kind):
        return [event for event in self.ledger if event["event"] == kind]


class DispatcherTickTests(unittest.TestCase):
    def test_empty_queue_is_idle(self):
        h = Harness(None)
        self.assertEqual(h.tick(), "idle")
        self.assertEqual(h.queue.calls, [("claim_next", 900)])
        self.assertEqual(h.ledger, [])

    def test_dirty_baseline_blocks_before_execution(self):
        h = Harness(make_task(), clean=False)
        self.assertEqual(h.tick(), "blocked")
        self.assertEqual(h.queue.calls[-1], ("fail", "t1", "dirty_baseline"))
        self.assertEqual(h.gateway_calls, [])

    def test_unapproved_gated_task_waits_for_owner(self):
        h = Harness(make_task(requires_owner_approval=True))
        self.assertEqual(h.tick(), "needs_owner")
        self.assertEqual(h.queue.transitions(), ["needs_owner"])
        self.assertEqual(h.gateway_calls, [])

    def test_approved_gated_task_runs(self):
        h = Harness(make_task(requires_owner_approval=True, approved=True))
        self.assertEqual(h.tick(), "done")

    def test_budget_deferral_skips_verifier(self):
        h = Harness(make_task(), gateway_status="deferred_budget")
        self.assertEqual(h.tick(), "deferred")
        self.assertEqual(h.queue.calls[-1], ("defer", "t1", "budget"))
        self.assertEqual(h.verifier_calls, [])

    def test_gateway_escalation_marks_needs_owner(self):
        h = Harness(make_task(), gateway_status="needs_owner")
        self.assertEqual(h.tick(), "needs_owner")
        self.assertEqual(h.queue.transitions(), ["needs_owner"])
        self.assertEqual(h.verifier_calls, [])

    def test_happy_path_completes_records_and_syncs(self):
        h = Harness(make_task())
        self.assertEqual(h.tick(), "done")
        self.assertEqual(h.queue.transitions(), ["complete"])
        self.assertEqual(len(h.events("verdict")), 1)
        self.assertTrue(h.events("verdict")[0]["ok"])
        self.assertEqual(h.sync_calls, [("t1", "done")])

    def test_verifier_runs_even_when_worker_reports_task_fail(self):
        """Worker exit status is never trusted as the verdict."""
        h = Harness(make_task(), gateway_status="task_fail", verdict_ok=False)
        self.assertEqual(h.tick(), "retry")
        self.assertEqual(h.verifier_calls, ["t1"])

    def test_failed_verdict_retries_while_attempts_remain(self):
        h = Harness(make_task(attempt=1, max_attempts=2), verdict_ok=False)
        self.assertEqual(h.tick(), "retry")
        self.assertEqual(h.queue.transitions(), ["retry"])

    def test_failed_verdict_fails_after_last_attempt(self):
        h = Harness(make_task(attempt=2, max_attempts=2), verdict_ok=False)
        self.assertEqual(h.tick(), "failed")
        self.assertEqual(h.queue.transitions(), ["fail"])
        self.assertEqual(h.sync_calls, [("t1", "failed")])

    def test_verifier_crash_is_never_a_pass(self):
        h = Harness(make_task(), verifier_raises=True)
        self.assertEqual(h.tick(), "retry")
        self.assertNotIn("complete", h.queue.transitions())
        self.assertEqual(len(h.events("verifier_error")), 1)

    def test_sync_failure_does_not_lose_the_result(self):
        h = Harness(make_task(), sync_raises=True)
        self.assertEqual(h.tick(), "done")
        self.assertEqual(h.queue.transitions(), ["complete"])
        self.assertEqual(len(h.events("verdict")), 1)
        self.assertEqual(len(h.events("sync_error")), 1)

    def test_ledger_is_written_before_queue_transition(self):
        """A crash between the two must leave evidence, not a silent success."""
        order = []
        h = Harness(make_task())
        h.ledger = SimpleNamespace(append=lambda event: order.append("ledger"))
        original = h.queue.complete
        h.queue.complete = lambda task, reason=None: (
            order.append("queue"), original(task, reason))
        h.tick()
        self.assertEqual(order[:2], ["ledger", "queue"])


class DispatcherPrepareTests(unittest.TestCase):
    def test_prepared_task_is_what_the_worker_and_verifier_receive(self):
        h = Harness(make_task())
        seen = {}

        def prepare(task):
            task.envelope = {**task.envelope, "workdir": "/tmp/wt"}
            return task

        h._invoke_original = h._invoke

        def invoke(worker_id, envelope):
            seen["envelope"] = envelope
            return h._invoke_original(worker_id, envelope)

        h._invoke = invoke
        self.assertEqual(h.tick(prepare=prepare), "done")
        self.assertEqual(seen["envelope"]["workdir"], "/tmp/wt")

    def test_prepare_runs_after_the_gates(self):
        calls = []
        h = Harness(make_task(), clean=False)
        self.assertEqual(h.tick(prepare=calls.append), "blocked")
        self.assertEqual(calls, [])

    def test_prepare_failure_fails_the_task_without_running_a_worker(self):
        h = Harness(make_task())

        def prepare(task):
            raise RuntimeError("worktree add failed")

        self.assertEqual(h.tick(prepare=prepare), "blocked")
        self.assertEqual(h.queue.calls[-1], ("fail", "t1", "prepare_failed"))
        self.assertEqual(h.gateway_calls, [])
        self.assertEqual(len(h.events("prepare_error")), 1)


class DispatcherRunTests(unittest.TestCase):
    def test_sleeps_only_when_idle_and_stops_on_request(self):
        outcomes = iter(["done", "idle", "failed"])
        sleeps = []
        ticks = []

        def tick_once():
            ticks.append(1)
            return next(outcomes)

        processed = dispatcher.run(
            tick_once, should_stop=lambda: len(ticks) >= 3,
            poll_seconds=7, sleep=sleeps.append)
        self.assertEqual(processed, 2)
        self.assertEqual(sleeps, [7])


if __name__ == "__main__":
    unittest.main()
