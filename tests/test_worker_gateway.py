"""RED contract tests for tools/worker_gateway.py (SPEC-001 §4, ADR-0002).

unittest-style on purpose: runs under pytest (CI) and under
``python -m unittest`` (the loop verifier allowlist accepts unittest only).
"""

from __future__ import annotations

import unittest

from tools import worker_gateway as wg

COSTS = {"cheap": 1, "standard": 3, "premium": 10}


def registry(**overrides):
    agents = [
        {"id": "codex", "available": True, "cost_class": "premium",
         "timeout": 300, "fallback": "claude_code"},
        {"id": "claude_code", "available": True, "cost_class": "premium",
         "timeout": 600, "fallback": None},
    ]
    for agent in agents:
        agent.update(overrides.get(agent["id"], {}))
    return agents


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeRunner:
    """Returns scripted RunResults per worker id; the last one repeats."""

    def __init__(self, script):
        self.script = {key: list(value) for key, value in script.items()}
        self.calls = []

    def __call__(self, worker, envelope):
        self.calls.append(worker["id"])
        results = self.script[worker["id"]]
        return results.pop(0) if len(results) > 1 else results[0]


def ok():
    return wg.RunResult(exit_code=0, stdout="done", stderr="")


def quota():
    return wg.RunResult(exit_code=1, stdout="",
                        stderr="Error: 429 Too Many Requests: rate limit exceeded")


def task_fail():
    return wg.RunResult(exit_code=1, stdout="", stderr="AssertionError: 2 != 3")


class Harness:
    def __init__(self, script, *, limits=None, agents=None, threshold=3):
        self.clock = FakeClock()
        self.runner = FakeRunner(script)
        self.ledger = []
        self.notes = []
        self.breaker = wg.CircuitBreaker(threshold=threshold, cooldown_s=600,
                                         clock=self.clock)
        self.budget = wg.Budget(
            limits=limits or {"project:demo": 1000, "worker:codex": 1000,
                              "worker:claude_code": 1000},
            costs=COSTS, window_s=86400, clock=self.clock)
        self.gateway = wg.WorkerGateway(
            registry=agents or registry(), runner=self.runner,
            budget=self.budget, breaker=self.breaker,
            ledger=self.ledger.append, notify=self.notes.append)

    def invoke(self, worker_id="codex"):
        return self.gateway.invoke(worker_id, {"project": "demo", "goal": "x"})

    def events(self, kind):
        return [event for event in self.ledger if event["event"] == kind]


class ClassifyTests(unittest.TestCase):
    def test_exit_zero_is_ok(self):
        self.assertEqual(wg.classify(ok()), "ok")

    def test_429_and_quota_messages_are_quota(self):
        for stderr in ("429 Too Many Requests", "You exceeded your current quota",
                       "usage limit reached", "rate_limit_error"):
            with self.subTest(stderr=stderr):
                self.assertEqual(
                    wg.classify(wg.RunResult(1, "", stderr)), "quota")

    def test_timeout_and_network_errors_are_transient(self):
        self.assertEqual(
            wg.classify(wg.RunResult(124, "", "", timed_out=True)), "transient")
        self.assertEqual(
            wg.classify(wg.RunResult(1, "", "connection reset by peer")),
            "transient")

    def test_other_nonzero_is_task_fail(self):
        self.assertEqual(wg.classify(task_fail()), "task_fail")


class CircuitBreakerTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.breaker = wg.CircuitBreaker(threshold=3, cooldown_s=600,
                                         clock=self.clock)

    def trip(self):
        for _ in range(3):
            self.breaker.record_failure("codex")

    def test_starts_closed(self):
        self.assertEqual(self.breaker.state("codex"), "closed")
        self.assertTrue(self.breaker.allow("codex"))

    def test_opens_after_threshold_and_blocks(self):
        self.trip()
        self.assertEqual(self.breaker.state("codex"), "open")
        self.assertFalse(self.breaker.allow("codex"))

    def test_is_per_worker(self):
        self.trip()
        self.assertTrue(self.breaker.allow("claude_code"))

    def test_half_open_after_cooldown_then_success_closes(self):
        self.trip()
        self.clock.advance(601)
        self.assertEqual(self.breaker.state("codex"), "half_open")
        self.assertTrue(self.breaker.allow("codex"))
        self.breaker.record_success("codex")
        self.assertEqual(self.breaker.state("codex"), "closed")

    def test_failure_in_half_open_reopens(self):
        self.trip()
        self.clock.advance(601)
        self.breaker.record_failure("codex")
        self.assertEqual(self.breaker.state("codex"), "open")


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.budget = wg.Budget(limits={"project:demo": 20, "worker:codex": 10},
                                costs=COSTS, window_s=86400, clock=self.clock)
        self.codex = registry()[0]

    def test_allows_within_limits_then_blocks(self):
        self.assertTrue(self.budget.check("demo", self.codex))
        self.budget.record("demo", self.codex)
        self.assertFalse(self.budget.check("demo", self.codex))

    def test_window_expiry_restores_budget(self):
        self.budget.record("demo", self.codex)
        self.clock.advance(86401)
        self.assertTrue(self.budget.check("demo", self.codex))

    def test_missing_limit_denies(self):
        """No configured limit means deny, never unlimited spend."""
        self.assertFalse(self.budget.check("unknown-project", self.codex))


class GatewayTests(unittest.TestCase):
    def test_success_records_run_and_spend(self):
        h = Harness({"codex": [ok()]})
        result = h.invoke()
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.worker_id, "codex")
        self.assertIsNone(result.substituted_from)
        self.assertEqual(len(h.events("run")), 1)
        self.assertEqual(h.notes, [])

    def test_budget_exhausted_defers_without_running(self):
        h = Harness({"codex": [ok()]},
                    limits={"project:demo": 1000, "worker:codex": 5})
        result = h.invoke()
        self.assertEqual(result.status, "deferred_budget")
        self.assertEqual(h.runner.calls, [])

    def test_quota_falls_back_loudly(self):
        h = Harness({"codex": [quota()], "claude_code": [ok()]})
        result = h.invoke()
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.worker_id, "claude_code")
        self.assertEqual(result.substituted_from, "codex")
        self.assertEqual(h.runner.calls, ["codex", "claude_code"])
        substitutions = h.events("substitution")
        self.assertEqual(len(substitutions), 1)
        self.assertEqual(substitutions[0]["from"], "codex")
        self.assertEqual(substitutions[0]["to"], "claude_code")
        self.assertEqual(substitutions[0]["reason"], "quota")
        self.assertEqual(len(h.notes), 1)
        self.assertIn("codex", h.notes[0])
        self.assertIn("claude_code", h.notes[0])

    def test_exhausted_chain_escalates_to_owner(self):
        h = Harness({"claude_code": [quota()]})
        result = h.invoke("claude_code")
        self.assertEqual(result.status, "needs_owner")
        self.assertEqual(len(h.notes), 1)

    def test_task_failure_does_not_fall_back_or_trip_breaker(self):
        h = Harness({"codex": [task_fail()], "claude_code": [ok()]})
        result = h.invoke()
        self.assertEqual(result.status, "task_fail")
        self.assertEqual(h.runner.calls, ["codex"])
        self.assertEqual(h.breaker.state("codex"), "closed")
        self.assertEqual(h.events("substitution"), [])

    def test_open_breaker_skips_worker_without_running_it(self):
        h = Harness({"codex": [quota()], "claude_code": [ok()]})
        for _ in range(3):
            h.invoke()
        h.runner.calls.clear()
        result = h.invoke()
        self.assertEqual(h.runner.calls, ["claude_code"])
        self.assertEqual(result.substituted_from, "codex")
        self.assertEqual(h.events("substitution")[-1]["reason"], "breaker_open")

    def test_unavailable_fallback_is_not_used(self):
        h = Harness({"codex": [quota()], "claude_code": [ok()]},
                    agents=registry(claude_code={"available": False}))
        result = h.invoke()
        self.assertEqual(result.status, "needs_owner")
        self.assertEqual(h.runner.calls, ["codex"])

    def test_fallback_cycle_terminates(self):
        h = Harness({"codex": [quota()], "claude_code": [quota()]},
                    agents=registry(claude_code={"fallback": "codex"}))
        result = h.invoke()
        self.assertEqual(result.status, "needs_owner")
        self.assertEqual(h.runner.calls, ["codex", "claude_code"])

    def test_fallback_respects_its_own_budget(self):
        h = Harness({"codex": [quota()], "claude_code": [ok()]},
                    limits={"project:demo": 1000, "worker:codex": 1000,
                            "worker:claude_code": 5})
        result = h.invoke()
        self.assertEqual(result.status, "deferred_budget")
        self.assertEqual(h.runner.calls, ["codex"])


if __name__ == "__main__":
    unittest.main()
