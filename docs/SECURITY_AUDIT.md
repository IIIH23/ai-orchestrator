# Security Audit Report

> Last updated: 2026-06-29

## GitHub Actions Permissions

| Check | Status | Notes |
|-------|--------|-------|
| Default permissions | `contents: read` | ✅ Least privilege |
| CI packages write | `packages: write` | ✅ For GHCR push |
| No admin permissions | ✅ | |
| Fork PR safety | ⚠️ | `dependency-review-action` only on PR |

## Secrets Exposure

| Check | Status | Notes |
|-------|--------|-------|
| Secrets in workflow files | ✅ | All use `${{ secrets.XXX }}` |
| Secrets in logs | ✅ | GitHub auto-redacts |
| Secrets in repo files | ✅ | No secrets committed |
| Telegram token in scripts | ✅ | Read from env |
| Linear API Key in scripts | ✅ | Read from env |

## Third-Party Actions

| Action | Pinned | Risk |
|--------|--------|------|
| `actions/checkout@v4` | ⚠️ version only | Low |
| `actions/setup-python@v5` | ⚠️ version only | Low |
| `docker/build-push-action@v5` | ⚠️ version only | Low |
| `docker/login-action@v3` | ⚠️ version only | Low |
| `docker/setup-buildx-action@v3` | ⚠️ version only | Low |
| `aquasecurity/trivy-action@master` | ⚠️ master | Medium |
| `sigstore/cosign-installer@v3` | ⚠️ version only | Low |
| `anchore/sbom-action@v0` | ⚠️ version only | Low |
| `appleboy/ssh-action@v1` | ⚠️ version only | Medium |
| `ludeeus/action-shellcheck@master` | ⚠️ master | Low |

**Recommendation**: Pin all actions to commit SHA for supply chain security.

## SSH Key Permissions

| Check | Status | Notes |
|-------|--------|-------|
| Deploy key | `~/.ssh/deploy_staging_ed25519` | ✅ |
| Key permissions | `600` | ✅ |
| Root SSH disabled | ✅ | `PermitRootLogin no` |
| Password auth disabled | ✅ | `PasswordAuthentication no` |
| AllowUsers | `deploy` only | ✅ |

## Docker Security

| Check | Status | Notes |
|-------|--------|-------|
| Non-root container | ✅ | `USER app` in Dockerfile |
| Read-only filesystem | ⚠️ | Not enforced |
| No-new-privileges | ⚠️ | Not set |
| Resource limits | ✅ | `memory: 128M` |
| Health check | ✅ | Built-in |

## Shell Injection Risks

| Script | Risk | Notes |
|--------|------|-------|
| `bootstrap-staging.sh` | Low | `set -euo pipefail`, no user input |
| `lockdown-staging-ssh.sh` | Low | Root-only, no user input |
| `check-health.sh` | Low | Read-only checks |
| `rollback.sh` | Low | Docker compose commands |
| `send-telegram-alert.sh` | Low | Curl with fixed payload |

## Telegram Log Redaction

| Check | Status | Notes |
|-------|--------|-------|
| Bot token in logs | ✅ | Not printed |
| Chat ID in logs | ✅ | Not printed |
| Error messages | ✅ | Sanitized |

## Linear Token Redaction

| Check | Status | Notes |
|-------|--------|-------|
| API Key in logs | ✅ | Read from env only |
| API Key in repo | ✅ | Not committed |

## High-Risk Findings

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| Actions not pinned to SHA | Medium | Pin to commit SHA |
| Trivy action uses `@master` | Medium | Pin to version/SHA |
| No Docker Content Trust | Low | Enable for production |
| No container signing verification | Low | Verify on staging |

## Recommendations

1. Pin all GitHub Actions to commit SHA
2. Enable Docker Content Trust (`DOCKER_CONTENT_TRUST=1`)
3. Add `no-new-privileges: true` to compose files
4. Add read-only root filesystem where possible
