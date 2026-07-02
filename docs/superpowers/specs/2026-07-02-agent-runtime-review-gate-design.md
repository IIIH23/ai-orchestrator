# Agent Runtime and Claude Review Gate

## Goal

Connect static routing policy to real runtime availability and provide a
fail-closed, machine-readable Claude Code review gate for sensitive tasks.

## Boundaries

- `agent_router` remains a pure policy decision module.
- `agent_runtime` is an infrastructure adapter that probes registry
  healthchecks with bounded subprocesses and returns availability evidence.
- `review_gate` is an application service. It resolves a route, determines
  whether Claude is required, invokes an injected reviewer port, validates the
  verdict, and returns a stable result.
- `claude_code_adapter` remains the only module aware of Claude CLI arguments.

No queue, daemon, remote deployment, or Codex execution adapter is introduced
in this increment.

## Data flow

1. Load and validate the agent registry.
2. Probe only agents relevant to routing, with a per-command timeout and no
   shell invocation.
3. Pass observed availability to `route_task`.
4. Stop when a required primary or reviewer is unavailable.
5. If Claude review is required, execute it in read-only `review` mode.
6. Parse a strict JSON verdict: `approve`, `request_changes`, or `blocked`.
7. Return route, evidence, verdict, findings, and session metadata. Do not
   infer approval from free-form prose.

## Security invariants

- Registry healthchecks never execute through a shell.
- Unsupported commands and malformed registry entries fail closed.
- High-risk or mandatory-category tasks never bypass an unavailable Claude
  reviewer.
- Review mode cannot edit files or run shell commands.
- Prompts and responses remain absent from metadata audit logs.
- A malformed or unknown Claude verdict is treated as a failed gate.

## Test strategy

- Unit tests cover health success, timeout, missing executable, and special
  Python executable resolution.
- Router integration tests prove observed availability overrides static flags.
- Review-gate tests cover no-review routes, required review, unavailable
  reviewer, each valid verdict, and malformed output.
- The full existing suite and GitHub CI remain mandatory.
