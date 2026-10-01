#!/usr/bin/env python3
"""Durable SQLite task queue with leases.

A claimed task holds a lease. If the dispatcher crashes, the lease expires
and the task becomes claimable again, so no task is lost or stuck.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable

from tools.dispatcher import Task

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    task_type TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    envelope TEXT NOT NULL,
    allowed_paths TEXT NOT NULL,
    repo TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    max_attempts INTEGER NOT NULL,
    requires_owner_approval INTEGER NOT NULL,
    approved INTEGER NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    lease_expires REAL,
    not_before REAL NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS tasks_claim ON tasks (status, created_at);
"""

_FIELDS = ("id, project, task_type, risk_level, envelope, allowed_paths, repo, "
           "attempt, max_attempts, requires_owner_approval, approved")


class TaskQueue:
    """Statuses: queued, running, done, failed, needs_owner."""

    def __init__(self, path: str | Path, *, clock: Callable[[], float] = time.time,
                 defer_seconds: float = 900) -> None:
        self._clock = clock
        self._defer_seconds = defer_seconds
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.executescript(_SCHEMA)

    def close(self) -> None:
        self._db.close()

    def enqueue(self, task: Task) -> bool:
        """Add a task. Returns False when the id already exists."""
        now = self._clock()
        cursor = self._db.execute(
            f"INSERT OR IGNORE INTO tasks ({_FIELDS}, status, not_before, "
            "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (task.id, task.project, task.task_type, task.risk_level,
             json.dumps(task.envelope), json.dumps(task.allowed_paths), task.repo,
             task.attempt, task.max_attempts, int(task.requires_owner_approval),
             int(task.approved), "queued", now, now, now))
        return cursor.rowcount == 1

    def claim_next(self, lease_seconds: int) -> Task | None:
        now = self._clock()
        self._db.execute("BEGIN IMMEDIATE")
        try:
            row = self._db.execute(
                f"SELECT {_FIELDS} FROM tasks WHERE "
                "(status = 'queued' AND not_before <= ?) OR "
                "(status = 'running' AND lease_expires <= ?) "
                "ORDER BY created_at, id LIMIT 1", (now, now)).fetchone()
            if row is None:
                self._db.execute("COMMIT")
                return None
            self._db.execute(
                "UPDATE tasks SET status = 'running', lease_expires = ?, "
                "updated_at = ? WHERE id = ?", (now + lease_seconds, now, row[0]))
            self._db.execute("COMMIT")
        except BaseException:
            self._db.execute("ROLLBACK")
            raise
        return _task_from_row(row)

    def _transition(self, task: Task, status: str, reason: str | None,
                    **extra: Any) -> None:
        columns = {"status": status, "reason": reason, "lease_expires": None,
                   "updated_at": self._clock(), **extra}
        assignments = ", ".join(f"{name} = ?" for name in columns)
        self._db.execute(f"UPDATE tasks SET {assignments} WHERE id = ?",
                         (*columns.values(), task.id))

    def complete(self, task: Task, reason: str | None = None) -> None:
        self._transition(task, "done", reason)

    def fail(self, task: Task, reason: str | None = None) -> None:
        self._transition(task, "failed", reason)

    def needs_owner(self, task: Task, reason: str | None = None) -> None:
        self._transition(task, "needs_owner", reason)

    def retry(self, task: Task, reason: str | None = None) -> None:
        self._transition(task, "queued", reason, attempt=task.attempt + 1)

    def defer(self, task: Task, reason: str | None = None) -> None:
        self._transition(task, "queued", reason,
                         not_before=self._clock() + self._defer_seconds)

    def approve(self, task_id: str) -> bool:
        """Release a task that waits for the owner. Returns False otherwise."""
        cursor = self._db.execute(
            "UPDATE tasks SET status = 'queued', approved = 1, reason = NULL, "
            "updated_at = ? WHERE id = ? AND status = 'needs_owner'",
            (self._clock(), task_id))
        return cursor.rowcount == 1

    def status(self, task_id: str) -> tuple[str, str | None] | None:
        row = self._db.execute(
            "SELECT status, reason FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return (row[0], row[1]) if row else None

    def counts(self) -> dict[str, int]:
        return dict(self._db.execute(
            "SELECT status, COUNT(*) FROM tasks GROUP BY status").fetchall())


def _task_from_row(row: tuple[Any, ...]) -> Task:
    return Task(
        id=row[0], project=row[1], task_type=row[2], risk_level=row[3],
        envelope=json.loads(row[4]), allowed_paths=json.loads(row[5]), repo=row[6],
        attempt=row[7], max_attempts=row[8],
        requires_owner_approval=bool(row[9]), approved=bool(row[10]))
