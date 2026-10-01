# Integration Matrix

> Generated: 2026-06-27
> Status: current

## Integrations

| Integration | Status | Priority | Owner | Notes |
| --- | --- | --- | --- | --- |
| GitHub (remote) | ❌ not configured | high | owner | No git remote; needs `git remote add` |
| GitHub Branch Protection | ❌ not configured | high | owner | Requires admin rights |
| GitHub Actions CI | ⚠️ partial | high | auto | smoke.yml exists; no full pipeline |
| GHCR | ❌ not configured | high | owner | Needs registry auth |
| Dependabot | ❌ not configured | medium | owner | Needs .github/dependabot.yml |
| GitHub Environments | ❌ not configured | high | owner | staging + production |
| Hetzner Cloud | ⚠️ manual | high | owner | VPS exists; no Terraform |
| Hetzner Private Network | ❌ not configured | high | owner | Needs verification |
| Hetzner Firewall | ⚠️ unknown | high | owner | Policy says enabled; unverified |
| Hetzner Object Storage | ❌ not configured | high | owner | For PostgreSQL backups |
| Cloudflare DNS | ❌ not configured | high | owner | app.staging.example.org |
| Cloudflare Access | ❌ not configured | medium | owner | After HTTPS confirmed |
| Cloudflare Proxy | ❌ not configured | medium | owner | After HTTPS confirmed |
| Docker (staging) | ✅ working | high | auto | Docker 29.6.1 installed |
| Docker Compose (staging) | ✅ working | high | auto | Plugin installed |
| Caddy | ❌ not configured | high | auto | No config yet |
| PostgreSQL | ❌ not configured | high | owner | Needs container + volume |
| UFW | ✅ working | high | auto | 22/80/443 allowed |
| Fail2ban | ✅ working | high | auto | sshd jail active |
| unattended-upgrades | ✅ working | high | auto | Enabled |
| SSH lockdown | ✅ working | high | auto | PermitRootLogin no |
| Linear | ❌ not configured | medium | owner | Needs API key |
| Obsidian | ❌ not configured | medium | owner | Needs vault path + sync method |
| n8n | ❌ not configured | low | auto | Architecture only; no install without approval |
| Telegram Alerts | ❌ not configured | high | owner | Needs bot token + chat ID |
| Monitoring | ❌ not configured | medium | auto | Lightweight scripts |
| Backups (PostgreSQL) | ❌ not configured | high | owner | Needs Object Storage |
| Secrets Management | ❌ not configured | high | owner | GitHub Environments |
| Trivy Scan | ❌ not configured | high | auto | In CI pipeline |
| Cosign Signing | ❌ not configured | high | auto | In CI pipeline |
| SBOM | ❌ not configured | high | auto | In CI pipeline |

## Legend

- ✅ working: tested and operational
- ⚠️ partial: partially implemented or unverified
- ❌ not configured: not started
- auto: can be done autonomously
- owner: requires owner action

## Integration Dependencies

```
GitHub remote → Branch protection → CI workflow → GHCR → Trivy → Cosign → Staging deploy
                                          ↓
                                     Dependabot

Hetzner Cloud ← Terraform (owner) → Private Network → Object Storage (owner)
      ↓
  VPS (staging) ← Docker ← Caddy ← Cloudflare DNS (owner)
      ↓
  PostgreSQL → Backups → Object Storage (owner)

Telegram Bot (owner) ← Monitoring → Health checks

Linear API (owner) ← Task sync ← Autopilot

Obsidian vault (owner) ← Sync bridge → Decision logs
```
