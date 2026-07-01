# AI Orchestrator

Control plane for coordinating AI agents, repository automation, verification,
task tracking, operational checks, and owner notifications.

## Responsibilities

- route work between Hermes, Codex, reviewers, and low-cost reasoning models;
- enforce approval and security boundaries;
- integrate GitHub, Linear, Obsidian, Telegram, and staging infrastructure;
- collect verification evidence and preserve an audit trail;
- manage multiple product repositories through explicit project profiles.

AI Orchestrator does **not** own product source code, scientific algorithms, or
product runtime data. Those remain in their product repositories.

## Pulse of Earth integration

Pulse of Earth remains in
[`IIIH23/earth-pulse-poc`](https://github.com/IIIH23/earth-pulse-poc).
This repository retains the useful control-plane integration through
[`projects/pulse-of-earth.yaml`](projects/pulse-of-earth.yaml).

The Orchestrator may inspect the project, run or observe CI, synchronize
approved roadmap items, publish operational notifications, and coordinate
changes through pull requests. It must not duplicate or directly own the
detector, collection scripts, or `earth-pulse.json`.

See [`docs/ARCHITECTURE_BOUNDARIES.md`](docs/ARCHITECTURE_BOUNDARIES.md) for the
ownership boundary and infrastructure-fit assessment.

## Current maturity

The agent registries, verification tools, repository adapters, and operational
patterns are useful today. The repository exposes a minimal operational API
with real health, version, and managed-project endpoints. Docker and Compose run
that API as a non-root, read-only container.

Terraform and environment-specific staging automation remain prototypes and
must be validated before production use. The Orchestrator runtime is not the
Pulse of Earth application runtime.

## Local runtime

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m pytest -q --ignore=tests/test_staging_smoke.py --ignore=tests/test_lockdown_ssh.py
python -m orchestrator_api.app
```

Install `requirements-quality.txt` for lint/type-check tooling and
`requirements-remote.txt` only when running SSH-backed staging tests.

The local API listens on `http://127.0.0.1:8080` by default:

- `GET /health` — runtime status;
- `GET /version` — service version;
- `GET /v1/projects` — configured project profile identifiers.

Container workflow:

```bash
docker compose up --build
curl http://127.0.0.1:8080/health
```

## Repository map

- `config/` — agent and tool registries.
- `orchestrator_api/` — minimal operational HTTP API.
- `tools/` — verification, synchronization, reporting, and rollback tools.
- `scripts/` — staging and integration helpers.
- `projects/` — product-specific integration profiles.
- `docs/` — architecture, security, operations, and historical reports.
- `tests/` — unit, integration, and environment-dependent checks.
