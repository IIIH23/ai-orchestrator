# Cloudflare Integration

> Last updated: 2026-06-27

## Domain

- **Base domain**: example.org
- **Staging**: app.staging.example.org → 203.0.113.10
- **Registrar**: Cloudflare
- **DNSSEC**: enabled

## DNS Records

| Type | Name | Content | TTL | Proxy | Purpose |
| --- | --- | --- | --- | --- | --- |
| A | earthbit.staging | 203.0.113.10 | 300 | ❌ (DNS only) | Staging app |
| A | hermes | <hermes-vps-ip> | 300 | ❌ | Orchestrator |
| CNAME | www.earthbit.staging | app.staging.example.org | 300 | ❌ | WWW redirect |
| MX | <base domain> | mail server | 3600 | — | Email |
| TXT | <base domain> | v=spf1 ... | 3600 | — | SPF |

### Initial Mode

- **DNS only** (no orange cloud / proxy)
- After HTTPS confirmed → enable Cloudflare Proxy

### API Token

- Name: `hermes-automation`
- Permissions: `Zone.DNS` (read/edit for example.org zone only)
- Do NOT store token in repo
- Provide to orchestrator via secure channel

## Cloudflare Access

### Staging Policy

| Setting | Value |
| --- | --- |
| Application | app.staging.example.org |
| Policy name | Staging Users |
| Action | Allow |
| Include | Team emails (comma-separated) |
| Exclude | None |
| Session duration | 24h |

### Service Token (CI/CD)

- Name: hermes-deployer
- Used by GitHub Actions for staging deploy
- Stored in GitHub Environment as `CF_SERVICE_TOKEN`

## Terraform Plan

```hcl
# infrastructure/terraform/cloudflare/main.tf
resource "cloudflare_record" "staging" {
  zone_id = var.cloudflare_zone_id
  name    = "earthbit.staging"
  type    = "A"
  value   = "203.0.113.10"
  ttl     = 300
  proxied = false
}

resource "cloudflare_access_application" "staging" {
  zone_id = var.cloudflare_zone_id
  name   = "Pulse of Earth Staging"
  domain = "app.staging.example.org"
}

resource "cloudflare_access_policy" "staging_team" {
  application_id = cloudflare_access_application.staging.id
  name           = "Staging Team"
  action         = "allow"
  include        = [for email in var.team_emails : {email = email}]
}
```

### Terraform Variables (no secrets)

```hcl
# infrastructure/terraform/terraform.tfvars.example
cloudflare_zone_id = "your-zone-id"
team_emails = [
  "ops@example.org",
]
```

## Deployment Order

1. Create DNS record (A staging → 203.0.113.10)
2. Wait for DNS propagation (< 5 min with TTL 300)
3. Verify HTTPS via automated test
4. After first successful HTTPS:
   - Enable Cloudflare Proxy
   - Create Access application
   - Create Access policy with team emails
   - Create service token for CI/CD
   - Store in GitHub Environment

## Rollback

- DNS: revert A record IP
- Access: disable application
- Proxy: disable if needed
- Terraform: `terraform plan` first to preview changes

## Owner Actions Required

1. Provide Cloudflare zone ID for example.org
2. Provide API token with Zone.DNS permissions
3. Provide team emails for staging Access allowlist
4. Approve Terraform plan before apply (if self-hosted state)
