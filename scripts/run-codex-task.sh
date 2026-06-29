#!/usr/bin/env bash
# run-codex-task.sh — wrap Codex CLI with logging and boundary checks
set -euo pipefail

TASK_FILE="${1:?Usage: $0 <task-file>}"
WORKDIR="${2:-.}"

if [ ! -f "$TASK_FILE" ]; then
echo "ERROR: task file not found: $TASK_FILE" >&2
  exit 1
fi

# Safety checks
if grep -qi "danger-full-access\|yolo\|bypass" "$TASK_FILE"; then
  echo "ERROR: task file contains forbidden flags (danger-full-access/yolo/bypass)" >&2
  exit 1
fi

# Run Codex in workspace-write only
codex exec --sandbox workspace-write "$(cat "$TASK_FILE")"

echo "Codex task completed."
