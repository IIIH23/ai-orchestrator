# Model Routing

> Generated: 2026-06-27
> Based on: ORCHESTRATOR_POLICY.md sections 1-3 + ORCHESTRATOR_COMPLETION_PROMPT section 3

## Routing Rules

### Primary Model: openrouter/owl-alpha
Use for:
- Owner dialogue and strategy
- Task routing and prioritization
- Discovery and planning
- Synthesis and reporting
- All orchestration decisions

### Auxiliary / Fallback: GPT-5 mini (via appropriate provider)
Use for:
- Cron orchestration
- Brief checks and validations
- Low-cost automation
- Fallback if owl-alpha is unavailable

### Coding Worker: Codex CLI
Use for:
- Code implementation and refactoring
- Unit/integration tests
- Shell scripts
- GitHub Actions workflows
- Dockerfiles
- Code-related documentation

**Only via**: `codex exec --sandbox workspace-write "<narrow task>"`

### High-Risk Reviewer: Claude Code
Use for:
- Security changes
- Production architecture
- Authentication and permissions
- Secrets management
- Database migrations
- Infrastructure changes
- Deployment changes
- Rollback logic
- Irreversible operations
- Financially significant decisions

## Decision Tree

```
Task received
  ├─ Is it a code implementation? → Codex CLI (workspace-write)
  ├─ Is it a high-risk change? → Claude Code (review)
  ├─ Is it a brief check/report? → GPT-5 mini
  ├─ Is it orchestration/dialogue/synthesis? → owl-alpha (default)
  └─ Fallback: GPT-5 mini if owl-alpha unavailable
```

## Escalation

| Situation | Action |
| --- | --- |
| owl-alpha unavailable | Use GPT-5 mini, notify owner, prepare switch plan |
| Codex fails | Retry once with narrower task scope, then report |
| High-risk detected | Stop, invoke Claude via skill, await verdict |
| Budget exceeded | Stop, report usage, do not spend more |

## Executable policy path

The operational implementation is:

```text
config/agent-registry.yaml
  -> tools.agent_runtime.resolve_route
  -> tools.agent_router.route_task
  -> tools.review_gate.run_review_gate
  -> tools.claude_code_adapter.run_claude
```

Static `available` values enable an integration; runtime health is
authoritative for execution. Mandatory reviewers fail closed when their
healthcheck fails. Claude verdicts are machine-readable and never inferred from
free-form text.

## Profile-to-Model Mapping

| Profile | Primary Model | Coding Worker | Reviewer |
| --- | --- | --- | --- |
| default (owner) | owl-alpha | Codex (with approval) | Claude Code |
| development | owl-alpha | Codex | Claude Code (high-risk) |
| architecture | owl-alpha | Codex (ADR only) | Claude Code |
| research | owl-alpha | — | — |
| devops | owl-alpha | Codex | Claude Code (infra) |
| design | owl-alpha | — | — |
| finance | owl-alpha | — | — |
| team | owl-alpha | — | — |
