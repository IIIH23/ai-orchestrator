# Sanitized Gateway Model Diagnostics

Captured from local Hermes gateway/agent logs. No API keys, bearer tokens, cookies, or credential values are included.

## Failed rate-limit call

| Field | Value |
|---|---|
| provider | `openrouter` |
| model | `openrouter/owl-alpha` |
| endpoint/base URL | `https://openrouter.ai/api/v1` |
| HTTP status code | `429` |
| error code/message | `429` / `Rate limit exceeded: free-models-per-day-stealth.` |
| retry count | `3` attempts total |
| rate-limit headers | `X-RateLimit-Limit: 1000`; `X-RateLimit-Remaining: 0`; `X-RateLimit-Reset: 1782777600000` |
| fallback models attempted | none observed in the failed cron run; same model retried 3 times |
| model_router enabled | no evidence in logs; this PR adds `model_router` foundation and schema with `enabled: true` |

Evidence lines were present in `~/.hermes/logs/errors.log` for cron session `cron_dd25d4fecd66_20260630_020137`.

## Failed unavailable-model call

| Field | Value |
|---|---|
| provider | `openrouter` |
| model | `openrouter/owl-alpha` |
| endpoint/base URL | `https://openrouter.ai/api/v1` |
| HTTP status code | `404` |
| error code/message | `404` / `No endpoints found for openrouter/owl-alpha.` |
| retry count | `3` attempts total |
| rate-limit headers | none present |
| fallback models attempted | none observed; same model retried 3 times |
| model_router enabled | no evidence in logs; this PR adds `model_router` foundation and schema with `enabled: true` |

Evidence lines were present in `~/.hermes/logs/agent.log` and `~/.hermes/logs/errors.log` for sessions `20260629_191722_faa8c964` and `20260630_153956_addad96c`.

## Required behavior after this PR foundation

- HTTP 429/rate-limit diagnostics must skip OpenRouter free candidates.
- Paid configured fallbacks may be selected only when enabled in config.
- Code tasks route to Codex.
- Review and architecture tasks route to Claude when available.
- Completion remains blocked until `verification_state` contains evidence.
