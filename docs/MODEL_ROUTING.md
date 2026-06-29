# Model Routing

> Last updated: 2026-06-29

## Active Configuration

| Setting | Value |
|---------|-------|
| Primary model | `openrouter/owl-alpha` |
| Provider | `openrouter` |
| Base URL | `https://openrouter.ai/api/v1` |
| API mode | `chat_completions` |
| Max turns | 150 |

## Roles

| Role | Model | When to use |
|------|-------|-------------|
| **Primary orchestrator** | `openrouter/owl-alpha` | Dialogue, strategy, planning, discovery, synthesis, reports |
| **Fallback/low-cost** | GPT-5 mini (via OpenAI) | Cron orchestration, brief checks, routing, low-cost automation |
| **Coding worker** | Codex CLI | Code implementation, refactoring, tests, scripts, Dockerfiles |
| **High-risk reviewer** | Claude Code | Security, infrastructure, secrets, database migrations, rollback logic |

## Routing Decision Tree

```
Task received
  ├─ Is it substantial code implementation? → Codex CLI (--sandbox workspace-write)
  ├─ Is it high-risk (security/infra/secrets)? → Claude Code (review)
  ├─ Is it brief check/report/cron? → GPT-5 mini
  └─ Default → owl-alpha (orchestrator)
```

## Fallback Chain

```
owl-alpha (primary)
  ↓ (if unavailable)
GPT-5 mini (fallback)
  ↓ (if unavailable)
Error + Telegram alert to owner
```

## Profile Mapping

| Profile | Model | Primary Use |
|---------|-------|-------------|
| `default` (owner) | owl-alpha | Orchestration, strategy, approvals |
| `development` | owl-alpha + Codex | Coding, tests, CI/CD |
| `architecture` | owl-alpha + Claude | ADR, security review |
| `research` | owl-alpha | Analysis, knowledge notes |
| `devops` | owl-alpha + Codex | Infrastructure, monitoring |
| `design` | owl-alpha | UX specs, design briefs |
| `finance` | GPT-5 mini | Budgets, cost estimates (read-only) |
| `team` | GPT-5 mini | Task tracking, Linear sync |

## Cron Configuration

| Job | Model | Schedule |
|-----|-------|----------|
| `pulse-autopilot` | `openrouter/owl-alpha` | every 120m |

## Verification

Run: `bash scripts/verify-model-routing.sh`
