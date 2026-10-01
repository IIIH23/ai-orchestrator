# Cloudflare Terraform

> Last updated: 2026-06-27

## Provider

```hcl
# infrastructure/terraform/providers.tf
terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
```

## Variables

```hcl
# infrastructure/terraform/variables.tf
variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone.DNS permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for example.org"
  type        = string
}

variable "domain" {
  description = "Base domain"
  type        = string
  default     = "example.org"
}

variable "staging_ip" {
  description = "Staging VPS IPv4"
  type        = string
  default     = "203.0.113.10"
}

variable "team_emails" {
  description = "Emails for Cloudflare Access allowlist"
  type        = list(string)
  default     = ["ops@example.org"]
}
```

## DNS Records

```hcl
# infrastructure/terraform/dns.tf
resource "cloudflare_record" "staging" {
  zone_id = var.cloudflare_zone_id
  name    = "earthbit.staging"
  type    = "A"
  value   = var.staging_ip
  ttl     = 300
  proxied = false
}

resource "cloudflare_record" "staging_www" {
  zone_id = var.cloudflare_zone_id
  name    = "www.earthbit.staging"
  type    = "CNAME"
  value   = "app.staging.example.org"
  ttl     = 300
  proxied = false
}

resource "cloudflare_record" "hermes" {
  zone_id = var.cloudflare_zone_id
  name    = "hermes"
  type    = "A"
  value   = var.hermes_ip
  ttl     = 300
  proxied = false
}
```

## Access Application

```hcl
# infrastructure/terraform/access.tf
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
  require        = [{email_domain = {domain = "example.org"}}]
}
```

## Example tfvars (without secrets)

```hcl
# infrastructure/terraform/terraform.tfvars.example
cloudflare_zone_id = "your-zone-id-here"
cloudflare_api_token = "your-api-token-here"
staging_ip         = "203.0.113.10"
team_emails        = ["ops@example.org"]
```

## Deployment

```bash
cd infrastructure/terraform/
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

## Cost Estimate

| Service | Plan | Monthly Cost |
| --- | --- | --- |
| Cloudflare DNS | Free | $0 |
| Cloudflare Access | Free (up to 50 users) | $0 |
| Cloudflare Proxy | Free | $0 |
| **Total** | | **$0** |

## Owner Actions Required

1. Provide Cloudflare Zone ID for example.org
2. Provide Cloudflare API token (Zone.DNS permissions)
3. Provide team emails for Access allowlist
4. Provide Hermes VPS IP (for hermes.example.org record)
