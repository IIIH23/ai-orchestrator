# Telegram Integration

> Last updated: 2026-06-27

## Bot

- **Name**: TerraBits Infra Bot
- **Token**: stored in GitHub Environment `staging` as `TELEGRAM_BOT_TOKEN`

## Chats

| Chat | ID | Purpose |
| --- | --- | --- |
| TerraBits Staging Alerts | `TELEGRAM_STAGING_CHAT_ID` | staging notifications |
| TerraBits Production Alerts | `TELEGRAM_PRODUCTION_CHAT_ID` | production notifications |

## Notification Types

| Event | Severity | Message |
| --- | --- | --- |
| Deployment started | 🔵 info | Deploy started for {app} @ {commit} |
| Deployment success | 🟢 success | Deploy OK: {app} @ {commit} |
| Deployment failure | 🔴 critical | Deploy FAILED: {app} @ {commit} |
| Rollback started | 🟡 warning | Rolling back {app} |
| Rollback success | 🟢 success | Rollback OK: {app} |
| Rollback failure | 🔴 critical | Rollback FAILED: {app} |
| Health check failure | 🟡 warning | {count} health checks failed |
| High RAM | 🟡 warning | RAM usage > 80% |
| High disk | 🟡 warning | Disk usage > 80% |
| Container crash | 🔴 critical | Container {name} restarted {n} times |
| Backup failure | 🔴 critical | Backup failed for {app} |
| Certificate expiry | 🟡 warning | Certificate expires in {days} days |
| Security alert | 🔴 critical | {description} |

## Message Format

- Markdown formatting
- Environment tag: `[staging]` or `[production]`
- Commit SHA link to GitHub
- No secrets, no full stack traces, no env dumps
- Max 4096 chars per message

## Rate Limiting

- Cooldown: 5 minutes between same alert type
- Max 10 messages per hour per chat
- Deduplication: identical alerts within cooldown are suppressed
