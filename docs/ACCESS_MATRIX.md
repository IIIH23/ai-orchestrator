# Access Matrix

> Last updated: 2026-06-27

## Human Actors

| Actor | SSH | GitHub | Linear | Obsidian | Deploy |
| --- | --- | --- | --- | --- | --- |
| Owner | ✅ (key) | ✅ admin | ✅ admin | ✅ owner | ✅ approve |
| Developer | ❌ | ✅ write | ✅ write | ✅ write | ❌ |
| Partner | ❌ | ❌ (isolated) | ❌ | ✅ own vault | ❌ |

## System Actors

| Actor | SSH | GitHub | Docker | Deploy | Monitoring |
| --- | --- | --- | --- | --- | --- |
| Hermes (owner) | ✅ root key | ✅ (via PAT) | ✅ | ✅ approve | ✅ |
| Codex (dev) | ❌ | ✅ (via PAT) | ✅ | ✅ staging | ❌ |
| Autopilot cron | ❌ | ✅ (via PAT) | ❌ | ✅ staging | ✅ |
| CI/CD | ❌ | ✅ (GITHUB_TOKEN) | ✅ push | ✅ staging | ❌ |

## Service Accounts

| Account | Scope | Permissions |
| --- | --- | --- |
| GitHub Actions | repo | contents: read/write, packages: write |
| Dependabot | repo | contents: write, PRs: write |
| Terraform (future) | Hetzner | read, compute, network |
| Backup script | Object Storage | read, write (backup bucket only) |
| Monitoring | localhost | read-only system metrics |

## Network Access

| Source | Destination | Port | Protocol |
| --- | --- | --- | --- |
| Internet | Staging | 22 | SSH (key only) |
| Internet | Staging | 80 | HTTP → redirect |
| Internet | Staging | 443 | HTTPS |
| Hermes VPS | Staging | 22 | SSH (deploy key) |
| Hermes VPS | Staging | 443 | HTTPS (health) |
| Staging | GHCR | 443 | HTTPS (pull images) |
| Staging | Internet | 443 | HTTPS (updates, APIs) |

## Owner Actions Required

1. Configure GitHub team access
2. Create Linear workspace and invite team
3. Set up partner isolation (separate profile/workspace)
