# Orchestrator Status

> Single source of truth. Updated after each cycle.
> Last updated: 2026-06-29 16:30 EEST

## Active Phase

**Phase A: Audit + Phase B: Self-Audit Tools**

## Current Task

Building self-audit and feedback loop system (HERMES_SELF_AUDIT_AND_FEEDBACK_LOOP_PROMPT.md)

## Last Successful Cycle

| What | Result |
|------|--------|
| CI pipeline (test + security) | ✅ Success |
| Smoke tests | ✅ 17/17 pass |
| Smoke.yml workflow | ✅ Success |
| Linear Sync workflow | ✅ Success |

## Last Failed Cycle

| What | Reason | Fix |
|------|--------|-----|
| CI Build Docker Image | `docker/build-push-action` failure | Removed temporarily |
| Linear API Auth | Security redaction of token | Added to GitHub Secrets |
 file writes | YAML/Python syntax errors | Using Python heredoc for writes |

## Open Gaps

| Gap | Status | Blocker |
|-----|--------|---------|
| Full end-to-end test | ⏳ Pending | Needs staging deploy |
| Linear idempotency test | ⏳ Pending | Needs real API key |
| Obsidian sync | � Pending | Needs Windows access |
| PostgreSQL container | � Pending | Not yet deployed |
| Docker build in CI | � Pending | Action version issue |

## Blocked Integrations

| Integration | Status | Reason |
|-------------|--------|--------|
| Linear full sync | Partial | Needs Project ID |
| Obsidian sync | Not started | Needs Windows |
| n8n | Not needed | Too early |

## Approvals Needed

| Action | Reason |
|--------|--------|
| Linear Project ID | UUID needed for sync |
| Cloudflare Proxy enable | After HTTPS verified |

## Git Info

| Item | Value |
|------|-------|
| Branch | feat/orchestrator-self-audit-loop |
| Dirty | Yes (14+ files) |
| Latest commit | local only |

## Staging Health

| Check | Status |
|-------|--------|
| Docker | ✅ Running |
| UFW | ✅ Active |
| Fail2ban | ✅ Active |
| Swap | ✅ 2GB |
| Deploy user | ✅ SSH working |

## Model Routing

| Role | Model | Status |
|------|-------|--------|
| Primary | openrouter/owl-alpha | ✅ |
| Fallback | GPT-5 mini | ✅ |
| Coding | Codex | ✅ |
| High-risk | Claude Code | ✅ |

## Cron Health

| Job | Status | Last Run |
|-----|--------|----------|
| pulse-autopilot | ✅ Active | 2026-06-29 15:43 (ok) |

## Worker Status

| Worker | Status | Notes |
|--------|--------|-------|
| Hermes | ✅ Active | Orchestrator |
| Codex | ✅ Available | skill enabled, workspace-write only |
| Claude Code | ✅ Available | skill enabled, for high-risk review |

## Owner Actions Required

1. Delete compromised PAT `ghp_7pt...`
2. Verify LINEAR_PROJECT_ID in staging secrets
3. Create Obsidian private repo
4. Install Obsidian Git plugin
