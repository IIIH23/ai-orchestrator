# App Directory Structure

> Last updated: 2026-06-27

## Layout

```
/opt/terrabits/
├── apps/
│   └── pulse-of-earth/
│       ├── compose.yaml      # Docker Compose for this app
│       ├── .env             # Secrets (not in repo)
│       ├── releases/        # Current SHA tag + metadata
│       │   └── current.txt
│       ├── data/            # Persistent container data
│       └── logs/            # Application logs
├── caddy/
│   └── Caddyfile            # Reverse proxy config
├── backups/
│   ├── postgres/            # Database dumps
│   └── releases/            # Rollback state
├── scripts/
│   ├── check-health.sh      # Health check
│   ├── rollback.sh          # Rollback
│   └── send-telegram-alert.sh
└── shared/
    └── releases/            # Cross-app release tracking
```

## Health Check Flow

```
cron/systemd (every 5 min)
  → scripts/check-health.sh
    → docker compose ps
    → curl /health
    → df /, free -m
    → ufw status
    → systemctl fail2ban
  → if failures: send-telegram-alert.sh
```

## Rollback Flow

```
CI deploy fails health check
  → scripts/rollback.sh
    → save current state
    → pull previous SHA image
    → docker compose up -d
    → health check
    → if success: Telegram success
    → if fail: Telegram critical + manual intervention
```

## Deployment Flow

```
Docker image tagged staging arrives
  → scripts/check-health.sh (pre-deploy)
  → docker compose pull
  → docker compose up -d
  → scripts/check-health.sh (post-deploy)
  → if pass: Telegram success + update releases/current.txt
  → if fail: rollback.sh
```
