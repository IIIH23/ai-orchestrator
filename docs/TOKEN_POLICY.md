# Token and Cost Policy

This policy consolidates the rules that were spread across `AGENTS.md`,
`ORCHESTRATOR_POLICY.md`, `docs/MODEL_ROUTING.md`, `AUTOPILOT_PROMPT.md` and
`NIGHT_SHIFT_PROMPT.md`. It states what is enforced by code, what is only a
convention, and how the numbers get calibrated from data.

## Principles

1. **Deterministic first.** Anything that code can decide costs no tokens:
   routing (`tools/agent_router.py`), verification (`tools/task_verifier.py`),
   budget checks, git, the ledger, reports.
2. **Cheapest sufficient step.** A step goes to the next rung of the ladder
   only when the previous one cannot do it.
3. **Verify before spending again.** A retry is justified by a failed
   verifier result, never by a worker's own claim.
4. **Fail closed, never silent.** An exhausted budget defers the task; an
   exhausted fallback chain asks the owner; every substitution is logged and
   announced.
5. **Measure before tuning.** Limits are changed from `tools/cost_report.py`
   output, not from intuition.

## Ladder

| Rung | What runs | Cost | Used for |
| --- | --- | --- | --- |
| 0 | code: router, verifier, linters, tests, git | no tokens | everything that has a deterministic answer |
| 1 | cheap model through Hermes (GPT-5 mini; owl-alpha as orchestrator) | low | short plans, summaries, cron checks, reports |
| 2 | Codex CLI, `workspace-write` | premium | implementation inside `allowed_paths` |
| 3 | Claude Code, read-only review | premium | independent review of high-risk or sensitive tasks only |

The producing worker never reviews its own output.

## Tiers by risk

| Risk | Owner approval | Worker | Independent review | Attempts (target) |
| --- | --- | --- | --- | --- |
| low | no | Codex | no | 2 |
| medium | before work starts | Codex | only for sensitive task types | 2 |
| high | before work starts | Codex | Claude Code, mandatory; unavailable reviewer blocks the task | 1 |

Approval and review are enforced by code. The attempt targets are not yet
derived from the risk level: every task gets the `max_attempts` written in its
spec (default 2).

Sensitive task types (always reviewed): security, architecture,
infrastructure, permissions, rollback, database, deploy.

## Budgets

- Spend is counted in abstract **units** per worker `cost_class`
  (`cheap 1`, `standard 3`, `premium 10`) over a rolling window. Subscription
  CLIs do not report a reliable price, so units measure *relative* effort.
- Scopes: `project:<id>` and `worker:<id>`. A scope without a configured
  limit is **denied**, never unlimited.
- At 100% of a limit the task is deferred (`deferred_budget`) and retried
  after the window moves; it is never dropped.
- Warning level is 80%: `tools/cost_report.py` marks the scope `warn`.
- The limits in `config/orchestrator.yaml` are **interim**. Calibrate after
  one week of ledger data: set each limit to roughly 1.5x the busiest day's
  spend, then review weekly.

## Per-run limits

- One task per cycle; a task that is too large is split and only its first
  independently testable part is done.
- `max_attempts` per task (see tiers); the worker timeout comes from the
  registry; the verifier timeout is bounded.
- Autopilot cycles: at most 12 tool actions, no repeated full audits, no
  secondary reviews after green tests unless the risk is high, final report
  under 200 words.
- Worker prompts are built from the task envelope only. A stage receives the
  structured output of the previous stage, never the whole conversation.

## Provider-side caps (defense in depth)

Local accounting can be wrong or bypassed, so a second limit belongs to the
provider:

- OpenRouter key: set a credit limit on the key used by Hermes.
- Direct API keys (OpenAI, Anthropic), if any: set monthly spend limits in
  the provider console.
- Subscription logins (Codex via ChatGPT, Claude Code via Claude) are
  bounded by the plan; verify the plan limits and what happens after they
  run out.

Status: **not verified from this repository** - these are console settings.

## Measurement and review

- `python tools/cost_report.py --days 7` prints spend per worker and project,
  units per verified task, units wasted on failed tasks, substitutions by
  reason, deferrals, owner escalations and budget utilization. `--json`
  gives the same data to other tools.
- Weekly review (no model needed): read the report, then act on it:
  - many `quota` outcomes: the worker's limit is too low, or it is overused;
  - many failed tasks: the task envelopes are too vague, not the model too weak;
  - units per verified task rising: look at retries before raising limits.
- A rule changes only with a number from the report in the PR description.

## Conflicts in the old rules and how they were resolved

| Old rules | Resolution |
| --- | --- |
| `AGENTS.md`: "do not invoke a second model unless explicitly requested" vs `ORCHESTRATOR_POLICY.md`: "Claude review is automatic for high-risk" | A second model runs only through the review gate, for high-risk or sensitive tasks. Routine and low-risk work never gets one. |
| Who routes: GPT-5 mini (`AGENTS.md`, autopilot) vs owl-alpha primary (`ORCHESTRATOR_POLICY.md`, `MODEL_ROUTING.md`) | Routing between workers is deterministic code. In Hermes, owl-alpha stays the orchestrator and GPT-5 mini the cheap/fallback model, as in `MODEL_ROUTING.md`. |
| `AUTOPILOT_PROMPT.md`: report under 300 words and under 200 words | 200 words. |
| `MODEL_ROUTING.md`: "retry once with a narrower scope" vs the daemon rerunning the same prompt | Proposed: pass the verifier's failure reason to the retry (not implemented). |
| "Budget exceeded: stop, report usage" | Implemented as deferral plus `cost_report`. |

## Enforcement status

| Rule | Where | Status |
| --- | --- | --- |
| Deterministic routing and verification | `agent_router`, `task_verifier` | enforced |
| Budget per project and worker, deny without a limit | `worker_gateway.Budget`, persisted in SQLite | enforced |
| Defer at 100% | dispatcher + `deferred_budget` | enforced |
| Loud fallback, owner when the chain is empty | `worker_gateway` | enforced |
| Mandatory Claude review for high-risk/sensitive | `agent_router`, `review_gate` | enforced; reviewer needs a logged-in Claude Code on the host |
| Owner approval for non-low risk | `dispatcher`, `task_queue` | enforced |
| Attempt cap per task | `task_queue`, `dispatcher` | enforced (`max_attempts`) |
| Attempt cap derived from the risk tier | - | proposed |
| 80% warning | `cost_report` | report only; no automatic alert yet |
| Weekly cost review | `cost_report` | manual; not scheduled |
| Retry with failure feedback | - | proposed |
| Green-baseline check before spending tokens | - | proposed |
| Actual token usage in the ledger | - | proposed (Claude Code returns `total_cost_usd`; Codex output needs parsing) |
| Hermes (VPS) usage in the ledger | - | not covered: it runs outside this daemon |
| Provider-side caps | provider consoles | owner action, unverified |

## Considered and not adopted now

Following ADR-0001, a component is added when its trigger fires:

| Option | Trigger |
| --- | --- |
| LiteLLM proxy for budgets on direct API calls | Hermes or the planning stages call provider APIs directly at volume; it cannot see CLI workers |
| Langfuse / OpenTelemetry for LLM traces | the JSONL ledger and report stop answering the questions asked |
| Prometheus and Grafana dashboard | more than one host, or the weekly report is read daily |
| Local models for mechanical tasks | a measured share of spend goes to mechanical steps |
