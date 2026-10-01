# TerraBits Ecosystem — Current State Analysis

> Last updated: 2026-06-28
> Purpose: Analyze existing Linear workspace and Obsidian vault for integration

## Existing Artifacts

### Linear Workspace
- **URL:** (fill after access)
- **Workspace name:** TerraBits
- **Projects:** Pulse of Earth
- **Team members:** (to be documented)
- **Existing labels:** (to be documented)
- **Existing issues:** (to be documented)

### Obsidian Vault
- **Path:** `C:\Obsidian\Pulse of Earth` (or similar)
- **Existing folders:** (to be scanned)
- **Existing notes:** (to be scanned)
- **Templates:** (to be scanned)
- **Tags:** (to be scanned)

### GitHub Repository
- **URL:** https://github.com/IIIH23/earth-pulse-poc
- **Default branch:** main
- **Active branches:** master, feat/staging-bootstrap, feat/orchestrator-phase0
- **Staging environment:** configured with STAGING_HOST, STAGING_USER secrets
- **CI:** .github/workflows/ci.yml

### Staging VPS
- **Host:** hermes-staging-01
- **IPv4:** 203.0.113.10
- **OS:** Ubuntu 26.04 LTS
- **Services:** Docker 29.6.1, UFW, Fail2ban, unattended-upgrades
- **SSH:** deploy user (key-only), root disabled
- **Pending:** /opt/terrabits/ structure not yet created
- **Pending:** PostgreSQL container not yet deployed

### Telegram
- **Bot:** TerraBits Infra Bot (created)
- **Staging chat:** (ID needed)
- **Production chat:** (ID needed)

## Integration Status

| Integration | Status | Blocker |
| --- | --- | --- |
| GitHub → CI/CD | � configured | needs first push trigger |
| GitHub → Staging deploy | ⏳ configured | needs staging bootstrap |
| Cloudflare DNS | ⏳ pending | needs A record creation |
| Linear ↔ GitHub | ⏳ not started | needs API key + workspace analysis |
| Obsidian ↔ GitHub | ⏳ not started | needs vault path + Git sync |
| Telegram alerts | ⏳ not started | needs bot token + chat IDs |
| PostgreSQL backups | � not started | needs Object Storage |
| Monitoring | � not started | needs systemd deployment |

## Next Steps

1. Create Cloudflare A record → enables staging domain
2. Get Linear API key → analyze workspace
3. Get Obsidian vault access → scan notes
4. Get Telegram bot token + chat IDs → configure alerts
5. Bootstrap staging VPS structure
6. Deploy PostgreSQL container
7. Trigger first CI run
