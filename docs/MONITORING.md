# Monitoring

> Last updated: 2026-06-27

## Strategy

Lightweight monitoring for 4 GB staging VPS. No Prometheus/Grafana/Loki stack.

## Monitored Metrics

| Metric | Check | Threshold | Alert |
| --- | --- | --- | --- |
| Disk usage | `df /` | > 80% | 🟡 warning |
| RAM usage | `free -m` | < 100MB available | 🟡 warning |
| Swap usage | `free -m` | > 1.5 GB used | 🟡 warning |
| CPU load | `cat /proc/loadavg` | > 2.0 (2 vCPU) | 🟡 warning |
| Container health | `docker compose ps` | any unhealthy | 🔴 critical |
| HTTPS endpoint | `curl -f https://...` | non-200 | 🔴 critical |
| Certificate expiry | `openssl s_client` | < 14 days | 🟡 warning |
| Backup freshness | `ls -t backups/` | > 25h | 🔴 critical |
| UFW status | `ufw status` | not active | 🔴 critical |
| Fail2ban status | `systemctl is-active` | not active | 🔴 critical |

## Monitoring Scripts

### System Health

```bash
#!/usr/bin/env bash
# /opt/terrabits/scripts/check-system-health.sh
set -euo pipefail

ALERT_SCRIPT="/opt/terrabits/scripts/send-telegram-alert.sh"
STATUS="ok"
DETAILS=""

# Disk
DISK_USAGE=$(df / | tail -n1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 80 ]; then
  STATUS="warning"
  DETAILS="${DETAILS}\nDisk: ${DISK_USAGE}% used"
fi

# RAM
RAM_AVAILABLE=$(free -m | awk '/Mem:/{print $7}')
if [ "$RAM_AVAILABLE" -lt 100 ]; then
  STATUS="warning"
  DETAILS="${DETAILS}\nRAM: ${RAM_AVAILABLE}MB available"
fi

# Swap
SWAP_USED=$(free -m | awk '/Swap:/{print $3}')
if [ "$SWAP_USED" -gt 1500 ]; then
  STATUS="warning"
  DETAILS="${DETAILS}\nSwap: ${SWAP_USED}MB used"
fi

# CPU
CPU_LOAD=$(cat /proc/loadavg | awk '{print $1}')
if (( $(echo "$CPU_LOAD > 2.0" | bc -l) )); then
  STATUS="warning"
  DETAILS="${DETAILS}\nCPU load: ${CPU_LOAD}"
fi

if [ "$STATUS" = "warning" ]; then
  bash "$ALERT_SCRIPT" "warning" "System health check" "$DETAILS" || true
fi
```

### Container Health

```bash
#!/usr/bin/env bash
# /opt/terrabits/scripts/check-containers.sh
set -euo pipefail

ALERT_SCRIPT="/opt/terrabits/scripts/send-telegram-alert.sh"
COMPOSE_FILE="/opt/terrabits/apps/pulse-of-earth/compose.yaml"

UNHEALTHY=$(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null | \
  jq -r 'select(.State != "running" or .Health == "unhealthy") | .Name' 2>/dev/null)

if [ -n "$UNHEALTHY" ]; then
  bash "$ALERT_SCRIPT" "critical" "Container unhealthy" "$UNHEALTHY" || true
fi
```

### Certificate Check

```bash
#!/usr/bin/env bash
# /opt/terrabits/scripts/check-certificates.sh
set -euo pipefail

ALERT_SCRIPT="/opt/terrabits/scripts/send-telegram-alert.sh"
DOMAIN="app.staging.example.org"

EXPIRY_DAYS=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | \
  openssl x509 -noout -enddate 2>/dev/null | \
  cut -d= -f2 | xargs -I{} date -d @{} +%s | \
  xargs -I{} echo $(( ($(date +%s) - {}) / 86400 )))

if [ "$EXPIRY_DAYS" -lt 14 ]; then
  bash "$ALERT_SCRIPT" "warning" "Certificate expires in ${EXPIRY_DAYS} days" || true
fi
```

## Alert Deduplication

- Cooldown: 5 minutes between same alert type
- Key: `hash(metric_name + severity)`
- Stored in `/tmp/alert-cooldown.json`
- Max 10 messages per hour per chat

## Schedule

| Check | Frequency |
| --- | --- |
| System health | Every 5 min (systemd timer) |
| Container health | Every 5 min (systemd timer) |
| Certificate | Daily at 08:00 UTC |
| Backup freshness | Daily at 08:00 UTC |

## Owner Actions Required

1. Provide Telegram bot token
2. Provide Telegram chat IDs
3. Approve monitoring systemd timers
