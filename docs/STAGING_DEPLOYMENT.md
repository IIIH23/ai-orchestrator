# Staging Deployment

> Last updated: 2026-06-27

## Server

- **Host**: hermes-staging-01
- **IPv4**: 157.180.125.174
- **OS**: Ubuntu 26.04 LTS
- **User**: deploy (SSH key: ~/.ssh/deploy_staging_ed25519)

## Deployment Steps

### Initial Setup (one-time)

```bash
# Create directory structure
sudo mkdir -p /opt/terrabits/{apps/pulse-of-earth,caddy,backups/{postgres,releases},scripts,shared/releases}
sudo chown -R deploy:deploy /opt/terrabits

# Create .env file
cat > /opt/terrabits/apps/pulse-of-earth/.env << 'EOF'
ENVIRONMENT=staging
LOG_LEVEL=INFO
EOF
```

### Deploy via CI

1. CI builds Docker image
2. Pushes to ghcr.io with SHA tag + staging tag
3. SSH to staging as deploy
4. Pull new image
5. docker compose up -d
6. Health check
7. Telegram notification

### Manual Deploy

```bash
cd /opt/terrabits/apps/pulse-of-earth
docker compose pull
docker compose up -d
docker compose ps
curl -f http://127.0.0.1:8080/health
```

### Rollback

```bash
/opt/terrabits/scripts/rollback.sh rollback staging
```

## Health Checks

- Every 5 minutes via systemd timer
- HTTP GET /health → 200 OK
- Docker compose ps → all healthy
- Disk < 80%
- RAM available > 100MB
- UFW active
- Fail2ban active

## Monitoring

- Docker health checks (container level)
- Systemd timer (host level)
- Telegram alerts (notification)
- No heavy Prometheus/Grafana on 4 GB VPS

## Backup

- PostgreSQL daily dumps (when DB is added)
- Stored in /opt/terrabits/backups/postgres/
- Encrypted, off-server (Object Storage when configured)
- Retention: 7 daily, 4 weekly
