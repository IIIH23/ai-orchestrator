# Claude Code integration

The orchestrator invokes Claude Code through `tools/claude_code_adapter.py`.
The adapter uses the official non-interactive CLI JSON interface, sends prompts
over stdin, applies bounded tool permissions, enforces time and turn limits, and
parses the final result into a stable internal shape.

## Setup

1. Install Claude Code and complete its normal authentication flow.
   On native Windows, install Git for Windows and set
   `CLAUDE_CODE_GIT_BASH_PATH` if Git is outside its standard location.
2. Verify the integration:

   ```bash
   python tools/claude_code_adapter.py health
   ```

The health check verifies both installation and authentication. It returns a
non-zero status until `claude auth login` has been completed.

3. Run a read-only review:

   ```bash
   echo "Review the current diff for security defects." \
     | python tools/claude_code_adapter.py run --mode review --cwd .
   ```

`CLAUDE_CODE_BIN` can point to a non-standard executable. Claude Code's own
authentication is preserved (`ANTHROPIC_API_KEY` when used); unrelated provider
and deployment secrets are removed from the child environment.

## Execution modes

| Mode | Permission mode | Intended use |
|---|---|---|
| `review` | `plan` | Read-only review and verdict |
| `plan` | `plan` | Read-only implementation plan |
| `edit` | `acceptEdits` | Bounded edits plus allowlisted local checks |

The adapter never enables `--dangerously-skip-permissions`. The `edit` mode
denies pushes, destructive Git operations, GitHub CLI operations, and shell
deletion. Project defaults in `.claude/settings.json` provide a second policy
layer; command-line restrictions are applied per run.

## Routing behavior

`tools/agent_router.py` separates implementation from independent review:

- Codex remains the primary implementation/integration worker.
- Claude Code is the primary reviewer.
- All high-risk work requires Claude review; medium-risk work still requires
  owner approval and receives Claude review when its task category mandates it.
- Security, architecture, infrastructure, permission, rollback, database, and
  deployment tasks require Claude review regardless of nominal risk.
- Missing Claude availability blocks a mandatory review instead of silently
  substituting the implementation agent.

The `available` registry flag means the integration is enabled. Runtime
availability is collected by `tools/agent_runtime.py` and supplied to
`route_task`; observed health overrides the static flag.

## Runtime review gate

Run a policy-aware review from the repository root:

```bash
python tools/review_gate.py security high \
  --cwd . \
  --prompt "Review the current branch for authentication vulnerabilities."
```

For long prompts, omit `--prompt` and pipe the request over stdin. The command:

1. probes the registered agents without using a shell;
2. resolves the primary worker and mandatory reviewers;
3. stops if a required worker is unavailable;
4. invokes Claude in read-only review mode;
5. accepts only `approve`, `request_changes`, or `blocked`;
6. returns JSON and uses exit code `0`, `1`, or `2` for approval/not-required,
   rejected/blocked, or execution/policy failure respectively.

Programmatic callers can use `tools.agent_runtime.resolve_route()` to retain
both the route decision and per-agent health evidence.

## Audit and privacy

Use `--audit-log PATH` to append cost, duration, turn count, mode, and session
metadata. Prompts, responses, and environment values are not written to this
audit log.

## References

- [Claude Code CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage)
- [Claude Code SDK / structured output](https://docs.anthropic.com/en/docs/claude-code/sdk)
- [Claude Code permissions](https://docs.anthropic.com/en/docs/claude-code/iam)
