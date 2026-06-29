#!/usr/bin/env bash
# run-claude-review.sh — wrap Claude Code for high-risk review
set -euo pipefail

PLAN_FILE="${1:?Usage: $0 <plan-or-diff-file>}"
TASK_SLUG="${2:-review}"

REVIEW_DIR="artifacts/reviews"
mkdir -p "$REVIEW_DIR"

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
REVIEW_FILE="${REVIEW_DIR}/${TIMESTAMP}-${TASK_SLUG}-claude.md"

# Run Claude code review (read-only, no infrastructure changes)
claude review --plan "$PLAN_FILE" > "$REVIEW_FILE" 2>&1

echo "Review saved: $REVIEW_FILE"
