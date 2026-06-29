# Owner Notification Flow

> Last updated: 2026-06-29

```
Task completed
  → tools/telegram_notify.py (--severity success --message "...")
  → GitHub Actions log
→ Linear issue (comment)
  → docs/executions/<timestamp>-<task>.md
  → docs/ORCHESTRATOR_STATUS.md (auto-update)
```

## Telegram delivery

- Bot: @earthbit_bot 8704929397
- Staging chat: TELEGRAM_STAGING_CHAT_ID env var
- Production chat: TELEGRAM_PRODUCTION_CHAT_ID env var
- Script: `python3 tools/telegram_notify.py --severity <level> --message "..."`
- Cooldown: betyen same alert type
- Max 10 messages/hour (in config)

## Retry and failure handling

1. Спробувати delivery через python3 tools/telegram_notify.py
2. Якщо failure → save report у Git
3. Якщо повторний failure → записати status
4. Якщо Linear недоступний → GitHub PR comment

## Secrets redaction

- У logs секрети не показуються
- якщо --details містить secret pattern → redacted
- Telegram messages не містять credentials
