# Caddy Configuration

> Last updated: 2026-06-27

## Staging Domain

- **Domain**: earthbit.staging.terrabits.org
- **Target**: 157.180.125.174:8080 (app)
- **HTTPS**: Automatic via Caddy
- **Auth**: Basic Auth (initial), Cloudflare Access (later)

## Caddyfile

```
# Staging: earthbit.staging.terrabits.org
earthbit.staging.terrabits.org {
    # Automatic HTTPS
    tls {
        protocols tls1.2 tls1.3
    }

    # Basic Auth (temporary, until Cloudflare Access)
    basicauth / {
        admin $2a$14$HASHED_PASSWORD_HERE
    }

    # Health endpoint (no auth)
    handle /health {
        respond "OK" 200
    }

    # Reverse proxy to app
    handle {
        reverse_proxy app:8080
    }

    # Structured logging
    log {
        output file /var/log/caddy/access.log {
            roll_size 10mb
            roll_keep 5
        }
        level INFO
        format json
    }

    # Security headers
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        X-XSS-Protection "1; mode=block"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
}
```

## Caddy Compose File

```yaml
# /opt/terrabits/caddy/compose.yaml
version: "3.9"

services:
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
      - caddy_logs:/var/log/caddy
    environment:
      - CF_API_TOKEN=${CF_API_TOKEN:-}
    healthcheck:
      test: ["CMD", "caddy", "version"]
      interval: 30s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 128M

volumes:
  caddy_data:
  caddy_config:
  caddy_logs:
```

## Logging

- Format: JSON
- Retention: 7 days (logrotate)
- Location: /var/log/caddy/
- Access + error logs
- No sensitive data in logs

## Security

- TLS 1.2+ only
- Security headers (HSTS, XSS, CSP)
- Basic Auth for staging (password in env, not in repo)
- Rate limiting (Caddy built-in)
- Health endpoint without auth for monitors
