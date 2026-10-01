# Dispatcher

`tools/orchestrator_daemon.py` moves a queued task through the whole cycle
without manual steps.

```text
enqueue ──► SQLite queue ──► claim (lease)
                               │
              owner approval gate (non-low risk)      ─► needs_owner
              dirty-baseline gate                      ─► failed: dirty_baseline
                               │
              route (registry + runtime health)
              git worktree  task/<id>-a<attempt>
                               │
              worker gateway: budget ─► breaker ─► worker ─► fallback
                               │                              (always logged
                               │                               and notified)
              verifier: changes exist, inside allowed_paths, tests pass
              Claude Code review gate (high-risk / sensitive tasks)
                               │
              commit on the task branch ─► ledger ─► queue: done
```

## Guarantees

- The verifier alone decides the verdict. A worker exit code is not trusted,
  and a crashed verifier is a failure.
- A worker is never replaced silently: every substitution is a ledger event
  and a notification.
- The baseline checkout is never modified. Each attempt runs in its own
  worktree under `ORCHESTRATOR_STATE_DIR/worktrees`.
- A crashed dispatcher loses nothing: the lease expires and the task is
  claimed again.
- The ledger is written before the queue transition.

## What it does not do

- It does not push or open pull requests. A finished task is a local commit
  on `task/<id>-a<attempt>`; publishing stays with the owner.
- Budget and circuit-breaker state are in memory and reset on restart.
- Linear and Obsidian status sync is not wired.

## Usage

```bash
export ORCHESTRATOR_STATE_DIR=/var/lib/orchestrator   # outside any repository

python tools/orchestrator_daemon.py enqueue task.json
python tools/orchestrator_daemon.py run --once        # one task
python tools/orchestrator_daemon.py run               # until SIGTERM
python tools/orchestrator_daemon.py status
python tools/orchestrator_daemon.py approve <task-id>
```

Task file:

```json
{
  "id": "add-retry-constant",
  "project": "ai-orchestrator",
  "task_type": "code",
  "risk_level": "low",
  "goal": "Add MAX_RETRIES = 3 to tools/example.py",
  "repo": "/srv/ai-orchestrator",
  "allowed_paths": ["tools/"],
  "test_command": ["python", "-m", "pytest", "-q"],
  "max_attempts": 2
}
```

`allowed_paths` and `test_command` are required. Only `python -m unittest`
and `python -m pytest` are accepted as test commands. A task with a risk
level other than `low` waits for `approve`.

## Configuration

- `config/orchestrator.yaml` — lease, polling, breaker and budget limits.
  A project or worker without a budget limit is denied.
- `config/agent-registry.yaml` — workers, their `command`, `fallback` chain
  and the `available` kill switch.
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — optional notifications.
