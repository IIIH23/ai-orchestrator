#!/usr/bin/env python3
"""Fail-closed Claude Code review gate for policy-sensitive tasks."""

from __future__ import annotations

import argparse
import dataclasses
import enum
import json
import pathlib
import sys
from collections.abc import Callable, Mapping, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tools.agent_router import REGISTRY_PATH, RouteDecision, load_registry, route_task
from tools.agent_runtime import RuntimeHealth, collect_availability
from tools.claude_code_adapter import ClaudeRequest, ClaudeResult, run_claude


class ReviewGateError(RuntimeError):
    """Raised when a mandatory review cannot produce a valid verdict."""


class Verdict(enum.StrEnum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    BLOCKED = "blocked"


Reviewer = Callable[[ClaudeRequest], ClaudeResult]
AvailabilityProvider = Callable[
    [pathlib.Path], Mapping[str, bool] | RuntimeHealth
]


@dataclasses.dataclass(frozen=True)
class ReviewGateResult:
    status: str
    route: RouteDecision
    verdict: Verdict | None = None
    summary: str | None = None
    findings: tuple[str, ...] = ()
    session_id: str | None = None
    cost_usd: float | None = None
    health: RuntimeHealth | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "route": self.route.as_dict(),
            "verdict": self.verdict.value if self.verdict else None,
            "summary": self.summary,
            "findings": list(self.findings),
            "session_id": self.session_id,
            "cost_usd": self.cost_usd,
            "health": (
                {
                    agent_id: dataclasses.asdict(status)
                    for agent_id, status in self.health.statuses.items()
                }
                if self.health
                else None
            ),
        }


def _requires_claude(route: RouteDecision) -> bool:
    if route.primary and route.primary.get("id") == "claude_code":
        return True
    return any(reviewer.get("id") == "claude_code" for reviewer in route.reviewers)


def _review_prompt(task_type: str, risk_level: str, prompt: str) -> str:
    return f"""You are the independent policy reviewer for AI Orchestrator.
Task type: {task_type}
Risk level: {risk_level}

Review request:
{prompt}

Return JSON only with exactly this shape:
{{
  "verdict": "approve" | "request_changes" | "blocked",
  "summary": "non-empty concise summary",
  "findings": ["specific finding"]
}}
Do not wrap the JSON in Markdown.
"""


def _parse_verdict(result: ClaudeResult) -> tuple[Verdict, str, tuple[str, ...]]:
    try:
        payload = json.loads(result.result)
    except json.JSONDecodeError as exc:
        raise ReviewGateError("Claude review verdict is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ReviewGateError("Claude review verdict must be a JSON object")

    try:
        verdict = Verdict(payload.get("verdict"))
    except (TypeError, ValueError) as exc:
        raise ReviewGateError("Claude review verdict is invalid") from exc
    summary = payload.get("summary")
    findings = payload.get("findings")
    if not isinstance(summary, str) or not summary.strip():
        raise ReviewGateError("Claude review verdict summary is invalid")
    if not isinstance(findings, list) or not all(
        isinstance(finding, str) and finding.strip() for finding in findings
    ):
        raise ReviewGateError("Claude review verdict findings are invalid")
    return verdict, summary.strip(), tuple(finding.strip() for finding in findings)


def runtime_availability(registry_path: pathlib.Path) -> RuntimeHealth:
    return collect_availability(load_registry(registry_path))


def run_review_gate(
    task_type: str,
    risk_level: str,
    prompt: str,
    cwd: pathlib.Path,
    *,
    registry_path: pathlib.Path = REGISTRY_PATH,
    availability: Mapping[str, bool] | None = None,
    availability_provider: AvailabilityProvider = runtime_availability,
    reviewer: Reviewer = run_claude,
) -> ReviewGateResult:
    health: RuntimeHealth | None = None
    if availability is None:
        observed = availability_provider(registry_path)
        if isinstance(observed, RuntimeHealth):
            health = observed
            availability = observed.availability
        else:
            availability = observed
    route = route_task(
        task_type,
        risk_level,
        registry_path=registry_path,
        availability=availability,
    )
    if route.blocked_reason:
        raise ReviewGateError(route.blocked_reason)
    if not _requires_claude(route):
        return ReviewGateResult(status="not_required", route=route, health=health)

    request = ClaudeRequest(
        prompt=_review_prompt(task_type, risk_level, prompt),
        cwd=cwd,
        mode="review",
    )
    try:
        result = reviewer(request)
    except Exception as exc:
        raise ReviewGateError(f"Claude review execution failed: {exc}") from exc
    verdict, summary, findings = _parse_verdict(result)
    return ReviewGateResult(
        status="completed",
        route=route,
        verdict=verdict,
        summary=summary,
        findings=findings,
        session_id=result.session_id,
        cost_usd=result.cost_usd,
        health=health,
    )


Gate = Callable[..., ReviewGateResult]


def main(argv: Sequence[str] | None = None, *, gate: Gate = run_review_gate) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_type")
    parser.add_argument("risk_level", choices=("low", "medium", "high"))
    parser.add_argument("--prompt", help="review request; stdin is used when omitted")
    parser.add_argument("--cwd", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--registry", type=pathlib.Path, default=REGISTRY_PATH)
    args = parser.parse_args(argv)
    prompt = args.prompt if args.prompt is not None else sys.stdin.read()
    try:
        result = gate(
            args.task_type,
            args.risk_level,
            prompt,
            args.cwd,
            registry_path=args.registry,
        )
    except ReviewGateError as exc:
        print(
            json.dumps({"status": "error", "error": str(exc)}),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result.as_dict(), ensure_ascii=False))
    if result.verdict in {Verdict.REQUEST_CHANGES, Verdict.BLOCKED}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
