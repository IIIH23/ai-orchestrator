#!/usr/bin/env python3
"""Worker gateway — budget, circuit breaker and explicit fallback for workers.

Workers are CLI processes (Codex, Claude Code) that talk to their providers
directly, so an HTTP proxy cannot see them. The gateway therefore wraps the
worker invocation itself. Every substitution is written to the ledger and
sent to the notifier: a worker is never replaced silently.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

Worker = Mapping[str, Any]
Clock = Callable[[], float]

_QUOTA_PATTERN = re.compile(
    r"\b429\b|too many requests|rate.?limit|quota|usage limit|insufficient_quota",
    re.IGNORECASE,
)
_TRANSIENT_PATTERN = re.compile(
    r"connection (reset|refused|aborted)|timed? ?out|temporarily unavailable"
    r"|\b50[234]\b|overloaded|network is unreachable|worker unavailable",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RunResult:
    """Outcome of one worker process."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass(frozen=True)
class GatewayResult:
    """Outcome of a gateway invocation.

    status is one of: ok, task_fail, deferred_budget, needs_owner.
    """

    status: str
    worker_id: str
    substituted_from: str | None = None
    output: str = ""


def classify(result: RunResult) -> str:
    """Classify a run as ok, quota, transient or task_fail.

    Only quota and transient are provider problems; task_fail is the task's
    own failure and must not trigger a fallback.
    """
    if result.timed_out:
        return "transient"
    if result.exit_code == 0:
        return "ok"
    if _QUOTA_PATTERN.search(result.stderr):
        return "quota"
    if _TRANSIENT_PATTERN.search(result.stderr):
        return "transient"
    return "task_fail"


class MemoryGatewayState:
    """Breaker and spend state that lives only as long as the process."""

    def __init__(self) -> None:
        self._breakers: dict[str, tuple[int, float | None]] = {}
        self._spend: dict[str, list[tuple[float, float]]] = {}

    def breaker(self, worker_id: str) -> tuple[int, float | None]:
        return self._breakers.get(worker_id, (0, None))

    def set_breaker(self, worker_id: str, failures: int,
                    opened_at: float | None) -> None:
        self._breakers[worker_id] = (failures, opened_at)

    def clear_breaker(self, worker_id: str) -> None:
        self._breakers.pop(worker_id, None)

    def add_spend(self, scope: str, at: float, amount: float) -> None:
        self._spend.setdefault(scope, []).append((at, amount))

    def spent_since(self, scope: str, cutoff: float) -> float:
        return sum(amount for at, amount in self._spend.get(scope, []) if at > cutoff)


class CircuitBreaker:
    """Per-worker breaker: closed -> open after N failures -> half_open."""

    def __init__(self, threshold: int = 3, cooldown_s: float = 600,
                 clock: Clock = time.monotonic, state: Any = None) -> None:
        self._threshold = threshold
        self._cooldown_s = cooldown_s
        self._clock = clock
        self._state = state if state is not None else MemoryGatewayState()

    def state(self, worker_id: str) -> str:
        _, opened_at = self._state.breaker(worker_id)
        if opened_at is None:
            return "closed"
        if self._clock() - opened_at >= self._cooldown_s:
            return "half_open"
        return "open"

    def allow(self, worker_id: str) -> bool:
        return self.state(worker_id) != "open"

    def record_success(self, worker_id: str) -> None:
        self._state.clear_breaker(worker_id)

    def record_failure(self, worker_id: str) -> None:
        failures, opened_at = self._state.breaker(worker_id)
        if self.state(worker_id) == "half_open":
            self._state.set_breaker(worker_id, failures, self._clock())
            return
        failures += 1
        if failures >= self._threshold:
            opened_at = self._clock()
        self._state.set_breaker(worker_id, failures, opened_at)


class Budget:
    """Spend limits in abstract units over a rolling window.

    CLI workers do not report a reliable price, so cost is derived from the
    worker's cost_class. A scope without a configured limit is denied.
    """

    def __init__(self, limits: Mapping[str, float], costs: Mapping[str, float],
                 window_s: float = 86400, clock: Clock = time.monotonic,
                 state: Any = None) -> None:
        self._limits = dict(limits)
        self._costs = dict(costs)
        self._window_s = window_s
        self._clock = clock
        self._state = state if state is not None else MemoryGatewayState()

    def _cost(self, worker: Worker) -> float | None:
        return self._costs.get(str(worker.get("cost_class")))

    def _spent(self, scope: str) -> float:
        return float(self._state.spent_since(scope, self._clock() - self._window_s))

    @staticmethod
    def _scopes(project: str, worker: Worker) -> tuple[str, str]:
        return f"project:{project}", f"worker:{worker['id']}"

    def check(self, project: str, worker: Worker) -> bool:
        cost = self._cost(worker)
        if cost is None:
            return False
        for scope in self._scopes(project, worker):
            limit = self._limits.get(scope)
            if limit is None or self._spent(scope) + cost > limit:
                return False
        return True

    def record(self, project: str, worker: Worker) -> float:
        cost = self._cost(worker) or 0.0
        now = self._clock()
        for scope in self._scopes(project, worker):
            self._state.add_spend(scope, now, cost)
        return cost


class WorkerGateway:
    """Runs a worker under budget and breaker policy with a loud fallback."""

    def __init__(self, *, registry: Sequence[Worker],
                 runner: Callable[[Worker, Mapping[str, Any]], RunResult],
                 budget: Budget, breaker: CircuitBreaker,
                 ledger: Callable[[dict[str, Any]], None],
                 notify: Callable[[str], None]) -> None:
        self._workers = {str(worker["id"]): worker for worker in registry}
        self._runner = runner
        self._budget = budget
        self._breaker = breaker
        self._ledger = ledger
        self._notify = notify

    def invoke(self, worker_id: str, envelope: Mapping[str, Any]) -> GatewayResult:
        project = str(envelope.get("project", ""))
        requested = worker_id
        current: str | None = worker_id
        visited: set[str] = set()
        reason = ""

        while current is not None and current not in visited:
            worker = self._workers.get(current)
            if worker is None or not worker.get("available", False):
                break
            visited.add(current)
            substituted_from = requested if current != requested else None

            if not self._budget.check(project, worker):
                self._ledger({"event": "deferred_budget", "worker": current,
                              "project": project})
                return GatewayResult("deferred_budget", current, substituted_from)

            if self._breaker.allow(current):
                if substituted_from is not None:
                    self._substitute(requested, current, reason, project)
                result = self._runner(worker, envelope)
                outcome = classify(result)
                # A rejected (quota) call consumed nothing; everything else did.
                cost = 0.0 if outcome == "quota" else self._budget.record(project, worker)
                self._ledger({"event": "run", "worker": current, "project": project,
                              "outcome": outcome, "exit_code": result.exit_code,
                              "cost": cost})
                if outcome in ("ok", "task_fail"):
                    self._breaker.record_success(current)
                    return GatewayResult(outcome, current, substituted_from,
                                         result.stdout)
                self._breaker.record_failure(current)
                reason = outcome
            else:
                reason = "breaker_open"

            current = worker.get("fallback")

        self._ledger({"event": "needs_owner", "worker": requested,
                      "project": project, "reason": reason or "unavailable"})
        self._notify(
            f"Worker {requested}: no usable fallback ({reason or 'unavailable'}); "
            "owner decision required.")
        return GatewayResult("needs_owner", requested)

    def _substitute(self, requested: str, replacement: str, reason: str,
                    project: str) -> None:
        self._ledger({"event": "substitution", "from": requested,
                      "to": replacement, "reason": reason, "project": project})
        self._notify(
            f"Worker substitution: {requested} -> {replacement} ({reason}).")
