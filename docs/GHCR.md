# GHCR (GitHub Container Registry)

> Last updated: 2026-06-27

## Registry

- **URL**: ghcr.io
- **Namespace**: github.com/hermes/pulse-of-earth (or owner org)
- **Auth**: GITHUB_TOKEN (no extra credentials needed for pull)

## Image Naming

| Image | Tag Format | Example |
| --- | --- | --- |
| pulse-of-earth | sha-<commit> | ghcr.io/hermes/pulse-of-earth:sha-a1b2c3d |
| pulse-of-earth | staging | ghcr.io/hermes/pulse-of-earth:staging |
| pulse-of-earth | stable | ghcr.io/hermes/pulse-of-earth:stable |

## Tag Policy

- **Never use `latest`** for deployments
- Use immutable SHA tags for production
- Use environment tags (staging, stable) as mutable pointers
- Retain all SHA-tagged images indefinitely
- Clean up dangling images monthly

## Build Pipeline

1. CI builds on push to main
2. Trivy scan (CRITICAL/HIGH block)
3. Multi-stage Dockerfile (minimal image)
4. Push to GHCR with SHA tag + staging tag
5. Cosign keyless signing
6. SBOM generated (SPDX JSON)
7. GitHub Artifact Attestation

## Pull Policy

- Staging VPS pulls by SHA tag (immutable)
- After verifying SHA works, update staging pointer
- Production pulls only after staging verified

## Security

- Non-root container user
- Read-only filesystem where possible
- No secrets in image layers
- Pinned base images (SHA)
- Multi-stage builds
- Resource limits in compose
