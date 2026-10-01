"""Tests for the deterministic cost report built from the JSONL ledger."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from tools import cost_report
from tools import worker_gateway as wg

NOW = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)


def ts(days_ago: float = 0.0) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat(timespec="seconds")


def run(task, worker="codex", outcome="ok", cost=10, project="demo", days_ago=0.0):
    return {"event": "run", "task": task, "worker": worker, "project": project,
            "outcome": outcome, "exit_code": 0 if outcome == "ok" else 1,
            "cost": cost, "ts": ts(days_ago)}


def verdict(task, ok, reason="tests_passed", days_ago=0.0, attempt=1):
    return {"event": "verdict", "task": task, "ok": ok, "reason": reason,
            "attempt": attempt, "ts": ts(days_ago)}


def event(kind, days_ago=0.0, **fields):
    return {"event": kind, "ts": ts(days_ago), **fields}


class ReportTests(unittest.TestCase):
    def test_empty_ledger_reports_zeros(self):
        report = cost_report.build_report([], now=NOW, days=7)
        self.assertEqual(report["totals"]["units"], 0)
        self.assertEqual(report["totals"]["verified_tasks"], 0)
        self.assertIsNone(report["totals"]["units_per_verified_task"])

    def test_spend_is_grouped_by_worker_and_project(self):
        events = [run("a", "codex", cost=10), run("b", "codex", cost=10),
                  run("c", "claude_code", cost=10, project="other")]
        report = cost_report.build_report(events, now=NOW, days=7)
        self.assertEqual(report["by_worker"]["codex"]["units"], 20)
        self.assertEqual(report["by_worker"]["codex"]["runs"], 2)
        self.assertEqual(report["by_worker"]["claude_code"]["units"], 10)
        self.assertEqual(report["by_project"]["demo"]["units"], 20)
        self.assertEqual(report["by_project"]["other"]["units"], 10)
        self.assertEqual(report["totals"]["units"], 30)

    def test_outcomes_are_counted_per_worker(self):
        events = [run("a", outcome="ok"), run("b", outcome="quota", cost=0),
                  run("c", outcome="task_fail"), run("d", outcome="transient")]
        outcomes = cost_report.build_report(events, now=NOW, days=7)[
            "by_worker"]["codex"]["outcomes"]
        self.assertEqual(
            outcomes, {"ok": 1, "quota": 1, "task_fail": 1, "transient": 1})

    def test_units_per_verified_task_includes_waste_on_failed_tasks(self):
        events = [
            run("good"), verdict("good", True),
            run("bad"), verdict("bad", False, "out_of_scope: README.md"),
        ]
        report = cost_report.build_report(events, now=NOW, days=7)
        totals = report["totals"]
        self.assertEqual(totals["verified_tasks"], 1)
        self.assertEqual(totals["failed_tasks"], 1)
        self.assertEqual(totals["units_per_verified_task"], 20)
        self.assertEqual(totals["wasted_units"], 10)

    def test_retries_are_attributed_to_the_task(self):
        events = [run("t"), verdict("t", False, "tests_failed: exit 1", attempt=1),
                  run("t"), verdict("t", True, attempt=2)]
        task = cost_report.build_report(events, now=NOW, days=7)["tasks"]["t"]
        self.assertEqual((task["runs"], task["units"], task["verified"]),
                         (2, 20, True))

    def test_window_excludes_older_events(self):
        events = [run("old", days_ago=10), run("new", days_ago=1)]
        report = cost_report.build_report(events, now=NOW, days=7)
        self.assertEqual(report["totals"]["units"], 10)
        self.assertNotIn("old", report["tasks"])

    def test_operational_events_are_counted(self):
        events = [
            event("substitution", **{"from": "codex", "to": "claude_code",
                                     "reason": "quota"}),
            event("substitution", **{"from": "codex", "to": "claude_code",
                                     "reason": "breaker_open"}),
            event("deferred_budget", worker="codex"),
            event("needs_owner", worker="claude_code", reason="quota"),
            event("review", task="t", verdict="approve"),
            event("published", task="t", url="https://example.invalid/pull/1"),
            event("sync_error", task="t"),
        ]
        counts = cost_report.build_report(events, now=NOW, days=7)["events"]
        self.assertEqual(counts["substitutions"], 2)
        self.assertEqual(counts["substitution_reasons"],
                         {"quota": 1, "breaker_open": 1})
        self.assertEqual(counts["deferred_budget"], 1)
        self.assertEqual(counts["needs_owner"], 1)
        self.assertEqual(counts["reviews"], 1)
        self.assertEqual(counts["published"], 1)
        self.assertEqual(counts["sync_errors"], 1)

    def test_units_per_verified_task_works_for_events_without_a_task_id(self):
        legacy = {"event": "run", "worker": "codex", "project": "demo",
                  "outcome": "ok", "cost": 10, "ts": ts()}
        events = [legacy, verdict("t", True)]
        totals = cost_report.build_report(events, now=NOW, days=7)["totals"]
        self.assertEqual(totals["units_per_verified_task"], 10)

    def test_events_without_a_task_id_do_not_break_the_report(self):
        legacy = {"event": "run", "worker": "codex", "project": "demo",
                  "outcome": "ok", "cost": 10, "ts": ts()}
        report = cost_report.build_report([legacy], now=NOW, days=7)
        self.assertEqual(report["totals"]["units"], 10)
        self.assertEqual(report["tasks"], {})

    def test_malformed_timestamps_are_skipped_not_fatal(self):
        events = [{"event": "run", "worker": "codex", "cost": 10, "ts": "garbage"},
                  run("ok-task")]
        report = cost_report.build_report(events, now=NOW, days=7)
        self.assertEqual(report["totals"]["units"], 10)
        self.assertEqual(report["skipped_events"], 1)


class UtilizationTests(unittest.TestCase):
    LIMITS = {"project:demo": 100, "worker:codex": 50}

    def test_utilization_uses_the_budget_window_and_warns_at_the_threshold(self):
        events = [run("a", cost=10), run("b", cost=10), run("c", cost=10),
                  run("d", cost=10), run("e", cost=10, days_ago=3)]
        report = cost_report.build_report(
            events, now=NOW, days=7, limits=self.LIMITS, window_s=86400,
            warn_ratio=0.8)
        codex = report["utilization"]["worker:codex"]
        self.assertEqual((codex["spent"], codex["limit"]), (40, 50))
        self.assertAlmostEqual(codex["ratio"], 0.8)
        self.assertEqual(codex["status"], "warn")
        self.assertEqual(report["utilization"]["project:demo"]["status"], "ok")

    def test_exhausted_scope_is_reported_as_exhausted(self):
        events = [run(str(i), cost=10) for i in range(5)]
        report = cost_report.build_report(
            events, now=NOW, days=7, limits=self.LIMITS, window_s=86400)
        self.assertEqual(report["utilization"]["worker:codex"]["status"], "exhausted")


class RenderAndCliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ledger = Path(self._tmp.name) / "ledger.jsonl"
        events = [run("a"), verdict("a", True)]
        self.ledger.write_text(
            "\n".join(json.dumps(e) for e in events) + "\n\n", "utf-8")

    def test_text_report_names_the_key_numbers(self):
        report = cost_report.build_report(
            list(cost_report.read_ledger(self.ledger)), now=NOW, days=7)
        text = cost_report.render_text(report)
        for expected in ("codex", "units", "verified", "demo"):
            self.assertIn(expected, text)

    def test_read_ledger_skips_blank_and_corrupt_lines(self):
        with self.ledger.open("a", encoding="utf-8") as stream:
            stream.write("{not json\n")
        self.assertEqual(len(list(cost_report.read_ledger(self.ledger))), 2)

    def test_missing_ledger_reads_as_empty(self):
        self.assertEqual(
            list(cost_report.read_ledger(Path(self._tmp.name) / "none.jsonl")), [])

    def test_cli_prints_json(self):
        recent = datetime.now(timezone.utc).isoformat(timespec="seconds")
        line = json.dumps(
            {"event": "run", "task": "a", "worker": "codex", "project": "demo",
             "outcome": "ok", "cost": 10, "ts": recent})
        self.ledger.write_text(line + chr(10), "utf-8")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = cost_report.main(
                ["--ledger", str(self.ledger), "--days", "1", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buffer.getvalue())["totals"]["units"], 10)

    def test_cli_without_a_ledger_or_state_dir_is_an_error(self):
        with mock.patch.dict("os.environ", {}, clear=False) as env:
            env.pop(cost_report.STATE_DIR_ENV, None)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cost_report.main([]), 2)


class GatewayCarriesTheTaskId(unittest.TestCase):
    def test_gateway_events_include_the_task_from_the_envelope(self):
        ledger = []
        gateway = wg.WorkerGateway(
            registry=[{"id": "codex", "available": True, "cost_class": "premium",
                       "fallback": None}],
            runner=lambda worker, envelope: wg.RunResult(0, "", ""),
            budget=wg.Budget({"project:demo": 100, "worker:codex": 100},
                             {"premium": 10}),
            breaker=wg.CircuitBreaker(), ledger=ledger.append, notify=lambda m: None)

        gateway.invoke("codex", {"project": "demo", "task_id": "t42"})

        self.assertEqual(ledger[0]["event"], "run")
        self.assertEqual(ledger[0]["task"], "t42")


if __name__ == "__main__":
    unittest.main()
