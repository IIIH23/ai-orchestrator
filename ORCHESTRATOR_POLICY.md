# Hermes Orchestrator Policy

## 1. Model Roles

- Primary orchestrator: owl-alpha
- Auxiliary and fallback model: GPT-5 mini
- Coding worker: Codex
- High-risk reviewer: Claude

Claude review is automatic for:

- security changes
- production architecture
- authentication and permissions
- secrets management
- database migrations
- infrastructure changes
- deployment changes
- irreversible operations
- financially significant decisions

## 2. GitHub Policy

- Initial workspace: personal GitHub account
- Future migration: GitHub Organization
- New repositories are private by default
- Public repositories require explicit approval

Repository model:

- separate repository for every serious project
- one sandbox repository for experiments

New repositories may be created automatically only after:

1. short discovery
2. MVP plan
3. classification as a valid project

## 3. Branch and Pull Request Policy

Hermes may automatically:

- create feature branches
- commit tested changes
- push to feature branches
- create pull requests for low-risk changes
- merge low-risk pull requests after successful CI

Hermes may not:

- push directly to main
- force-push main
- merge medium-risk or high-risk changes without approval

Main branch protection:

- direct push disabled
- force push disabled
- required CI checks
- required status checks

## 4. Risk Classification

### Low-risk

Examples:

- documentation
- tests
- formatting
- internal refactoring without API changes
- dependency patch updates
- dependency minor updates

Low-risk changes may:

- create PR automatically
- merge automatically after successful CI
- deploy automatically to staging

### Medium-risk

Examples:

- API behavior changes
- dependency major updates
- schema-compatible database changes
- deployment workflow modifications

Medium-risk changes require approval before deployment or merge.

### High-risk

Examples:

- security
- authentication
- permissions
- secrets
- production database changes
- infrastructure
- billing resources
- irreversible operations

High-risk changes require:

- Claude review
- explicit user approval
- successful CI
- tested rollback plan

## 5. Staging Infrastructure

Provider: Hetzner

Server:

- name: hermes-staging-01
- location: hel1
- operating system: Ubuntu 26.04 LTS
- CPU: 2 vCPU
- RAM: 4 GB
- disk: 40 GB
- swap: 2 GB
- public IPv4 enabled
- IPv6 enabled
- automatic Hetzner backups enabled

Hermes VPS remains in nbg1.

Both servers are connected through a Hetzner Private Network.

Suggested network:

- network range: 10.10.0.0/16
- subnet: 10.10.1.0/24
- Hermes VPS: 10.10.1.2
- staging VPS: 10.10.1.3

## 6. Server Labels

- role=staging
- project=hermes
- environment=staging
- managed-by=automation

## 7. Access Policy

Initial administrator access:

- existing Ed25519 SSH key

Deployment access:

- separate deployment SSH key
- dedicated user: deploy
- Docker access without sudo
- deploy account reserved for CI/CD

Security:

- password login disabled
- root login disabled after initial setup
- SSH allowed from Hermes through Private Network
- SSH allowed from user device with Ed25519 key

## 8. Firewall Policy

Hetzner Firewall enabled.

Public inbound ports:

- 22/tcp
- 80/tcp
- 443/tcp

All other inbound traffic denied.

UFW enabled with mirrored rules:

- allow 22/tcp
- allow 80/tcp
- allow 443/tcp
- deny incoming by default
- allow outgoing by default

Internal services such as PostgreSQL and Redis must not expose public ports.

Fail2ban must protect SSH.

## 9. Container Platform

- Docker
- Docker Compose
- Caddy reverse proxy
- automatic HTTPS
- PostgreSQL in a separate container
- PostgreSQL persistent volume
- Redis only when required

Docker images are built in GitHub Actions and stored in ghcr.io.

The staging VPS only pulls and runs signed images.

## 10. Deployment Pipeline

Pipeline:

1. merge to main
2. required CI checks
3. build Docker image
4. Trivy vulnerability scan
5. generate SBOM
6. Cosign keyless signing
7. GitHub provenance attestation
8. push image to ghcr.io
9. SSH deployment to staging
10. Docker Compose deployment
11. health check
12. automatic rollback on failure
13. Telegram notification

Deployment approvals:

- low-risk: automatic
- medium-risk: explicit approval
- high-risk: explicit approval plus Claude review

## 11. Container Security

Trivy policy:

- critical vulnerabilities block deployment
- high vulnerabilities block deployment
- medium vulnerabilities produce warnings
- low vulnerabilities are informational

Each image must have:

- SBOM in CycloneDX or SPDX format
- Cosign keyless signature
- GitHub provenance attestation

Unsigned or unverifiable images must not be deployed.

## 12. Dependency Management

Dependabot enabled.

Schedule:

- weekly

Policy:

- patch updates may auto-merge after successful CI
- minor updates may auto-merge after successful CI
- major updates require review and approval

## 13. Domain and DNS

Registrar and DNS provider:

- Cloudflare

Base domain:

- example.org

Staging domain:

- app.staging.example.org

Initial DNS mode:

- DNS only

After successful deployment:

- Cloudflare Proxy may be enabled
- Cloudflare Access may replace Basic Auth

DNSSEC enabled.

## 14. Staging Access Control

Initial protection:

- Caddy Basic Auth

Later:

- Cloudflare Access
- separate access policies for team members

## 15. Monitoring and Alerts

Initial monitoring:

- Docker health checks
- CPU monitoring
- RAM monitoring
- swap monitoring
- disk monitoring
- container failure alerts
- HTTPS failure alerts
- backup failure alerts

Heavy Prometheus, Grafana, and Loki stack is not installed on the 4 GB staging server.

Telegram bot:

- TerraBits Infra Bot

Telegram chats:

- TerraBits Staging Alerts
- TerraBits Production Alerts

GitHub secrets:

- TELEGRAM_BOT_TOKEN
- TELEGRAM_STAGING_CHAT_ID
- TELEGRAM_PRODUCTION_CHAT_ID

## 16. Logging

- structured JSON logs
- Docker log rotation
- retention: 7 to 14 days
- critical errors sent to Telegram
- Sentry added only for applications that need it

## 17. PostgreSQL Backups

- daily encrypted backups
- stored outside staging VPS
- storage: Hetzner Object Storage
- retain 7 daily copies
- retain 4 weekly copies
- test restores regularly

Hetzner server backups do not replace PostgreSQL backups.

## 18. Secrets Policy

Staging secrets are stored in:

- GitHub Environment: staging

Future production secrets are stored separately in:

- GitHub Environment: production

Hermes may:

- propose secret names
- generate safe values
- prepare rotation plans

Hermes may not add, change, rotate, or delete secrets without explicit approval.

## 19. Cloud Resource Policy

Hermes may:

- prepare Hetzner configurations
- generate Terraform plans
- estimate costs
- validate infrastructure changes

Hermes may not create, modify, resize, or delete paid cloud resources without explicit approval.

This includes:

- VPS
- Object Storage
- Networks
- Firewalls
- production resources
- paid external services
