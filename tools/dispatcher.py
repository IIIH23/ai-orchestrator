#!/usr/bin/env python3
"""Dispatcher — moves one queued task through gate, worker, verifier and sync.

Invariants:
- the verifier alone decides the verdict; a worker exit status is not trusted
- a verifier crash is a failed verdict, never a pass
- the ledger is written before the queue transition
- a sync failure never changes or loses the result
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass
class Task:
    """A claimed queue item."""

    id: str
    project: str
    task_type: str
    risk_level: str
    envelope: dict[str, Any]
    allowed_paths: list[str] = field(default_factory=list)
    repo: str = ""
    attempt: int = 1
    max_attempts: int = 2
    requires_owner_approval: bool = False
    approved: bool = False


class Queue(Protocol):
    """Durable task queue. claim_next leases a task so a crashed run returns."""

    def claim_next(self, lease_seconds: int) -> Task | None: ...
    def complete(self, task: Task, reason: str | None = None) -> None: ...
    def defer(self, task: Task, reason: str | None = None) -> None: ...
    def retry(self, task: Task, reason: str | None = None) -> None: ...
    def fail(self, task: Task, reason: str | None = None) -> None: ...
    def needs_owner(self, task: Task, reason: str | None = None) -> None: ...


Ledger = Callable[[dict[str, Any]], None]


def _sync_safely(sync: Callable[[Task, str], None], ledger: Ledger,
                 task: Task, outcome: str) -> None:
    try:
        sync(task, outcome)
    except Exception as exc:  # noqa: BLE001 - sync must never affect the result
        ledger({"event": "sync_error", "task": task.id, "outcome": outcome,
                "error": str(exc)[:500]})


def tick(*, queue: Queue, route: Callable[[Task], str], gateway: Any,
         verify: Callable[[Task, Any], Any], ledger: Ledger,
         sync: Callable[[Task, str], None],
         repo_is_clean: Callable[[str], bool], lease_seconds: int = 900,
         prepare: Callable[[Task], Task] | None = None) -> str:
    """Process at most one task.

    prepare, when given, runs after the gates and returns the task the worker
    and verifier will see (for example with a workdir in its envelope).

    Returns idle, needs_owner, blocked, deferred, done, retry or failed.
    """
    task = queue.claim_next(lease_seconds)
    if task is None:
        return "idle"

    if task.requires_owner_approval and not task.approved:
        queue.needs_owner(task, "approval_required")
        _sync_safely(sync, ledger, task, "needs_owner")
        return "needs_owner"

    if not repo_is_clean(task.repo):
        queue.fail(task, "dirty_baseline")
        return "blocked"

    worker_id = route(task)
    if prepare is not None:
        try:
            task = prepare(task)
        except Exception as exc:  # noqa: BLE001 - no workspace, no worker run
            ledger({"event": "prepare_error", "task": task.id,
                    "error": str(exc)[:500]})
            queue.fail(task, "prepare_failed")
            return "blocked"

    result = gateway.invoke(worker_id, task.envelope)

    if result.status == "deferred_budget":
        queue.defer(task, "budget")
        return "deferred"

    if result.status == "needs_owner":
        queue.needs_owner(task, "no_usable_worker")
        _sync_safely(sync, ledger, task, "needs_owner")
        return "needs_owner"

    try:
        verdict = verify(task, result)
        ok, reason = bool(verdict.ok), getattr(verdict, "reason", None)
    except Exception as exc:  # noqa: BLE001 - a crashed verifier is never a pass
        ledger({"event": "verifier_error", "task": task.id,
                "error": str(exc)[:500]})
        ok, reason = False, "verifier_error"

    ledger({"event": "verdict", "task": task.id, "ok": ok, "reason": reason,
            "worker": result.worker_id,
            "substituted_from": result.substituted_from,
            "attempt": task.attempt})

    if ok:
        queue.complete(task)
        _sync_safely(sync, ledger, task, "done")
        return "done"

    if task.attempt < task.max_attempts:
        queue.retry(task, reason)
        return "retry"

    queue.fail(task, reason)
    _sync_safely(sync, ledger, task, "failed")
    return "failed"


def run(tick_once: Callable[[], str], *, should_stop: Callable[[], bool],
        poll_seconds: float = 10, sleep: Callable[[float], None] = time.sleep) -> int:
    """Call tick_once until should_stop(); sleep only when the queue is idle."""
    processed = 0
    while not should_stop():
        if tick_once() == "idle":
            sleep(poll_seconds)
        else:
            processed += 1
    return processed
