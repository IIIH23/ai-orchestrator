#!/usr/bin/env python3
"""SQLite-backed breaker and budget state for the worker gateway.

Without it a daemon restart would forget what was spent and close every
circuit, so a restart loop could exceed the budget.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS breaker (
    worker TEXT PRIMARY KEY,
    failures INTEGER NOT NULL,
    opened_at REAL
);
CREATE TABLE IF NOT EXISTS spend (
    scope TEXT NOT NULL,
    at REAL NOT NULL,
    amount REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS spend_scope_at ON spend (scope, at);
"""


class SqliteGatewayState:
    """Same interface as worker_gateway.MemoryGatewayState, but durable."""

    def __init__(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.executescript(_SCHEMA)

    def close(self) -> None:
        self._db.close()

    def breaker(self, worker_id: str) -> tuple[int, float | None]:
        row = self._db.execute(
            "SELECT failures, opened_at FROM breaker WHERE worker = ?",
            (worker_id,)).fetchone()
        return (row[0], row[1]) if row else (0, None)

    def set_breaker(self, worker_id: str, failures: int,
                    opened_at: float | None) -> None:
        self._db.execute(
            "INSERT INTO breaker (worker, failures, opened_at) VALUES (?, ?, ?) "
            "ON CONFLICT(worker) DO UPDATE SET failures = excluded.failures, "
            "opened_at = excluded.opened_at", (worker_id, failures, opened_at))

    def clear_breaker(self, worker_id: str) -> None:
        self._db.execute("DELETE FROM breaker WHERE worker = ?", (worker_id,))

    def add_spend(self, scope: str, at: float, amount: float) -> None:
        self._db.execute(
            "INSERT INTO spend (scope, at, amount) VALUES (?, ?, ?)",
            (scope, at, amount))

    def spent_since(self, scope: str, cutoff: float) -> float:
        row = self._db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM spend WHERE scope = ? AND at > ?",
            (scope, cutoff)).fetchone()
        return float(row[0])
