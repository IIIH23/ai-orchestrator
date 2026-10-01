#!/usr/bin/env python3
"""Deterministic cost report built from the orchestrator ledger.

No model is involved: the report only aggregates what the gateway, the
verifier and the dispatcher already recorded. It answers three questions:
where did the budget go, how much did a verified task cost, and how close
is each scope to its limit.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

import yaml

CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config" / "orchestrator.yaml"
STATE_DIR_ENV = "ORCHESTRATOR_STATE_DIR"


def read_ledger(path: pathlib.Path) -> Iterator[dict[str, Any]]:
    """Yield ledger events; blank and corrupt lines are skipped."""
    if not path.exists():
        return
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def _parse_ts(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _units(event: Mapping[str, Any]) -> float:
    value = event.get("cost", 0)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else round(value, 2)


def _utilization(events: Iterable[tuple[datetime, Mapping[str, Any]]],
                 now: datetime, limits: Mapping[str, float], window_s: float,
                 warn_ratio: float) -> dict[str, dict[str, Any]]:
    cutoff = now - timedelta(seconds=window_s)
    spent: defaultdict[str, float] = defaultdict(float)
    for at, event in events:
        if event.get("event") != "run" or at <= cutoff or at > now:
            continue
        spent[f"project:{event.get('project')}"] += _units(event)
        spent[f"worker:{event.get('worker')}"] += _units(event)
    result: dict[str, dict[str, Any]] = {}
    for scope, limit in sorted(limits.items()):
        used = spent.get(scope, 0.0)
        ratio = used / limit if limit else 1.0
        status = "exhausted" if ratio >= 1 else "warn" if ratio >= warn_ratio else "ok"
        result[scope] = {"spent": _number(used), "limit": _number(limit),
                         "ratio": round(ratio, 4), "status": status}
    return result


def build_report(events: Iterable[Mapping[str, Any]], *, now: datetime | None = None,
                 days: float = 7, limits: Mapping[str, float] | None = None,
                 window_s: float = 86400, warn_ratio: float = 0.8) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    dated: list[tuple[datetime, Mapping[str, Any]]] = []
    skipped = 0
    for event in events:
        at = _parse_ts(event.get("ts"))
        if at is None:
            skipped += 1
            continue
        dated.append((at, event))

    by_worker: dict[str, dict[str, Any]] = {}
    by_project: dict[str, dict[str, Any]] = {}
    tasks: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    total_units = 0.0

    for at, event in dated:
        if at <= since or at > now:
            continue
        kind = event.get("event")
        task_id = event.get("task")
        if kind == "run":
            units = _units(event)
            total_units += units
            worker = by_worker.setdefault(
                str(event.get("worker")), {"runs": 0, "units": 0.0, "outcomes": {}})
            worker["runs"] += 1
            worker["units"] += units
            outcome = str(event.get("outcome"))
            worker["outcomes"][outcome] = worker["outcomes"].get(outcome, 0) + 1
            project = by_project.setdefault(
                str(event.get("project")), {"runs": 0, "units": 0.0})
            project["runs"] += 1
            project["units"] += units
            if task_id:
                task = tasks.setdefault(
                    str(task_id), {"runs": 0, "units": 0.0, "verified": None})
                task["runs"] += 1
                task["units"] += units
        elif kind == "verdict" and task_id:
            task = tasks.setdefault(
                str(task_id), {"runs": 0, "units": 0.0, "verified": None})
            task["verified"] = bool(event.get("ok"))
        elif kind == "substitution":
            counts["substitutions"] += 1
            reasons[str(event.get("reason"))] += 1
        elif kind == "deferred_budget":
            counts["deferred_budget"] += 1
        elif kind == "needs_owner":
            counts["needs_owner"] += 1
        elif kind == "review":
            counts["reviews"] += 1
        elif kind == "published":
            counts["published"] += 1
        elif kind == "sync_error":
            counts["sync_errors"] += 1

    verified = [t for t in tasks.values() if t["verified"] is True]
    failed = [t for t in tasks.values() if t["verified"] is False]
    wasted = sum(t["units"] for t in failed)

    for group in (*by_worker.values(), *by_project.values(), *tasks.values()):
        group["units"] = _number(group["units"])

    return {
        "window_days": days,
        "generated_at": now.isoformat(timespec="seconds"),
        "skipped_events": skipped,
        "totals": {
            "units": _number(total_units),
            "verified_tasks": len(verified),
            "failed_tasks": len(failed),
            "units_per_verified_task": (
                _number(total_units / len(verified)) if verified else None),
            "wasted_units": _number(wasted),
        },
        "by_worker": by_worker,
        "by_project": by_project,
        "tasks": tasks,
        "events": {
            "substitutions": counts["substitutions"],
            "substitution_reasons": dict(reasons),
            "deferred_budget": counts["deferred_budget"],
            "needs_owner": counts["needs_owner"],
            "reviews": counts["reviews"],
            "published": counts["published"],
            "sync_errors": counts["sync_errors"],
        },
        "utilization": _utilization(dated, now, limits or {}, window_s, warn_ratio),
    }


def render_text(report: Mapping[str, Any]) -> str:
    totals = report["totals"]
    per_task = totals["units_per_verified_task"]
    lines = [
        f"Cost report - last {report['window_days']:g} days "
        f"(generated {report['generated_at']})",
        "",
        f"Total spend: {totals['units']} units",
        f"Verified tasks: {totals['verified_tasks']}, "
        f"failed tasks: {totals['failed_tasks']}",
        "Units per verified task (including failed ones): "
        f"{per_task if per_task is not None else 'n/a'}",
        f"Wasted on failed tasks: {totals['wasted_units']} units",
        "",
        "By worker:",
    ]
    for name, worker in sorted(report["by_worker"].items()):
        outcomes = ", ".join(f"{k}={v}" for k, v in sorted(worker["outcomes"].items()))
        lines.append(f"  {name}: {worker['units']} units, {worker['runs']} runs ({outcomes})")
    lines += ["", "By project:"]
    for name, project in sorted(report["by_project"].items()):
        lines.append(f"  {name}: {project['units']} units, {project['runs']} runs")
    events = report["events"]
    reasons = ", ".join(f"{k}={v}" for k, v in sorted(events["substitution_reasons"].items()))
    lines += [
        "",
        f"Substitutions: {events['substitutions']}" + (f" ({reasons})" if reasons else ""),
        f"Deferred by budget: {events['deferred_budget']}, "
        f"waiting for owner: {events['needs_owner']}, reviews: {events['reviews']}, "
        f"published: {events['published']}, sync errors: {events['sync_errors']}",
    ]
    if report["utilization"]:
        lines += ["", "Budget utilization (current window):"]
        for scope, row in report["utilization"].items():
            lines.append(f"  {scope}: {row['spent']}/{row['limit']} "
                         f"({row['ratio']:.0%}) {row['status']}")
    return "\n".join(lines)


def _load_limits(config: pathlib.Path) -> tuple[Mapping[str, float], float]:
    payload = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    budget = payload.get("budget") or {}
    return dict(budget.get("limits") or {}), float(budget.get("window_seconds", 86400))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=pathlib.Path,
                        help=f"ledger file (default: ${STATE_DIR_ENV}/ledger.jsonl)")
    parser.add_argument("--days", type=float, default=7)
    parser.add_argument("--config", type=pathlib.Path, default=CONFIG_PATH)
    parser.add_argument("--warn-ratio", type=float, default=0.8)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    ledger = args.ledger
    if ledger is None:
        state_dir = os.environ.get(STATE_DIR_ENV, "").strip()
        if not state_dir:
            print(json.dumps({"error": f"{STATE_DIR_ENV} is not set and no --ledger"}),
                  file=sys.stderr)
            return 2
        ledger = pathlib.Path(state_dir) / "ledger.jsonl"
    try:
        limits, window_s = _load_limits(args.config)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        print(json.dumps({"error": f"cannot read budget config: {exc}"}), file=sys.stderr)
        return 2

    report = build_report(read_ledger(ledger), days=args.days, limits=limits,
                          window_s=window_s, warn_ratio=args.warn_ratio)
    print(json.dumps(report, indent=2, sort_keys=True) if args.json
          else render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
