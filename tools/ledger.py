#!/usr/bin/env python3
"""Append-only JSONL ledger of orchestration events."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Callable, Iterator


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class JsonlLedger:
    """Callable ledger: ``ledger({"event": ...})`` appends one JSON line."""

    def __init__(self, path: str | Path, *, now: Callable[[], str] = _utc_now) -> None:
        self.path = Path(path)
        self._now = now
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, event: dict[str, Any]) -> None:
        line = json.dumps({"ts": self._now(), **event}, ensure_ascii=False,
                          sort_keys=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")

    def read(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)
