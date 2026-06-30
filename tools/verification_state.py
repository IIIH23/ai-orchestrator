#!/usr/bin/env python3
"""Verification-state ledger for autonomous orchestration tasks."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import pathlib
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_STATE_PATH = REPO_ROOT / "artifacts" / "verification_state.json"


@dataclasses.dataclass(frozen=True)
class Evidence:
    kind: str
    source: str
    summary: str
    captured_at: str


@dataclasses.dataclass
class TaskState:
    task_id: str
    status: str = "pending"
    evidence: list[Evidence] = dataclasses.field(default_factory=list)
    completed_at: str | None = None

    def can_complete(self) -> bool:
        return bool(self.evidence)

    def mark_completed(self) -> None:
        if not self.can_complete():
            raise ValueError("cannot mark completed without evidence")
        self.status = "completed"
        self.completed_at = _now()


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _to_state(data: dict[str, Any]) -> TaskState:
    return TaskState(
        task_id=str(data["task_id"]),
        status=str(data.get("status", "pending")),
        evidence=[Evidence(**item) for item in data.get("evidence", [])],
        completed_at=data.get("completed_at"),
    )


def load_state(path: pathlib.Path = DEFAULT_STATE_PATH) -> dict[str, TaskState]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {task_id: _to_state(item) for task_id, item in payload.get("tasks", {}).items()}


def save_state(tasks: dict[str, TaskState], path: pathlib.Path = DEFAULT_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"updated_at": _now(), "tasks": {task_id: dataclasses.asdict(state) for task_id, state in sorted(tasks.items())}}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def record_evidence(task_id: str, kind: str, source: str, summary: str, *, path: pathlib.Path = DEFAULT_STATE_PATH) -> TaskState:
    tasks = load_state(path)
    state = tasks.setdefault(task_id, TaskState(task_id=task_id))
    state.evidence.append(Evidence(kind=kind, source=source, summary=summary, captured_at=_now()))
    state.status = "verified"
    tasks[task_id] = state
    save_state(tasks, path)
    return state


def mark_completed(task_id: str, *, path: pathlib.Path = DEFAULT_STATE_PATH) -> TaskState:
    tasks = load_state(path)
    state = tasks.setdefault(task_id, TaskState(task_id=task_id))
    state.mark_completed()
    tasks[task_id] = state
    save_state(tasks, path)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain a verification-state ledger")
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record")
    rec.add_argument("task_id")
    rec.add_argument("kind")
    rec.add_argument("source")
    rec.add_argument("summary")
    done = sub.add_parser("complete")
    done.add_argument("task_id")
    show = sub.add_parser("show")
    show.add_argument("task_id", nargs="?")
    args = parser.parse_args()

    try:
        if args.command == "record":
            result = record_evidence(args.task_id, args.kind, args.source, args.summary)
            print(json.dumps(dataclasses.asdict(result), indent=2))
        elif args.command == "complete":
            result = mark_completed(args.task_id)
            print(json.dumps(dataclasses.asdict(result), indent=2))
        else:
            tasks = load_state()
            payload = dataclasses.asdict(tasks[args.task_id]) if args.task_id else {k: dataclasses.asdict(v) for k, v in tasks.items()}
            print(json.dumps(payload, indent=2, sort_keys=True))
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
