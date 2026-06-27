PRODUCTION READINESS CHECKLIST

This document summarizes the production readiness plan for Pulse of Earth. It is a living document for operations and reviewers.

1) Application architecture

- Overview: modular Python services and CLI utilities for data collection, processing, and visualization. Core components:
  - data-ingest: ingestion scripts and adapters
  - processing: core processing pipelines (batch/stream)
  - api: lightweight REST API for visualization and integration
  - ui: static site / dashboards (deployed separately)
  - ops: monitoring, backups, CI templates
- Deployment model: containerized services (Docker) deployed to staging and production hosts (or k8s) behind load balancers.
- Data stores: object storage for raw data, relational DB for metadata, time-series DB for telemetry.

2) Environments

- development: local developer environment; tests run with python3 and sandboxed Codex for code generation.
- staging: production-like environment for integration tests and approval gate.
- production: hardened environment with strict access control and rollback capability.

3) Secrets policy

- No secrets stored in repository.
- Use environment-specific secret managers (AWS Secrets Manager, HashiCorp Vault, or git-crypt) approved by owners.
- Short-lived tokens preferred; least privilege principle.
- Operators must avoid printing secrets in logs.

4) Docker plan (design, not executed)

- Provide Dockerfile templates for service components; multi-stage builds for smaller images.
- Do not install Docker on this host without explicit root approval.
- Local dev: provide docker-compose.yaml templates for developers with mounted volumes and non-root containers.
- CI: build images in CI and push to private registry guarded by credentials (not in repo).

5) CI/CD plan

- CI: run smoke tests, unit tests, lint, and build artifacts. Use GitHub Actions or chosen CI provider.
- Validate: run tests in a clean environment; verify dependency locking before artifacts accepted.
- CD: manual approval gate required before promoting from staging to production.
- No automatic git push or remote changes from the autopilot.

6) Health checks

- Provide /health and /ready endpoints returning simple JSON and application-specific readiness.
- Health checks must be fast (<200ms) and safe to call frequently.

7) Structured logs

- Use JSON-formatted logs with fields: timestamp, level, service, request_id, correlation_id, message, and structured metadata.
- Ensure logs are rotatable and shipped to centralized logging (ELK/CloudLog) via agents.

8) Monitoring

- Instrument metrics (Prometheus) for critical counters: request rates, error rates, processing lag, queue sizes, disk usage.
- Set alert thresholds and escalation playbooks.

9) Backup

- Backup plan: daily snapshots of critical metadata and weekly full backups of object storage metadata.
- Store backups in an external secure bucket, lifecycle policy for retention, and verify restore process monthly.

10) Restore

- Documented restore runbook: steps to restore metadata, recover object storage pointers, and rehydrate curated datasets.
- Test restores in staging quarterly.

11) Rollback

- Maintain immutable artifacts; rollback by redeploying previous artifact version and running smoke tests.
- Keep database migration backward-compatible or support downgrade scripts when needed; require manual approval for destructive migrations.

12) Dependency locking

- Use pinned dependencies (pyproject.lock, requirements.txt, or poetry lock).
- Run dependency scans for CVEs and upgrade regularly.

13) Vulnerability scanning

- Integrate OSV and SCA scanning into CI.
- Block releases with critical vulnerabilities unless mitigated.

14) Least privilege

- Apply least privilege for service accounts, CI tokens, and operator roles.
- Rotate keys on schedule.

15) Production deployment approval gate

- All production promotions require:
  - passing CI (tests, lint, vulnerability scan)
  - staging smoke tests passed
  - manual approval by an authorized operator
  - documented rollback plan attached to the deployment

Notes and constraints (do not perform here):
- Do not open network ports, change firewall rules, or modify DNS from this run.
- Do not create paid cloud resources from this environment.
- Do not perform any production deploys or DB migrations.

Contact: project owners and operators recorded in docs/PARTNER_PROFILE_TEMPLATE.md
