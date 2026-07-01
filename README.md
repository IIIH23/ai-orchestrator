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
patterns are useful today. The Docker/Compose and Terraform assets are
prototypes and are not a production runtime for Pulse of Earth without further
work. In particular, the current Compose service is an Orchestrator utility
container, not the Earth Pulse application.

## Repository map

- `config/` — agent and tool registries.
- `tools/` — verification, synchronization, reporting, and rollback tools.
- `scripts/` — staging and integration helpers.
- `projects/` — product-specific integration profiles.
- `docs/` — architecture, security, operations, and historical reports.
- `tests/` — unit, integration, and environment-dependent checks.
