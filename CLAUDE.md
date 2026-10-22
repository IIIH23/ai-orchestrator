@AGENTS.md

# Claude Code in this repository

## Commands
- Tests: `.venv/bin/python -m pytest -q --ignore=tests/test_staging_smoke.py --ignore=tests/test_lockdown_ssh.py`
  (always `python -m pytest`; bare `pytest` fails with `No module named tools`).
- Lint and types, as in CI: `.venv/bin/python -m ruff check .` and `.venv/bin/python -m mypy`.
- Second opinion from Codex on the current branch: `/codex-review`.

## Trunk-based workflow (ADR-0003)
- `main` is always green. One logical change per short branch
  (`feat|fix|security|docs|ci|refactor|chore/<slug>`), PR with a Conventional Commits title.
- RED first: show the new test failing against `main` in the PR body.
- Merge only squash, only with green CI. In an interactive session Claude may
  squash-merge its own green PRs and reports it; workers launched by the daemon never merge.
- Repository settings, rulesets and history rewrites need the owner's explicit approval.
- Unfinished code lands unwired or behind config, never in a long-lived branch.

## Local-only files
- `.claude/settings.local.json` holds the interactive session's permissions. It is
  untracked on purpose: tracked `.claude/settings.json` would reach the task
  worktrees the daemon gives to workers (see `tests/test_claude_code_adapter.py`).
