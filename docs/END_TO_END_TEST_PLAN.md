# End-to-End Staging Test

> Last updated: 2026-06-29
> Status: pending

## Test Application: earthbit-health

Minimal HTTP service for testing full pipeline.

### Service Specification

- **Language**: Python 3.11
- **Framework**: Flask
- **Endpoint**: `GET /health` → `{"status": "ok", "service": "earthbit-health"}`
- **Port**: 8080
- **Docker image**: `ghcr.io/IIIH23/earth-pulse-poc/earthbit-health:sha-<commit>`

### Files to Create

```
apps/earthbit-health/
├── app.py              # Flask app
├── requirements.txt    # Flask
├── test_app.py         # Unit test
├── Dockerfile          # Multi-stage build
└── compose.yaml        # Docker Compose
```

### Pipeline Steps

1. Feature branch → PR
2. CI: lint → test → security scan
3. Docker build → push to GHCR
4. Trivy scan
5. SBOM generation
6. Cosign signature
7. GitHub attestation
8. Deploy to staging via SSH
9. Caddy reverse proxy
10. HTTPS check
11. Health check
12. Telegram notification

### Rollback Test

1. Deploy image with failing health check
2. Verify automatic rollback
3. Verify Telegram alert
4. Verify no broken image remains active

## Owner Actions Required

1. Approve DNS record creation (if needed)
2. Approve Cloudflare Proxy enablement (after HTTPS verified)
3. Review and merge PR
