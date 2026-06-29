# Configuration Reference

> Single source of truth for TerraBits Pulse of Earth.
> Last updated: 2026-06-29
> Branch: audit/orchestrator-gap-closure

## Git

| Setting | Value |
|---------|-------|
| Repository | `IIIH23/earth-pulse-poc` |
| Default branch | `master` |
| Remote | `git@github.com:IIIH23/earth-pulse-poc.git` |
| Deploy key | `~/.ssh/deploy_staging_ed25519` (Hermes → staging) |
| Owner SSH key | `hermebot_ed25519` (Windows → staging) |

## Staging VPS

| Setting | Value |
|---------|-------|
| Hostname | `hermes-staging-01` |
| IPv4 | `157.180.125.174` |
| OS | Ubuntu 26.04 LTS |
| User | `deploy` (no sudo for sshd/ufw) |
| Root SSH | disabled |
| Docker | 29.6.1 |
| UFW ports | 22, 80, 443 |
| Swap | 2 GB |
| Project dirs | `/opt/terrabits/{apps,caddy,backups,scripts,shared}` |

## Telegram

| Setting | Value |
|---------|-------|
| Bot name | `@earthbit_bot` |
| Bot ID | `8704929397` |
| Staging chat | configured in GitHub Secrets |
| Production chat | configured in GitHub Secrets |
| GitHub Secrets | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_STAGING_CHAT_ID`, `TELEGRAM_PRODUCTION_CHAT_ID` |

## GitHub

| Setting | Value |
|---------|-------|
| Environment | `staging` (production planned) |
| Branch protection | master: PR required, status checks: `lint`, `test` |
| Dependabot | enabled (weekly) |
| Actions | ci.yml, smoke.yml, linear-sync.yml |
| Secrets (staging) | `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_STAGING_CHAT_ID`, `TELEGRAM_PRODUCTION_CHAT_ID`, `LINEAR_API_KEY`, `LINEAR_PROJECT_ID`, `CF_API_TOKEN` |

## Linear

| Setting | Value |
|---------|-------|
| Team | TerraBits |
| API Key | configured in GitHub Secrets |
| Project ID | configured in GitHub Secrets |
| Sync direction | GitHub/ROADMAP → Linear (one-way) |
| Workflow | `.github/workflows/linear-sync.yml` |

## Cloudflare

| Setting | Value |
|---------|-------|
| Zone | `terrabits.org` |
| Zone ID | configured in GitHub Secrets |
| Staging record | `earthbit.staging.terrabits.org` → `157.180.125.174` (DNS only, not proxied) |
| API Token | configured in GitHub Secrets (needs DNS Edit permission) |

## Obsidian

| Setting | Value |
|---------|-------|
| Vault path (Windows) | `C:\Obsidian\Pulse of Earth` |
| Sync method | Git (planned) |
| Bridge | private Git repository (recommended) |

## Model Routing

| Role | Model | Notes |
|------|-------|-------|
| Primary orchestrator | `openrouter/owl-alpha` | Current active model |
| Fallback/low-cost | GPT-5 mini | For cron, brief reports |
| Coding worker | Codex CLI | `--sandbox workspace-write` |
| High-risk reviewer | Claude Code | For security, infra, secrets |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/bootstrap-staging.sh` | Idempotent staging VPS bootstrap |
| `scripts/verify-staging.sh` | Post-bootstrap verification |
| `scripts/lockdown-staging-ssh.sh` | SSH lockdown (PermitRootLogin no) |
| `scripts/verify-staging-ssh.sh` | Verify lockdown |
| `scripts/check-health.sh` | Docker + HTTP + system health |
| `scripts/rollback.sh` | Save/restore container releases |
| `scripts/send-telegram-alert.sh` | Telegram notifications |
| `scripts/setup-github.py` | Branch protection + environments via API |
| `scripts/create-dns.py` | Cloudflare DNS record creation |

## Tools

| Tool | Purpose |
|------|---------|
| `tools/inventory.py` | File inventory |
| `tools/healthcheck.py` | System health checks |
| `tools/rollback.py` | Docker compose release management |
| `tools/telegram_notify.py` | Telegram alerts |
| `tools/linear_sync.py` | Linear issue sync |
| `tools/github_sync.py` | GitHub drift detection |
| `tools/obsidian_sync.py` | Obsidian sync (planned) |
| `tools/linear_setup.py` | Linear project/label creation |

## Workflows

| Workflow | File | Trigger |
|----------|------|---------|
| CI | `.github/workflows/ci.yml` | push/PR to master/main |
| Smoke | `.github/workflows/smoke.yml` | push/PR |
| Linear Sync | `.github/workflows/linear-sync.yml` | push to master, manual |

## Discrepancies Found

| Issue | Status |
|-------|--------|
| `smoke.yml` triggers on all branches | OK for now |
| `ci.yml` references `master` and `main` | main does not exist, only master used |
| `linear-sync.yml` only on master | OK |
| `scripts/trigger_workflow.py` leftover | Should be cleaned up |
| `scripts/linear_test.py`, `linear_auth.py`, `linear_survey.py`, `linear_setup.py` | Test scripts, should be cleaned up |
