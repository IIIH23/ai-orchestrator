# GitHub Environments

> Last updated: 2026-06-27

## Environments

### staging

| Setting | Value |
| --- | --- |
| Name | staging |
| URL | https://earthbit.staging.terrabits.org |
| Auto-deploy | ✅ (push to main, after CI pass) |
| Protection | None (low-risk) |
| Secrets | STAGING_HOST, STAGING_USER, STAGING_SSH_KEY |

#### Required Secrets (staging)

| Secret | Purpose | Type |
| --- | --- | --- |
| STAGING_HOST | VPS IP/hostname | string |
| STAGING_USER | SSH user | string |
| STAGING_SSH_KEY | Ed25519 deploy key | private key |

### production

| Setting | Value |
| --- | --- |
| Name | production |
| URL | https://earthbit.terrabits.org |
| Auto-deploy | ❌ (manual approval required) |
| Protection | Required reviewers, wait timer |
| Secrets | PROD_HOST, PROD_USER, PROD_SSH_KEY, PROD_DB_PASSWORD |

#### Required Secrets (production)

| Secret | Purpose | Type |
| --- | --- | --- |
| PROD_HOST | VPS IP/hostname | string |
| PROD_USER | SSH user | string |
| PROD_SSH_KEY | Ed25519 deploy key | private key |
| PROD_DB_PASSWORD | Database password | encrypted string |
| S3_BACKUP_KEY | Object Storage | access key |
| S3_BACKUP_SECRET | Object Storage | secret key |

## Environment Protection Rules

| Environment | Required Reviewers | Wait Timer | Branch Restriction |
| --- | --- | --- | --- |
| staging | 0 | 0 min | main only |
| production | 2 | 30 min | main only |

## Deployment Flow

```
CI passes (main) → staging deploy → health check → manual approval → production deploy
                     ↓
                  Telegram notification
```

## Rollback Procedure

1. Identify failed deployment (Telegram alert or health check failure)
2. Pull previous SHA-tagged image from GHCR
3. Deploy previous version manually
4. Verify health check passes
5. Notify owner via Telegram
