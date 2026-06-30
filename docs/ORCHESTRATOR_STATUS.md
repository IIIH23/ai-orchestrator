# Orchestrator Status

> Last updated: 2026-06-29
> Branch: feat/orchestrator-critical-limitations

## Current State

| Area | Status | Notes |
| --- | --- | --- |
| GitHub repo | ✅ Operational | IIIH23/earth-pulse-poc (public), SSH key auth |
| Git push/pull | ✅ Working | `git@github.com:IIIH23/earth-pulse-poc.git` via `github_ed25519` |
| Branch protection | ⚠️ Not enforced | API shows protection disabled; CI still runs on push/PR |
| CI/CD | ✅ Working | ci.yml + smoke.yml, built-in GITHUB_TOKEN |
| Dependabot | ✅ Enabled | pip, github-actions, docker |
| GHCR | 🔴 Not configured | No push workflow active yet |
| Environments | ✅ Created | staging, production, earth-pulse-poc |
| Secrets | ⚠️ Unknown | Cannot verify without GH admin token |
| Linear Sync | ✅ Working | Uses LINEAR_API_KEY via workflow_dispatch |
| Telegram | ✅ Working | Uses TELEGRAM_BOT_TOKEN env var |
| Hermes cron | ✅ Running | pulse-autopilot every 120m |
| PAT dependency | ✅ Eliminated | Old PAT revoked; .github_pat removed + gitignored |
| gh CLI | ⚠️ Installed, not auth | v2.95.0; no operational dependency on it |

## Authentication Map (post-PAT-revocation)

| Component | Auth Method | Status |
| --- | --- | --- |
| git push/pull | SSH key (github_ed25519) | ✅ Verified |
| GitHub Actions | built-in GITHUB_TOKEN | ✅ Auto-provisioned |
| Linear Sync | LINEAR_API_KEY secret | ✅ Via workflow_dispatch |
| Telegram | TELEGRAM_BOT_TOKEN env | ✅ Independent |
| Hermes cron | SSH key | ✅ No PAT needed |
| setup-github.py | GITHUB_TOKEN env (default dry-run) | ✅ No file storage |
| add_secrets.py | GITHUB_TOKEN env (default dry-run) | ✅ No file storage |

## Security Notes

- `.github_pat` file: removed from filesystem and gitignored
- All GitHub API scripts: default `--dry-run` mode, accept token via `GITHUB_TOKEN` env or `--token` flag
- No token values stored in git history (verified)
- Recommended future: use `GH_ADMIN_TOKEN` for local admin scripts, distinct from CI `GITHUB_TOKEN`

## Backlog — Low-Risk Refactor

- [ ] Local GitHub admin scripts: use `GH_ADMIN_TOKEN` env var instead of `GITHUB_TOKEN`
- [ ] Token input: runtime environment or stdin only (never file-based)
- [ ] Default mode: keep `--dry-run` as default for all admin scripts
- [ ] Remove any residual `.github_pat` references from documentation
