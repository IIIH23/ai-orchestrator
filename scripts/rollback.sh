#!/usr/bin/env bash
# Rollback script for Pulse of Earth staging
# Run as deploy user with docker access
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-/opt/terrabits/apps/pulse-of-earth/compose.yaml}"
STATE_DIR="${STATE_DIR:-/opt/terrabits/releases}"
LOG_FILE="${LOG_FILE:-/opt/terrabits/backups/rollback.log}"

mkdir -p "$STATE_DIR" "$(dirname "$LOG_FILE")"

log() { echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG_FILE"; }

release_current() {
  # Save current state before rollback
  local ts
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  echo "RELEASE_TAG=$(docker compose -f "$COMPOSE_FILE" images --format json 2>/dev/null | head -n1 | grep -oP '"tag":"[^"]+"' | head -n1 | cut -d'"' -f4)" > "$STATE_DIR/last-good-release.txt"
  echo "TIMESTAMP=$ts" >> "$STATE_DIR/last-good-release.txt
  log "Current state saved to $STATE_DIR/last-good-release.txt"
}

release_list() {
  echo "Available releases:"
  echo "  staging (current)"
  docker image ls ghcr.io/hermes/pulse-of-earth --format '{{.Tag}}' | grep '^sha-' | head -n10
}

rollback_to() {
  local tag="${1:-staging}"
  release_current
  log "Rolling back to tag: $tag"

  docker compose -f "$COMPOSE_FILE" pull || { log "ERROR: pull failed"; exit 1; }
  docker compose -f "$COMPOSE_FILE" up -d || { log "ERROR: up failed"; exit 1; }

  sleep 5
  if curl -fsS http://127.0.0.1:8080/health >/dev/null 2>&1; then
    log "Rollback successful: health check passing"
  else
    log "ERROR: health check failed after rollback"
    exit 1
  fi
}

case "${1:-help}" in
  current) release_current ;;
  list) release_list ;;
  rollback) rollback_to "${2:-staging}" ;;
  *) echo "Usage: $0 {current|list|rollback [tag]}" ;;
esac
