#!/usr/bin/env bash
# Health check script for Pulse of Earth staging
# Run as deploy user or root
set -euo pipefail

HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-http://127.0.0.1:8080/health}"
DOCKER_COMPOSE="${DOCKER_COMPOSE:-/opt/terrabits/apps/pulse-of-earth/compose.yaml}"
ALERT_SCRIPT="${ALERT_SCRIPT:-/opt/terrabits/scripts/send-telegram-alert.sh}"

pass=0
fail=0

check() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "PASS  $name"
    pass=$((pass+1))
  else
    echo "FAIL  $name"
    fail=$((fail+1))
  fi
}

# Docker health
check "docker service running" bash -c "docker info"
check "all containers healthy" bash -c "docker compose -f $DOCKER_COMPOSE ps | grep -q 'healthy\|running'"

# HTTP health
check "app responds on /health" curl -fsS "$HEALTH_ENDPOINT"

# System health
check "disk usage < 80%" bash -c "df / | tail -n1 | awk '{exit (\$5 > 80 ? 1 : 0)}'"
check "memory available > 100MB" bash -c "free -m | awk '/Mem:/{exit (\$7 < 100 ? 1 : 0)}'"
check "swap not overused" bash -c "free -m | awk '/Swap:/{exit (\$3 > 1500 ? 1 : 0)}'"

# Security
check "ufw active" bash -c "ufw status | grep -q 'Status: active'"
check "fail2ban running" bash -c "systemctl is-active fail2ban"

# Summary
echo ""
echo "Health: $pass PASS, $fail FAIL"

if [ "$fail" -gt 0 ]; then
  if [ -x "$ALERT_SCRIPT" ]; then
    bash "$ALERT_SCRIPT" "warning" "Staging health check failed: $fail failures" || true
  fi
  exit 1
fi
exit 0
