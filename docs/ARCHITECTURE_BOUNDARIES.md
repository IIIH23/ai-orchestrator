# Architecture Boundaries

## Decision

AI Orchestrator and Pulse of Earth use separate repositories with an explicit
control-plane integration.

| Concern | Owner |
| --- | --- |
| Agent routing, policy, approvals, verification, notifications | AI Orchestrator |
| GitHub/Linear/Obsidian/Telegram adapters | AI Orchestrator |
| Generic staging, monitoring, and rollback patterns | AI Orchestrator |
| Seismic acquisition and signal processing | Pulse of Earth |
| 26-second detector and collection scripts | Pulse of Earth |
| Public `earth-pulse.json` contract and publication workflow | Pulse of Earth |
| Breathing-product interpretation | Pulse of Earth |

## Infrastructure fit for Pulse of Earth

Useful now:

- repository inspection and pull-request coordination;
- scheduled verification and evidence collection;
- Linear roadmap synchronization;
- Obsidian decision-log synchronization;
- Telegram operational alerts;
- reusable security, approval, monitoring, and rollback policies.

Runtime boundary:

- `compose.yaml` runs the AI Orchestrator operational API and exposes a real
  health endpoint;
- the Orchestrator container does not contain or serve Pulse of Earth product
  code;
- `infrastructure/terraform/main.tf` is a design document containing fenced HCL,
  not an executable Terraform module;
- local CI covers unit tests and validates the Orchestrator container; remote
  staging tests remain explicit environment checks;
- PostgreSQL, Caddy, Cloudflare, and n8n are not required for the existing
  serverless JSON-feed architecture.

## Integration rule

Product code never moves into this repository. Product-specific configuration
is allowed only under `projects/` and must reference a separate repository,
declare allowed operations, and list product-owned artifacts.

The Orchestrator can become part of a future Pulse of Earth application
platform only when a real backend requires it. Until then, GitHub Actions in the
product repository remain the runtime scheduler and publisher.
