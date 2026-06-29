# Final Orchestrator Architecture Decision

> Last updated: 2026-06-29

## Recommended: Hybrid Architecture

```
Owner (chat, Telegram, web)
  ↓
Hermes (brain / router)
  ├── OpenRouter (primary reasoning: owl-alpha)
  ├── GPT-5 mini (fallback, low-cost tasks)
  ├── Codex CLI (coding worker, --sandbox workspace-write)
  ├── Claude Code (high-risk reviewer)
  ├── GitHub Actions (CI/CD)
  ├── Linear (task tracking via tools/linear_sync.py)
  ├── Telegram (alerts via tools/telegram_notify.py)
  ├── Staging VPS (deploy, monitoring)
  └── Obsidian Bridge (private Git repo, future)
```

## Why Not n8n

- Hermes already routes between providers and workers
- GitHub Actions handles CI/CD
- Tools handle event-driven tasks (Linear sync, Telegram alerts)
- n8n would duplicate orchestration without filling a clear gap
- Future: add n8n only when inbound webhooks from external services needed

## Provider Strategy

| Provider | Use | Risk |
|----------|-----|------|
| OpenRouter | Primary orchestration, model access | Single point of failure; direct provider fallback recommended |
| ChatGPT subscription | Owner UI, Codex OAuth | Account/session dependency |
| Claude subscription | Owner UI, Claude Code OAuth | Account/session dependency |
| Direct APIs | Machine-to-machine only | Billing complexity |

## Cost Controls

- Per-model spend limits
- GPT-5 mini for low-cost/cron tasks
- Codex/Claude only for their specific scopes
- Telegram alerts model: INFO (no alert fatigue)

## What Owner Must Verify

1. Codex CLI auth method (`codex auth status`)
2. Claude Code auth method (`claude auth status`)
3. No triple billing (subscription + API + OpenRouter)
4. Spend limits set in OpenRouter dashboard
5. Direct API keys only where subscriptions/OAuth don't cover
