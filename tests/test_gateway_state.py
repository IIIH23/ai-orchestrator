"""Budget and circuit-breaker state must survive a daemon restart."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import worker_gateway as wg
from tools.gateway_state import SqliteGatewayState

CODEX = {"id": "codex", "cost_class": "premium"}


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class PersistentStateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "state" / "gateway.sqlite3"
        self.clock = FakeClock()

    def state(self):
        state = SqliteGatewayState(self.path)
        self.addCleanup(state.close)
        return state

    def budget(self):
        return wg.Budget({"project:demo": 100, "worker:codex": 10},
                         {"premium": 10}, window_s=86400, clock=self.clock,
                         state=self.state())

    def breaker(self):
        return wg.CircuitBreaker(threshold=3, cooldown_s=600, clock=self.clock,
                                 state=self.state())

    def test_spend_survives_a_restart(self):
        self.budget().record("demo", CODEX)
        self.assertFalse(self.budget().check("demo", CODEX))

    def test_spend_still_expires_with_the_window_after_a_restart(self):
        self.budget().record("demo", CODEX)
        self.clock.now += 86401
        self.assertTrue(self.budget().check("demo", CODEX))

    def test_open_breaker_survives_a_restart(self):
        breaker = self.breaker()
        for _ in range(3):
            breaker.record_failure("codex")
        restarted = self.breaker()
        self.assertEqual(restarted.state("codex"), "open")
        self.assertFalse(restarted.allow("codex"))

    def test_failure_count_below_threshold_survives_a_restart(self):
        first = self.breaker()
        first.record_failure("codex")
        first.record_failure("codex")
        second = self.breaker()
        second.record_failure("codex")
        self.assertEqual(second.state("codex"), "open")

    def test_success_clears_persisted_breaker_state(self):
        breaker = self.breaker()
        for _ in range(3):
            breaker.record_failure("codex")
        self.clock.now += 601
        breaker.record_success("codex")
        self.assertEqual(self.breaker().state("codex"), "closed")


if __name__ == "__main__":
    unittest.main()
