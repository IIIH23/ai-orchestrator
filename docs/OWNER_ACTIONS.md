# Owner Actions

> Generated: 2026-06-27
> Consolidation of all owner-required actions across phases 0-10

## GitHub Setup

| # | Action | Phase | Priority |
| --- | --- | --- | --- |
| 1 | `git remote add origin <github-url>` | 0 | 🔴 Critical |
| 2 | Create GitHub repository (private) | 0 | 🔴 Critical |
| 3 | Push all branches to remote | 0 | 🔴 Critical |
| 4 | ~~Enable branch protection on main~~ | 2 | ✅ COMPLETED |
| 5 | ~~Require CI status checks~~ | 2 | ✅ COMPLETED |
| 6 | ~~Disable force push on main~~ | 2 | ✅ COMPLETED |
| 7 | ~~Create staging environment~~ | 2 | ✅ COMPLETED |
| 8 | ~~Add secrets to staging environment~~ | 2 | ✅ COMPLETED |
| 9 | ~~Create production environment~~ | 2 | ✅ COMPLETED |
| 42 | ~~Revoke old PAT ghp_7pt...~~ | Security | ✅ COMPLETED |

## GitHub Secrets (staging environment)

| Secret | Value | Purpose |
| --- | --- | --- |
| STAGING_HOST | 157.180.125.174 | Deploy SSH |
| STAGING_USER | deploy | SSH user |
| STAGING_SSH_KEY | Ed25519 private key | SSH auth |

## GitHub Secrets (production environment — future)

| Secret | Value | Purpose |
| --- | --- | --- |
| PROD_HOST | (future) | Deploy SSH |
| PROD_USER | deploy | SSH user |
| PROD_SSH_KEY | (future) | SSH auth |
| PROD_DB_PASSWORD | (future) | Database |

## Cloudflare Setup

| # | Action | Phase | Priority |
| --- | --- | --- | --- |
| 10 | Create DNS A record: earthbit.staging → 157.180.125.174 | 4 | 🔴 Critical |
| 11 | Provide Cloudflare Zone ID (terrabits.org) | 4 | 🟡 Medium |
| 12 | Provide API token (Zone.DNS permissions) | 4 | 🟡 Medium |
| 13 | After HTTPS: enable Cloudflare Proxy | 4 | 🟡 Medium |
| 14 | Provide team emails for Access allowlist | 4 | 🟡 Medium |
| 15 | Create Cloudflare Access application (staging) | 4 | 🟢 Low |
| 16 | Create service token for CI/CD | 4 | 🟢 Low |

## Linear Setup

| # | Action | Phase | Priority |
| --- | --- | --- | --- |
| 17 | Create Linear workspace (if not exists) | 5 | 🟡 Medium |
| 18 | Create Pulse of Earth project | 5 | 🟡 Medium |
| 19 | Provide Linear API key | 5 | 🟡 Medium |
| 20 | Create labels (discovery, architecture, backend, etc.) | 5 | 🟢 Low |
| 21 | Create team and invite members | 5 | 🟢 Low |

## Obsidian Setup

| # | Action | Phase | Priority |
| --- | --- | --- | --- |
| 22 | Install Obsidian Git plugin OR Syncthing | 6 | 🟡 Medium |
| 23 | Configure sync with repository | 6 | 🟡 Medium |
| 24 | Share vault path for local development | 6 | 🟢 Low |

## Hetzner / Infrastructure

| # | Action | Phase | Priority |
| --- | --- | --- | --- |
| 25 | Verify Hetzner Firewall mirrors UFW (22, 80, 443) | 9 | 🟡 Medium |
| 26 | Set up Hetzner Private Network (Hermes ↔ Staging) | 9 | 🟡 Medium |
| 27 | Create Hetzner Object Storage bucket (PostgreSQL backups) | 8 | 🟡 Medium |
| 28 | Provide S3 credentials (access_key, secret_key, endpoint) | 8 | 🟡 Medium |
| 29 | Provide backup encryption key | 8 | 🟡 Medium |

## Telegram Setup

| # | Action | Phase | Priority |
| --- | --- | --- | --- |
| 30 | Create Telegram bot (if not exists) | 3 | 🟡 Medium |
| 31 | Provide bot token | 3 | 🟡 Medium |
| 32 | Provide staging chat ID | 3 | 🟡 Medium |
| 33 | Provide production chat ID (future) | 3 | 🟢 Low |

## Monitoring / Systemd

| # | Action | Phase | Priority |
| --- | --- | --- | --- |
| 34 | Deploy health check.timer systemd unit | 8 | 🟡 Medium |
| 35 | Deploy monitoring scripts to /opt/terrabits/scripts/ | 8 | 🟡 Medium |

## n8n (Future)

| # | Action | Phase | Priority |
| --- | --- | --- | --- |
| 36 | Decide: self-hosted vs n8n Cloud | 7 | 🟢 Low |
| 37 | If self-hosted: provision VPS | 7 | 🟢 Low |
| 38 | Approve n8n installation | 7 | 🟢 Low |

## Deployment (first manual)

| # | Action | Phase | Priority |
| --- | --- | --- | --- |
| 39 | Bootstrap /opt/terrabits/ directory structure | 8 | 🟡 Medium |
| 40 | Create .env file on staging | 8 | 🟡 Medium |
| 41 | Deploy first Docker image to staging | 10 | 🟡 Medium |

## Summary

| Priority | Count | Actions |
| --- | --- | --- |
| 🔴 Critical | 0 | (all completed) |
| 🟡 Medium | 22 | Cloudflare, Linear, Obsidian, Telegram, Hetzner, systemd |
| 🟢 Low | 10 | Access policies, n8n, future setup |
| ✅ Completed | 11 | GitHub setup, secrets, branch protection, environments, PAT revocation |
| **Total** | **32 active + 11 done** | |

## Suggested Order

1. **Day 1**: GitHub setup (#1-9) → everything else depends on this
2. **Day 2**: Cloudflare DNS (#10) → staging accessible via domain
3. **Day 2**: Telegram (#30-32) → notifications working
4. **Day 2**: Bootstrap staging (#39-40) → app directories
5. **Day 3**: Hetzner resources (#25-29) → backups, private network
6. **Day 3**: Linear (#17-18, #20-21) → task tracking
7. **Day 3**: Obsidian (#22-24) → documentation sync
8. **Day 4**: Monitoring (#34-35) → health checks automated
9. **Day 5**: n8n decision (#36-38) → optional automation
