# Security Boundaries

> Generated: 2026-06-27
> Based on: ORCHESTRATOR_POLICY.md sections 7, 18 + ORCHESTRATOR_COMPLETION_PROMPT section 18

## Access Matrix

| Profile | Resources | Actions | Model |
| --- | --- | --- | --- |
| default/owner | All | All (with approval for high-risk) | owl-alpha |
| development | Repo, CI, staging (deploy) | Code, tests, commits, PRs, staging deploy | Codex |
| architecture | Repo, docs | ADR, design, review | Claude Code |
| research | Repo, docs | Research, analysis, notes | GPT-5 mini |
| devops | Repo, staging, infra | Bootstrap, monitoring, backups, deploy | Codex |
| design | Repo, docs | UX specs, design briefs | GPT-5 mini |
| finance | Repo (read-only) | Cost reports, budgets | GPT-5 mini |
| team | Repo, Linear | Task updates, reports | GPT-5 mini |

## Approval Boundaries

### Owner Approval Required

| Action | Risk | Reason |
| --- | --- | --- |
| Create/modify secrets | high | Credential exposure |
| Create/modify API tokens | high | Credential exposure |
| Hetzner resource create/modify/delete | high | Financial |
| Cloudflare DNS/firewall changes | high | Availability |
| Production deployment | high | User-facing impact |
| Database migration | high | Data integrity |
| Repository publication | high | IP exposure |
| Credential rotation | high | Security |
| Medium/high-risk merge | medium | Code quality |
| Terraform apply | high | Infrastructure |
| Hetzner Firewall modify | high | Network security |

### Autonomous Actions Allowed

| Action | Risk | Safeguard |
| --- | --- | --- |
| Read files, git status | low | — |
| Create feature branches | low | Naming convention |
| Run local tests | low | No external side effects |
| Commit to feature branches | low | No direct push to main |
| Create low-risk PR | low | Auto-merge after CI |
| Update docs | low | — |
| Run smoke tests | low | Read-only |
| Generate reports | low | — |
| Create monitoring scripts | low | Local only |

## Network Boundaries

| Zone | Access | Services |
| --- | --- | --- |
| Public internet | Inbound: 22, 80, 443 | SSH, HTTP, HTTPS |
| Hetzner Private Network | Internal only | Hermes ↔ Staging |
| Staging internal | Docker network only | PostgreSQL (5432) |
| Hermes VPS | Full outbound | Orchestration, Telegram |

## Container Security

- Non-root containers
- Read-only filesystem where possible
- Drop capabilities
- no-new-privileges
- Health checks
- Resource limits
- Pinned base images (SHA)
- Multi-stage builds
- Secrets via environment (not layers)

## Supply Chain

- Third-party actions pinned by commit SHA
- Dependencies locked (lockfile)
- Trivy scan: critical/high block
- SBOM generated (CycloneDX/SPDX)
- Cosign keyless signing
- GitHub provenance attestation

## Incident Response

1. Detect: monitoring alert or test failure
2. Isolate: stop affected service
3. Assess: classify severity
4. Recover: rollback or restore
5. Notify: Telegram alert to owner
6. Post-mortem: document + ADR

## GitHub Actions Security

- Default permissions: `contents: read`
- Write permissions scoped to specific jobs
- Third-party actions pinned by commit SHA where practical
- `actions/checkout` pinned to `v4` (SHA: `692973e3d937129bcbf40652eb9f2f61becf3332`)
- `actions/setup-python` pinned to `v5` (SHA: `0b93645e9fea7318ecaed2b359559ac225c90a2b`)
- Secrets never printed in logs
- No secrets in fork PR workflows
- Environment protection for staging/production
- OIDC preferred over long-lived credentials where possible
- Dependency review on PRs enabled

## Secret Rotation

| Secret | Frequency | Method |
| --- | --- | --- |
| SSH keys | 90 days | New key + update authorized_keys |
| GitHub PAT | 90 days | Regenerate in GitHub settings |
| Cloudflare token | 180 days | Regenerate in dashboard |
| Linear API key | 180 days | Regenerate in dashboard |
| PostgreSQL passwords | 90 days | Update in container env |
| Telegram bot token | As needed | Regenerate via BotFather |
