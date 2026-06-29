# Subscription and API Architecture Audit

> Last updated: 2026-06-29
> Status: PARTIALLY_COMPLETED (needs actual billing data from owner)

## Current Authentication Methods

### OpenRouter (Primary Orchestrator)

| Setting | Value |
|---------|-------|
| Provider | OpenRouter |
| Model | owl-alpha |
| Auth | API Key (stored in Hermes config) |
| Fallback | GPT-5 mini |

### Codex CLI (Coding Worker)

| Setting | Value |
|---------|-------|
| CLI | `@openai/codex` |
| Auth method | **Unknown — needs verification** |
| API Key | (redacted in this environment) |

### Claude Code (High-Risk Reviewer)

| Setting | Value |
|---------|-------|
| CLI | `claude` |
| Auth method | **Unknown — needs verification** |
| API Key | (redacted in this environment) |

## Ownership Ui Subscriptions

| Subscription | Owner Use | Automation Need | Verdict |
|--------------|-----------|-----------------|---------|
| ChatGPT Plus/Pro | Strategy, planning, file work | Codex OAuth (if used) | NEEDS OWNER INPUT |
| Claude Pro/Max | Manual review, docs | Claude Code OAuth (if used) | NEEDS OWNER INPUT |

OpenAI direct API, Anthropic direct API, and n8n status are Owner Actions.

## n8n Decision

**Verdict: NOT_NEEDED_NOW**

Reason: Hermes already provides reasoning, routing, Codex + Claude Code provide coding + review, GitHub Actions provide CI/CD, and tools provide Linear/ Telegram/ staging automation. n8n would add complexity without filling a current gap. Reassess when inbound webhooks or external event-driven services are needed.

## Model Provider

| Role | Model | Provider | Status |
|------|-------|----------|--------|
| Primary orchestrator | owl-alpha | OpenRouter | ✅ Active |
| Fallback | GPT-5 mini | (unknown) | ⚠️ Provider unconfirmed |
| Coding | Codex | (unknown) | ⚠️ Auth unconfirmed |
| High-risk review | Claude | (unknown) | ⚠️ Auth unconfirmed |

## Recommendations

1. **Verify Codex CLI auth**: run `codex auth status` or `codex whoami`
2. **Verify Claude Code auth**: run `claude auth status`
3. **Confirm no triple billing**: ChatGPT sub + OpenAI API + OpenRouter for same model usage
4. **Document spend limits** per provider in `~/.hermes/config.yaml` or `.env`
