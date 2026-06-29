# Orchestrator Gap Backlog

> Last updated: 2026-06-29

## P0: Security or Data Loss

| ID | Gap | Impact | Fix | Risk | Owner Action |
|----|-----|--------|-----|------|--------------|
| P0-1 | Compromised PAT ghp_7pt... | Token leak | Revoke immediately | Critical | Owner |
| P0-2 | Old Linear API Key | Unauthorized access | Revoke immediately | Critical | Owner |

## P1: Main User Journey Broken

| ID | Gap | Impact | Fix | Risk | Owner Action |
|----|-----|--------|-----|--------------|--------------|
| P1-1 | No real app deployed to staging | E2E cannot happen | Deploy earthbit-health | Low | Merge PR |
| P1-2 | Obsidian bridge not active | Knowledge loop broken | Create private repo + plugin | Low | Owner |
| P1-3 | Multi-project isolation missing | Cannot manage multiple projects | Configure Hermes profiles | Medium | Architect |
| P1-4 | Codex not auto-invoked | Coding tasks need manual delegation | Define task handoff protocol | Medium | Hermes |

## P2: Significant Limitation

| ID | Gap | Impact | Fix | Risk | Owner Action |
|----|-----|--------|-----|--------------|--------------|
| P2-1 | No browser tool | Research limited | Document limitation + use web_search | Low | Hermes |
| P2-2 | Actions not pinned to SHA | Supply chain risk | Pin all actions to SHA | Low | Hermes |
| P2-3 | Retry logic missing | Notifications fail silently | Implement retry in Telegram tool | Medium | Hermes |
| P2-4 | No budget tracking | Cannot track spend | Add spend monitoring | Medium | Owner |

## P3: Optimization

| ID | Gap | Impact | Fix | Risk | Owner Action |
|----|-----|--------|-----|--------------|--------------|
| P3-1 | Decision log not auto-updated | History lost | Cron: review + update log | Low | Hermes |
| P3  docs | Documentation drift | Weekly review + sync | Low | Hermes |
| P3-3 | Telegram alert throttling | Alert storms | Implement cooldown | Low | Hermes |

## Deferred

| ID | Gap | Reason | Review |
|----|-----|--------|--------|
| D-1 | n8n integration | Not needed yet | When webhooks needed |
| D-2 | Sentry | Too early | After first production deploy |
| D-3 | Team permissions | Single user yet | When team grows |
| D-4 | NotebookLM | No integration | After research provider chosen |
