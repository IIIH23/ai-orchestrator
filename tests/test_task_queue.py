"""Contract tests for the durable SQLite task queue."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.dispatcher import Task
from tools.task_queue import TaskQueue


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_task(task_id="t1", **overrides):
    fields = dict(
        id=task_id, project="demo", task_type="code", risk_level="low",
        envelope={"project": "demo", "goal": "x"}, allowed_paths=["tools/"],
        repo="/srv/demo", max_attempts=2)
    fields.update(overrides)
    return Task(**fields)


class TaskQueueTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "queue.sqlite3"
        self.clock = FakeClock()
        self.queue = TaskQueue(self.path, clock=self.clock)
        self.addCleanup(self.queue.close)

    def test_empty_queue_returns_none(self):
        self.assertIsNone(self.queue.claim_next(900))

    def test_claim_round_trips_every_field(self):
        task = make_task(requires_owner_approval=True)
        self.queue.enqueue(task)
        claimed = self.queue.claim_next(900)
        self.assertEqual(claimed, task)

    def test_enqueue_is_idempotent_on_id(self):
        self.assertTrue(self.queue.enqueue(make_task()))
        self.assertFalse(self.queue.enqueue(make_task(task_type="other")))
        self.assertEqual(self.queue.claim_next(900).task_type, "code")

    def test_claimed_task_is_not_handed_out_twice(self):
        self.queue.enqueue(make_task())
        self.assertIsNotNone(self.queue.claim_next(900))
        self.assertIsNone(self.queue.claim_next(900))

    def test_two_dispatchers_cannot_claim_the_same_task(self):
        other = TaskQueue(self.path, clock=self.clock)
        self.addCleanup(other.close)
        self.queue.enqueue(make_task())
        self.assertIsNotNone(self.queue.claim_next(900))
        self.assertIsNone(other.claim_next(900))

    def test_tasks_are_claimed_in_enqueue_order(self):
        for task_id in ("a", "b", "c"):
            self.queue.enqueue(make_task(task_id))
            self.clock.advance(1)
        self.assertEqual(
            [self.queue.claim_next(900).id for _ in range(3)], ["a", "b", "c"])

    def test_expired_lease_returns_the_task_after_a_crash(self):
        self.queue.enqueue(make_task())
        self.queue.claim_next(900)
        self.clock.advance(899)
        self.assertIsNone(self.queue.claim_next(900))
        self.clock.advance(2)
        reclaimed = self.queue.claim_next(900)
        self.assertEqual(reclaimed.id, "t1")
        self.assertEqual(reclaimed.attempt, 1)

    def test_state_survives_reopening_the_database(self):
        self.queue.enqueue(make_task())
        self.queue.close()
        reopened = TaskQueue(self.path, clock=self.clock)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.claim_next(900).id, "t1")

    def test_complete_is_terminal(self):
        self.queue.enqueue(make_task())
        task = self.queue.claim_next(900)
        self.queue.complete(task)
        self.clock.advance(10_000)
        self.assertIsNone(self.queue.claim_next(900))
        self.assertEqual(self.queue.status("t1"), ("done", None))

    def test_fail_is_terminal_and_keeps_the_reason(self):
        self.queue.enqueue(make_task())
        self.queue.fail(self.queue.claim_next(900), "dirty_baseline")
        self.assertIsNone(self.queue.claim_next(900))
        self.assertEqual(self.queue.status("t1"), ("failed", "dirty_baseline"))

    def test_retry_requeues_with_the_next_attempt(self):
        self.queue.enqueue(make_task())
        self.queue.retry(self.queue.claim_next(900), "tests")
        again = self.queue.claim_next(900)
        self.assertEqual(again.attempt, 2)

    def test_defer_hides_the_task_until_the_delay_passes(self):
        queue = TaskQueue(self.path.with_name("d.sqlite3"), clock=self.clock,
                          defer_seconds=600)
        self.addCleanup(queue.close)
        queue.enqueue(make_task())
        queue.defer(queue.claim_next(900), "budget")
        self.assertIsNone(queue.claim_next(900))
        self.assertEqual(queue.status("t1"), ("queued", "budget"))
        self.clock.advance(601)
        deferred = queue.claim_next(900)
        self.assertEqual(deferred.attempt, 1)

    def test_needs_owner_waits_for_approval(self):
        self.queue.enqueue(make_task(requires_owner_approval=True))
        self.queue.needs_owner(self.queue.claim_next(900), "approval_required")
        self.clock.advance(10_000)
        self.assertIsNone(self.queue.claim_next(900))
        self.assertEqual(
            self.queue.status("t1"), ("needs_owner", "approval_required"))

        self.assertTrue(self.queue.approve("t1"))
        approved = self.queue.claim_next(900)
        self.assertTrue(approved.approved)

    def test_approve_only_applies_to_tasks_waiting_for_the_owner(self):
        self.queue.enqueue(make_task())
        self.assertFalse(self.queue.approve("t1"))
        self.assertFalse(self.queue.approve("missing"))

    def test_counts_by_status(self):
        for task_id in ("a", "b"):
            self.queue.enqueue(make_task(task_id))
        self.queue.complete(self.queue.claim_next(900))
        self.assertEqual(self.queue.counts(), {"done": 1, "queued": 1})


if __name__ == "__main__":
    unittest.main()
