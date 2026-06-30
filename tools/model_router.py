#!/usr/bin/env python3
"""Model routing and fallback policy for the Pulse of Earth orchestrator.

This module is intentionally stdlib-only and secret-free.  It does not call
model providers; it evaluates diagnostics from a failed call and returns the
next safe route to try.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from typing import Any, Iterable

RATE_LIMIT_STATUSES = {429}
RATE_LIMIT_MARKERS = ("rate limit", "ratelimit", "quota", "too many requests")
DEFAULT_FREE_MODEL_MARKERS = (":free", "free", "owl-alpha")


@dataclasses.dataclass(frozen=True)
class ModelCandidate:
    """One model/provider option in priority order."""

    id: str
    provider: str
    model: str
    base_url: str | None = None
    role: str = "general"
    cost_class: str = "unknown"
    enabled: bool = True
    free_tier: bool = False
    delegate_to: str | None = None


@dataclasses.dataclass(frozen=True)
class ModelFailure:
    """Sanitized model-call failure details used by the router."""

    provider: str
    model: str
    status_code: int | None = None
    error_code: str | int | None = None
    message: str = ""
    retry_count: int = 0
    headers: dict[str, str] = dataclasses.field(default_factory=dict)


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"true", "yes", "1", "on"}


def candidate_from_mapping(data: dict[str, Any]) -> ModelCandidate:
    """Build a candidate from config data."""

    return ModelCandidate(
        id=str(data["id"]),
        provider=str(data["provider"]),
        model=str(data["model"]),
        base_url=data.get("base_url"),
        role=str(data.get("role", "general")),
        cost_class=str(data.get("cost_class", "unknown")),
        enabled=_as_bool(data.get("enabled"), True),
        free_tier=_as_bool(data.get("free_tier"), False),
        delegate_to=data.get("delegate_to"),
    )


def failure_from_mapping(data: dict[str, Any]) -> ModelFailure:
    """Build a failure object from sanitized diagnostics."""

    status = data.get("status_code")
    try:
        status = int(status) if status is not None else None
    except (TypeError, ValueError):
        status = None
    headers = {str(k): str(v) for k, v in (data.get("headers") or {}).items()}
    return ModelFailure(
        provider=str(data.get("provider", "")),
        model=str(data.get("model", "")),
        status_code=status,
        error_code=data.get("error_code"),
        message=str(data.get("message", "")),
        retry_count=int(data.get("retry_count", 0) or 0),
        headers=headers,
    )


def is_rate_limit_failure(failure: ModelFailure) -> bool:
    """Return true when diagnostics indicate quota/rate limiting."""

    text = " ".join(
        str(part).lower()
        for part in (failure.error_code, failure.message, *failure.headers.keys(), *failure.headers.values())
        if part is not None
    )
    return failure.status_code in RATE_LIMIT_STATUSES or any(marker in text for marker in RATE_LIMIT_MARKERS)


def is_openrouter_free_candidate(candidate: ModelCandidate) -> bool:
    """Detect OpenRouter free/stealth routes that should be skipped after 429."""

    if candidate.provider.lower() != "openrouter":
        return False
    haystack = f"{candidate.id} {candidate.model} {candidate.cost_class}".lower()
    return candidate.free_tier or any(marker in haystack for marker in DEFAULT_FREE_MODEL_MARKERS)


def select_fallback(
    failure: ModelFailure,
    candidates: Iterable[ModelCandidate],
    *,
    task_type: str = "general",
    attempted: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Select the next model or delegation route.

    Coding tasks route to Codex. Review/architecture tasks route to Claude.
    HTTP 429 on OpenRouter free models skips every free OpenRouter candidate
    and prefers configured paid models.
    """

    attempted_set = {str(item) for item in (attempted or [])}
    enabled = [candidate for candidate in candidates if candidate.enabled and candidate.id not in attempted_set]
    task = task_type.lower().strip()

    if task in {"code", "coding", "implement", "fix", "debug", "test", "refactor"}:
        return {"route": "delegate", "agent": "codex", "reason": "code_task"}
    if task in {"review", "architecture", "security", "audit", "design"}:
        return {"route": "delegate", "agent": "claude", "reason": "review_or_architecture_task"}

    skip_free_openrouter = failure.provider.lower() == "openrouter" and is_rate_limit_failure(failure)
    skipped: list[str] = []
    for candidate in enabled:
        if skip_free_openrouter and is_openrouter_free_candidate(candidate):
            skipped.append(candidate.id)
            continue
        if candidate.cost_class == "paid" or candidate.provider.lower() != failure.provider.lower():
            return {
                "route": "model",
                "candidate": dataclasses.asdict(candidate),
                "reason": "rate_limit_fallback" if skip_free_openrouter else "next_configured_model",
                "skipped": skipped,
            }
    return {"route": "unavailable", "reason": "no_enabled_fallback", "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Select a model fallback from sanitized JSON input")
    parser.add_argument("diagnostics_json", help="JSON with failure/candidates/task_type/attempted")
    args = parser.parse_args()
    payload = json.loads(args.diagnostics_json)
    failure = failure_from_mapping(payload.get("failure", payload))
    candidates = [candidate_from_mapping(item) for item in payload.get("candidates", [])]
    print(json.dumps(select_fallback(failure, candidates, task_type=payload.get("task_type", "general"), attempted=payload.get("attempted", [])), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
