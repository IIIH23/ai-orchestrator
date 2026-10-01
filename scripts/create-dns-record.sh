#!/usr/bin/env bash
# Create Cloudflare A record via API
# Requires: CF_API_TOKEN, CF_ZONE_ID env vars; args: <domain> <ip>
set -euo pipefail

: "${CF_API_TOKEN:?Usage: CF_API_TOKEN=xxx CF_ZONE_ID=xxx bash scripts/create-dns-record.sh}"
: "${CF_ZONE_ID:?Usage: CF_API_TOKEN=xxx CF_ZONE_ID=xxx bash scripts/create-dns-record.sh}"

DOMAIN="${1:?Usage: bash scripts/create-dns-record.sh <domain> <ip>}"
IP="${2:?Usage: bash scripts/create-dns-record.sh <domain> <ip>}"

echo "Creating DNS record: $DOMAIN → $IP"

curl -s -X POST \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records" \
  -d "{
    \"type\": \"A\",
    \"name\": \"${DOMAIN}\",
    \"content\": \"${IP}\",
    \"ttl\": 300,
    \"proxied\": false
  }" | python3 -c "import sys,json; r=json.load(sys.stdin); print('Success:', r.get('success')); [print('  ', rec['name'], '→', rec['content']) for rec in r.get('result',[])]"
