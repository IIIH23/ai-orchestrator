#!/usr/bin/env bash
# Send Telegram alert
# Usage: send-telegram-alert.sh <severity> <message> [details]
set -euo pipefail

TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
  echo "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set" >&2
  exit 0
fi

severity="${1:-info}"
message="${2:-No message}"
details="${3:-}"

case "$severity" in
  critical) icon="🔴" ;;
  warning)  icon="🟡" ;;
  success)  icon="🟢" ;;
  *)        icon="🔵" ;;
esac

payload="$icon *Pulse of Earth* [%PLACEHOLDER_ENV%]
$message"

if [ -n "$details" ]; then
  payload="$payload

\`\`\`
$details
\`\`\`"
fi

# Truncate to Telegram limit (4096 chars)
payload="${payload:0:4096}"

curl -fsS -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=${payload}" \
  -d "parse_mode=Markdown" \
  -d "disable_web_page_preview=true" >/dev/null
