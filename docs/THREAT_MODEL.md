# Threat Model

> Last updated: 2026-06-27

## Assets

| Asset | Value | Sensitivity |
| --- | --- | --- |
| Source code | High | Medium |
| SSH keys | Critical | High |
| GitHub repo | High | Medium |
| Staging VPS | High | Medium |
| API tokens | Critical | High |
| Database data | High | High |
| Backups | High | High |
| Obsidian vault | Medium | Medium |

## Threat Actors

| Actor | Motivation | Capability |
| --- | --- | --- |
| Script kiddie | Disruption | Low |
| Opportunistic hacker | Data theft | Medium |
| Insider (disgruntled) | Sabotage | High |
| Supply chain attacker | Backdoor | Advanced |

## Threat Analysis

### STRIDE

| Threat | Mitigation |
| --- | --- |
| Spoofing | SSH keys, MFA, PubkeyAuthentication |
| Tampering | Signed commits, branch protection, checksums |
| Repudiation | Git commit signing, audit logs |
| Information disclosure | No secrets in repo, encrypted backups |
| Denial of service | UFW, Fail2ban, rate limiting |
| Elevation of privilege | Non-root containers, sudo restrictions |

## Attack Surfaces

### 1. SSH Access

| Risk | Mitigation |
| --- | --- |
| Brute force | Fail2ban, key-only auth |
| Key theft | Separate deploy key, no root SSH |
| Port forwarding | AllowUsers deploy, no root login |

### 2. GitHub Actions

| Risk | Mitigation |
| --- | --- |
| Malicious PR | Required review, no secrets in fork PRs |
| Supply chain | Pinned actions by SHA, dependency review |
| Token leak | Scoped permissions, no echo of secrets |

### 3. Docker

| Risk | Mitigation |
| --- | --- |
| Container escape | Non-root, read-only fs, drop capabilities |
| Image tampering | Pinned base images, Trivy scan, Cosign signing |
| Secret exposure | No secrets in layers, env vars via .env |

### 4. Network

| Risk | Mitigation |
| --- | --- |
| DDoS | UFW rate limiting, Cloudflare Proxy (future) |
| Man-in-the-middle | TLS 1.2+, HSTS, certificate pinning |
| Port scanning | UFW default deny, only 22/80/443 open |

## Incident Response

### Severity Levels

| Level | Description | Response Time |
| --- | --- | --- |
| P1 Critical | Data breach, service down | Immediate |
| P2 High | Security vulnerability | < 1 hour |
| P3 Medium | Failed deploy, degraded service | < 4 hours |
| P4 Low | Minor issue, cosmetic | < 24 hours |

### Response Procedure

1. **Detect**: monitoring alert or test failure
2. **Assess**: classify severity (P1-P4)
3. **Contain**: stop affected service, block attacker
4. **Eradicate**: remove vulnerability
5. **Recover**: rollback or restore from backup
6. **Notify**: Telegram alert to owner
7. **Post-mortem**: document + ADR

### Rollback Scenarios

| Scenario | Rollback Action |
| --- | --- |
| Bad deploy | `rollback.sh` to previous SHA |
| Compromised key | Rotate key, update authorized_keys |
| Container compromise | Kill container, redeploy from known-good image |
| Data corruption | Restore from PostgreSQL backup |

## Owner Actions Required

1. Review and approve threat model
2. Provide incident response contact
3. Approve security tool installation (Trivy, etc.)
