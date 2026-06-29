#!/usr/bin/env bash
# Verify model routing configuration
set -euo pipefail

echo "=== Model Routing Verification ==="
echo ""

# Check Hermes config
echo "1. Hermes primary model:"
hermes config show 2>/dev/null | grep "Model:" | head -n1 || echo "  FAIL: hermes not configured"

echo ""
echo "2. Provider:"
hermes config show 2>/dev/null | grep -A2 "API Keys" | head -n3

echo ""
echo "3. Cron jobs:"
hermes cron list 2>/dev/null | grep -E "pulse-autopilot|active" || echo "  No cron jobs"

echo ""
echo "4. Required scripts exist:"
for s in scripts/verify-model-routing.sh scripts/bootstrap-staging.sh tools/linear_sync.py tools/rollback.py; do
  if [ -f "$s" ]; then
    echo "  OK: $s"
  else
    echo "  MISSING: $s"
  fi
done

echo ""
echo "Done."
