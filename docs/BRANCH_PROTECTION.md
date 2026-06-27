# Branch Protection

> Last updated: 2026-06-27

## Main Branch Protection Rules

| Rule | Status | Requires Owner |
| --- | --- | --- |
| Direct push disabled | ⏳ pending | yes |
| Force push disabled | ⏳ pending | yes |
| Required CI checks (ci.yml) | ⏳ pending | yes |
| Required status checks | ⏳ pending | yes |
| Required resolved conversations | ⏳ pending | yes |
| Branch up to date before merge | ⏳ pending | yes |
| Signed commits | ⏳ pending | yes |
| Auto-delete feature branches after merge | ⏳ pending | yes |

## Branch Naming Convention

| Prefix | Purpose | Example |
| --- | --- | --- |
| `feat/orchestrator-<topic>` | Feature branches | `feat/orchestrator-github-ci` |
| `infra/<topic>` | Infrastructure | `infra/terraform-staging` |
| `docs/<topic>` | Documentation | `docs/adr-001` |
| `fix/<topic>` | Bug fixes | `fix/lockdown-test-assertions` |
| `security/<topic>` | Security fixes | `security/ssh-hardening` |

## Merge Policy

| Risk | Auto-merge | Review Required | CI Required |
| --- | --- | --- | --- |
| Low (docs, tests, formatting) | ✅ after CI pass | Optional | ✅ |
| Medium (API changes, deps) | ❌ | 1 reviewer | ✅ |
| High (infra, security, secrets) | ❌ | 2 reviewers + owner | ✅ |

## GitHub Actions Permissions

- Default: `contents: read`
- CI workflow: `contents: write` (for GHCR push)
- Dependabot: `contents: write`, `pull-requests: write`
- Environment protection: required for staging/production deployments
