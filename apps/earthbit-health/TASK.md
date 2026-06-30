# Task: Add /version endpoint to earthbit-health

## Goal
Add a `/version` endpoint to the earthbit-health Flask app that returns:
```json
{"version": "0.1.0", "service": "earthbit-health"}
```

Also add a unit test for it.

## Files to modify
- `apps/earthbit-health/app.py` — add /version route
- `apps/earthbit-health/test_app.py` — add test_version

## Constraints
- Low-risk change, no infrastructure modifications
- Keep existing /health endpoint unchanged
- Use Flask test_client for unit test
