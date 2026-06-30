# Pulse of Earth Autonomous Orchestrator Architecture

## Objective

Re-architect Hermes from a chat assistant into a project orchestrator for Pulse of Earth that routes work through RAG, MCP tools, agent delegation, model fallback, and evidence-first verification.

## Required architecture

```text
Telegram / CLI / Cron
        |
        v
Planner -> RAG Librarian -> task context bundle with citations
        |
        v
Budget / Model Router -> model fallback or agent delegation
        |
        +--> Coder / Codex for code implementation
        +--> Reviewer / Claude for architecture/security review
        +--> DevOps for CI/staging/infrastructure diagnostics
        |
        v
MCP Tool Registry -> GitHub, Linear, Obsidian, filesystem, shell, Telegram, Cloudflare, Hetzner
        |
        v
Verifier -> verification_state ledger -> task may be completed only with evidence
```

## RAG memory sources

| Source | Index | Access | Notes |
|---|---|---|---|
| Obsidian | `obsidian` | filesystem | Local mirror in `docs/obsidian`; owner vault writes require approval. |
| GitHub repo | `github_repo` | filesystem/GitHub | Source, tests, docs, workflows, config. |
| Linear | `linear` | Linear GraphQL/MCP | Requires `LINEAR_API_KEY`; current key status must be verified externally. |
| GitHub Actions logs | `github_actions_logs` | GitHub API | Used for CI failure diagnosis and verification evidence. |
| Hermes logs | `hermes_logs` | redacted filesystem logs | Secret redaction required before indexing or reporting. |

## MCP tool layer

Tool definitions live in `config/tool-registry.yaml` and are loaded by `tools/tool_registry.py`. High-impact tools are gated:

- GitHub: secret changes, protected branches, merge, and side-effect dispatch require approval.
- Linear: writes require scoped token and Linear readback evidence.
- Cloudflare: DNS mutations require exact owner approval and rollback.
- Hetzner: paid resource changes require exact owner approval and cost statement.
- Shell: destructive or production operations require approval.

## Agent registry

Agent definitions live in `config/agent-registry.yaml` and are loaded by `tools/agent_registry.py`.

| Agent | Purpose |
|---|---|
| Planner | Decompose tasks, classify risk, define acceptance criteria. |
| DevOps | CI/CD, staging checks, rollback plans, infrastructure diagnostics. |
| Coder / Codex | Implementation, tests, debugging, refactors. |
| Reviewer / Claude | Architecture/security review and independent verdicts. |
| RAG Librarian | Build context bundles with citations from indexed sources. |
| Verifier | Collect evidence and block completion without proof. |
| Budget / Model Router | Detect 429/rate limits, avoid free OpenRouter routes, pick paid fallback or delegation. |

## Model fallback

`tools/model_router.py` implements the first routing primitive:

1. Detect HTTP 429/rate-limit errors from status, message, code, or rate-limit headers.
2. If the failed provider is OpenRouter, skip free OpenRouter candidates after rate limit.
3. Prefer configured paid model candidates.
4. Delegate code tasks to Codex.
5. Delegate review/architecture/security tasks to Claude when available.
6. Return structured diagnostics without printing API keys or secrets.

## Verification loop

`tools/verification_state.py` stores a JSON ledger under `artifacts/verification_state.json`.

Rule: a task cannot be marked `completed` unless it has at least one evidence item. Evidence can be a test result, CI status, API readback, log excerpt, artifact, or external side effect.

## Repository file structure

```text
config/
  agent-registry.yaml          # agent roles and boundaries
  tool-registry.yaml           # MCP-style tool definitions and gates
  orchestrator-schema.yaml     # secret-free orchestration config schema
docs/
  ORCHESTRATOR_ARCHITECTURE.md # architecture proposal and implementation plan
  GATEWAY_MODEL_DIAGNOSTICS.md # sanitized failed-call diagnostics
tools/
  agent_registry.py            # registry loader and route selection
  model_router.py              # rate-limit/fallback/delegation router
  tool_registry.py             # tool loader and approval gate
  verification_state.py        # evidence ledger; blocks completion without evidence
tests/
  test_orchestrator_foundation.py
```

## Implementation plan

1. Add foundation modules and tests for registries, model routing, and verification state.
2. Wire the router into Hermes/Pulse autopilot task execution so 429 failures trigger fallback instead of repeated same-model retries.
3. Add a RAG indexing command that builds sanitized citation bundles from Obsidian, repo files, Linear metadata, Actions logs, and Hermes logs.
4. Replace ad-hoc tool use with the MCP/tool registry risk gate.
5. Integrate Codex and Claude delegation adapters with task packets and output verification.
6. Extend CI to run orchestrator foundation tests and publish verification artifacts.
7. Add owner approval workflows for secrets, Cloudflare, Hetzner, and production actions.

## Approval boundary

No secrets are committed. No Cloudflare, Hetzner, production, firewall, DNS, or paid-resource changes are performed by this PR.
