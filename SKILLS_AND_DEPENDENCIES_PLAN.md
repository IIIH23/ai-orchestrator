# Skills and Dependencies Plan

For each capability: capability, recommended skill, source, installed/missing, dependencies, risk, needs root, needs secret, decision

1) Capability: Codex coding worker
- Recommended skill: codex
- Source: builtin (autonomous-ai-agents)
- Installed: installed
- Dependencies: Codex CLI + Codex auth for runtime use
- Risk: Medium (requires external API credentials to run effectively)
- Needs root: no
- Needs secret: yes (Codex / OpenAI credentials when executing)
- Decision: KEEP (do not change installation); runtime use requires secret and must use --sandbox workspace-write only

2) Capability: Git and GitHub workflow
- Recommended skill: github-repo-management, github-pr-workflow, github-auth
- Source: builtin
- Installed: installed
- Dependencies: Git; GitHub token for remote operations
- Risk: Medium (external account access, tokens)
- Needs root: no
- Needs secret: yes (GitHub token for remote operations)
- Decision: KEEP (installation present); operations that require tokens are BLOCKED until explicit credentials are provided

3) Capability: Python development and testing
- Recommended skill: python-debugpy, test-driven-development, jupyter-live-kernel
- Source: builtin
- Installed: installed
- Dependencies: python3 (present), test runners (user-managed)
- Risk: Low
- Needs root: no
- Needs secret: no
- Decision: KEEP

4) Capability: CI/CD planning
- Recommended skill: autopilot-verification, autopilot-manager
- Source: builtin/local
- Installed: installed
- Dependencies: CI provider (external) when enabling remote CI
- Risk: Low (planning only); higher when connecting real CI credentials
- Needs root: no
- Needs secret: maybe (CI tokens) — not required for planning
- Decision: KEEP

5) Capability: Docker and container planning
- Recommended skill: (official docker/container skill not installed)
- Source: missing (recommend official docker skill if available)
- Installed: missing
- Dependencies: Docker engine (requires root to install) for local container testing
- Risk: High without root approval
- Needs root: yes (Docker installation)
- Needs secret: no
- Decision: BLOCKED (do not install or provision Docker without explicit root approval)

6) Capability: DevOps and production readiness
- Recommended skill: autopilot-verification, devops (bundled if available)
- Source: autopilot-verification (local), devops category
- Installed: installed (autopilot-verification present)
- Dependencies: infra accounts for production (external)
- Risk: Medium
- Needs root: no
- Needs secret: maybe (cloud credentials) — BLOCKED until provided
- Decision: KEEP (planning and verification only)

7) Capability: Security audit
- Recommended skill: hermes security (CLI) / security audit flow
- Source: builtin (CLI)
- Installed: builtin
- Dependencies: network access to OSV.dev for vulnerability lookup
- Risk: Low for scans; findings may require attention
- Needs root: no
- Needs secret: no
- Decision: KEEP

8) Capability: Backup and restore
- Recommended skill: hermes backup (CLI)
- Source: builtin
- Installed: builtin
- Dependencies: disk space, optional external storage credentials (user-managed)
- Risk: Low
- Needs root: no
- Needs secret: maybe (external storage credentials) — operations blocked until configured
- Decision: KEEP

9) Capability: Logging and observability
- Recommended skill: (no dedicated observability skill bundled)
- Source: missing
- Installed: missing
- Dependencies: backend/agent for metrics (Prometheus/ELK) — external services
- Risk: Medium
- Needs root: maybe (install agents)
- Needs secret: maybe
- Decision: SKIP (recommend adding an official/bundled observability skill later; do not install untrusted third-party plugins)

10) Capability: Documentation
- Recommended skill: design-md, obsidian
- Source: builtin
- Installed: installed
- Dependencies: none
- Risk: Low
- Needs root: no
- Needs secret: no
- Decision: KEEP

11) Capability: API integration
- Recommended skill: google-workspace, airtable, maps, xurl
- Source: builtin
- Installed: installed
- Dependencies: external API credentials for each provider
- Risk: Medium (credentials management)
- Needs root: no
- Needs secret: yes (API keys/tokens)
- Decision: KEEP for installed skills; runtime actions requiring secrets are BLOCKED until credentials provided

12) Capability: n8n workflow design
- Recommended skill: n8n (not bundled)
- Source: missing
- Installed: missing
- Dependencies: n8n host or cloud account; possibly root to install self-hosted
- Risk: High if provisioning external services
- Needs root: maybe
- Needs secret: yes (external account)
- Decision: BLOCKED (do not install or configure without explicit owner approval)

13) Capability: Project planning and task orchestration
- Recommended skill: plan, autopilot-manager
- Source: builtin
- Installed: installed
- Dependencies: none
- Risk: Low
- Needs root: no
- Needs secret: no
- Decision: KEEP

Summary of actions allowed now:
- No INSTALL decisions were chosen because required skills are already bundled/installed or missing features are blocked by root/secret requirements.
- KEEP: codex, github-*, python-debugpy, test-driven-development, autopilot-verification/manager, hermes backup/security, documentation, API integration (skills kept but runtime credential usage is blocked).
- BLOCKED: docker/container skill (requires root), n8n (external host/account), any skill requiring secrets or external paid accounts unless owner provides explicit approval.

Next steps:
1. Review and confirm this SKILLS_AND_DEPENDENCIES_PLAN.md
2. If you approve any BLOCKED items, provide explicit permission and required credentials (outside this repo) and I will proceed with installation steps following the policy constraints.
