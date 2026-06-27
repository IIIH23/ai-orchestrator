# Security Checklist

> Last updated: 2026-06-27

## Infrastructure

- [x] SSH key-only auth (no password)
- [x] PermitRootLogin no
- [x] AllowUsers deploy only
- [x] UFW enabled (22, 80, 443 only)
- [x] Fail2ban active (sshd jail)
- [x] Unattended security updates enabled
- [x] 2 GB swap configured
- [x] Separate deploy user (no root for CI/CD)
- [ ] Hetzner Firewall mirrors UFW
- [ ] Hetzner Private Network between VPS

## GitHub

- [ ] Branch protection on main
- [ ] Required CI checks
- [ ] Required status checks
- [ ] Signed commits
- [ ] Dependabot enabled
- [ ] Dependency review on PRs
- [ ] Actions permissions: read by default
- [ ] Pinned actions by commit SHA

## Docker

- [x] Non-root containers
- [x] Read-only filesystem where possible
- [x] Capabilities dropped
- [x] no-new-privileges
- [x] Health checks
- [x] Resource limits
- [ ] Pinned base images (SHA)
- [ ] Multi-stage builds
- [ ] Secrets not in layers

## CI/CD

- [x] Lint stage
- [x] Test stage
- [ ] Security scan (Trivy)
- [ ] Docker build
- [ ] Cosign signing
- [ ] SBOM generation
- [ ] Staging deploy
- [ ] Health check post-deploy
- [ ] Rollback on failure

## Secrets

- [ ] No secrets in repo
- [ ] GitHub Environments (staging, production)
- [ ] Encrypted backups
- [ ] Secret rotation schedule
- [ ] Least privilege tokens

## Monitoring

- [x] Health check timer (5 min)
- [x] Disk monitoring
- [x] RAM monitoring
- [x] Container health
- [ ] Certificate expiry
- [ ] Backup freshness
- [ ] Alert deduplication
- [ ] Telegram notifications

## Backups

- [ ] PostgreSQL daily dumps
- [ ] Encrypted backups
- [ ] Off-server storage
- [ ] Restore test (monthly)
- [ ] Backup verification

## Documentation

- [x] Threat model
- [x] Security boundaries
- [x] Access matrix
- [x] Incident response
- [ ] Disaster recovery
- [ ] Runbook
- [ ] Owner actions
