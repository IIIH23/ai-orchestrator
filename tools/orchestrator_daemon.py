#!/usr/bin/env python3
"""Orchestrator daemon — wires queue, router, gateway, verifier and ledger.

State (queue database, ledger, worktrees) lives in ORCHESTRATOR_STATE_DIR,
outside any repository. A successful task ends as a commit on its own
branch `task/<id>-a<attempt>`; pushing and opening a pull request stay
with the owner.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import pathlib
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tools import dispatcher, task_verifier, workspace  # noqa: E402
from tools.agent_router import REGISTRY_PATH, RouteDecision, load_registry  # noqa: E402
from tools.agent_runtime import resolve_route  # noqa: E402
from tools.claude_code_adapter import run_claude  # noqa: E402
from tools.dispatcher import Task  # noqa: E402
from tools.ledger import JsonlLedger  # noqa: E402
from tools.review_gate import ReviewGateError, Verdict, run_review_gate  # noqa: E402
from tools.task_queue import TaskQueue  # noqa: E402
from tools.task_verifier import Verdict as TaskVerdict  # noqa: E402
from tools.worker_gateway import Budget, CircuitBreaker, WorkerGateway  # noqa: E402
from tools.worker_runner import run_worker  # noqa: E402

CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config" / "orchestrator.yaml"
STATE_DIR_ENV = "ORCHESTRATOR_STATE_DIR"


class ConfigurationError(RuntimeError):
    """Raised when the daemon cannot be configured safely."""


@dataclasses.dataclass(frozen=True)
class Settings:
    state_dir: pathlib.Path
    lease_seconds: int = 900
    poll_seconds: float = 10
    defer_seconds: float = 900
    breaker_threshold: int = 3
    breaker_cooldown_seconds: float = 600
    budget_window_seconds: float = 86400
    costs: Mapping[str, float] = dataclasses.field(default_factory=dict)
    limits: Mapping[str, float] = dataclasses.field(default_factory=dict)


def load_settings(path: pathlib.Path = CONFIG_PATH,
                  environ: Mapping[str, str] | None = None) -> Settings:
    environ = os.environ if environ is None else environ
    state_dir = environ.get(STATE_DIR_ENV, "").strip()
    if not state_dir:
        raise ConfigurationError(f"{STATE_DIR_ENV} is not set")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    breaker = payload.get("breaker") or {}
    budget = payload.get("budget") or {}
    return Settings(
        state_dir=pathlib.Path(state_dir),
        lease_seconds=int(payload.get("lease_seconds", 900)),
        poll_seconds=float(payload.get("poll_seconds", 10)),
        defer_seconds=float(payload.get("defer_seconds", 900)),
        breaker_threshold=int(breaker.get("threshold", 3)),
        breaker_cooldown_seconds=float(breaker.get("cooldown_seconds", 600)),
        budget_window_seconds=float(budget.get("window_seconds", 86400)),
        costs=dict(budget.get("costs") or {}),
        limits=dict(budget.get("limits") or {}),
    )


def _telegram_notifier() -> Callable[[str], None] | None:
    from tools import telegram_notify

    try:
        token, chat_id, _ = telegram_notify.load_configuration(None)
    except ValueError:
        return None
    return lambda message: telegram_notify.send_message(token, chat_id, message)


class Orchestrator:
    """One dispatcher with its durable state."""

    def __init__(self, settings: Settings, *,
                 registry_path: pathlib.Path = REGISTRY_PATH,
                 runner: Callable[..., Any] = run_worker,
                 reviewer: Callable[..., Any] = run_claude,
                 health_runner: Callable[..., Any] = subprocess.run,
                 notifier: Callable[[str], None] | None = None,
                 clock: Callable[[], float] = time.time) -> None:
        self.settings = settings
        self._registry_path = registry_path
        self._reviewer = reviewer
        self._health_runner = health_runner
        self._notifier = notifier
        self._routes: dict[str, tuple[RouteDecision, Mapping[str, bool]]] = {}
        state = settings.state_dir
        self.worktrees = state / "worktrees"
        self.queue = TaskQueue(state / "queue.sqlite3", clock=clock,
                               defer_seconds=settings.defer_seconds)
        self.ledger = JsonlLedger(state / "ledger.jsonl")
        self.gateway = WorkerGateway(
            registry=load_registry(registry_path), runner=runner,
            budget=Budget(settings.limits, settings.costs,
                          window_s=settings.budget_window_seconds, clock=clock),
            breaker=CircuitBreaker(settings.breaker_threshold,
                                   settings.breaker_cooldown_seconds, clock=clock),
            ledger=self.ledger, notify=self._notify)

    def close(self) -> None:
        self.queue.close()

    def _notify(self, message: str) -> None:
        self.ledger({"event": "notify", "message": message})
        if self._notifier is None:
            return
        try:
            self._notifier(message)
        except Exception as exc:  # noqa: BLE001 - a notification never stops work
            self.ledger({"event": "notify_error", "error": str(exc)[:300]})

    def _route(self, task: Task) -> str:
        resolution = resolve_route(
            task.task_type, task.risk_level, registry_path=self._registry_path,
            runner=self._health_runner)
        route = resolution.route
        self._routes[task.id] = (route, resolution.health.availability)
        primary = str(route.primary["id"]) if route.primary else ""
        self.ledger({"event": "route", "task": task.id, "primary": primary or None,
                     "reviewers": [str(r["id"]) for r in route.reviewers],
                     "blocked_reason": route.blocked_reason})
        # A blocked route has no usable worker: the gateway escalates to the owner.
        return "" if route.blocked_reason else primary

    def _prepare(self, task: Task) -> Task:
        workdir = workspace.prepare(task.repo, task.id, task.attempt, self.worktrees,
                                    reuse=True)
        task.envelope = {**task.envelope, "workdir": str(workdir),
                         "allowed_paths": list(task.allowed_paths)}
        return task

    def _review(self, task: Task, route: RouteDecision,
                availability: Mapping[str, bool]) -> TaskVerdict | None:
        if not route.reviewers:
            return None
        workdir = task.envelope["workdir"]
        changed = ", ".join(workspace.changed_paths(workdir))
        prompt = (f"Task: {task.envelope.get('goal', '')}\n"
                  f"Changed files in the working directory: {changed}\n"
                  "Review the uncommitted changes.")
        try:
            review = run_review_gate(
                task.task_type, task.risk_level, prompt, pathlib.Path(workdir),
                registry_path=self._registry_path, availability=availability,
                reviewer=self._reviewer)
        except ReviewGateError as exc:
            return TaskVerdict(False, f"review_error: {str(exc)[:200]}")
        self.ledger({"event": "review", "task": task.id,
                     "verdict": review.verdict.value if review.verdict else None,
                     "summary": review.summary, "findings": list(review.findings)})
        if review.verdict is not Verdict.APPROVE:
            verdict = review.verdict.value if review.verdict else "missing"
            return TaskVerdict(False, f"review_{verdict}")
        return None

    def _verify(self, task: Task, result: Any) -> TaskVerdict:
        verdict = task_verifier.verify(task, result)
        if not verdict.ok:
            return verdict
        route, availability = self._routes.get(task.id, (None, {}))
        if route is None:
            return TaskVerdict(False, "no_route")
        rejected = self._review(task, route, availability)
        if rejected is not None:
            return rejected
        workdir = task.envelope["workdir"]
        try:
            sha = workspace.commit(
                workdir, f"task {task.id}: {str(task.envelope.get('goal', ''))[:60]}")
        except workspace.WorkspaceError as exc:
            return TaskVerdict(False, f"commit_failed: {str(exc)[:200]}")
        self.ledger({"event": "commit", "task": task.id, "sha": sha,
                     "branch": f"task/{task.id}-a{task.attempt}"})
        return verdict

    def tick(self) -> str:
        return dispatcher.tick(
            queue=self.queue, route=self._route, gateway=self.gateway,
            verify=self._verify, ledger=self.ledger,
            # Linear and Obsidian status sync is not wired yet.
            sync=lambda task, outcome: None,
            repo_is_clean=workspace.repo_is_clean,
            lease_seconds=self.settings.lease_seconds, prepare=self._prepare)


def task_from_spec(spec: Mapping[str, Any]) -> Task:
    """Build a Task from an enqueue file. Non-low risk waits for the owner."""
    missing = [key for key in ("id", "project", "task_type", "goal", "repo",
                               "allowed_paths", "test_command") if not spec.get(key)]
    if missing:
        raise ConfigurationError(f"task spec is missing: {', '.join(missing)}")
    risk_level = str(spec.get("risk_level", "low"))
    return Task(
        id=str(spec["id"]), project=str(spec["project"]),
        task_type=str(spec["task_type"]), risk_level=risk_level,
        envelope={"project": str(spec["project"]), "goal": str(spec["goal"]),
                  "test_command": list(spec["test_command"]),
                  "context": spec.get("context")},
        allowed_paths=[str(path) for path in spec["allowed_paths"]],
        repo=str(spec["repo"]), max_attempts=int(spec.get("max_attempts", 2)),
        requires_owner_approval=risk_level != "low")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    enqueue = commands.add_parser("enqueue", help="add a task from a JSON file")
    enqueue.add_argument("spec", type=pathlib.Path)
    run = commands.add_parser("run", help="process the queue")
    run.add_argument("--once", action="store_true", help="process one tick and exit")
    commands.add_parser("status", help="show task counts by status")
    approve = commands.add_parser("approve", help="release a task waiting for the owner")
    approve.add_argument("task_id")
    args = parser.parse_args(argv)

    try:
        orchestrator = Orchestrator(load_settings(), notifier=_telegram_notifier())
    except ConfigurationError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    try:
        if args.command == "enqueue":
            try:
                task = task_from_spec(json.loads(args.spec.read_text(encoding="utf-8")))
            except (ConfigurationError, json.JSONDecodeError) as exc:
                print(json.dumps({"error": str(exc)}), file=sys.stderr)
                return 2
            added = orchestrator.queue.enqueue(task)
            print(json.dumps({"task": task.id, "enqueued": added}))
            return 0 if added else 1
        if args.command == "status":
            print(json.dumps(orchestrator.queue.counts(), sort_keys=True))
            return 0
        if args.command == "approve":
            approved = orchestrator.queue.approve(args.task_id)
            print(json.dumps({"task": args.task_id, "approved": approved}))
            return 0 if approved else 1
        if args.once:
            print(json.dumps({"outcome": orchestrator.tick()}))
            return 0
        stop = {"requested": False}
        for signum in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signum, lambda *_: stop.update(requested=True))
        dispatcher.run(orchestrator.tick, should_stop=lambda: stop["requested"],
                       poll_seconds=orchestrator.settings.poll_seconds)
        return 0
    finally:
        orchestrator.close()


if __name__ == "__main__":
    raise SystemExit(main())
