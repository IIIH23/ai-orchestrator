# AI Orchestrator Agent Instructions

## Project

AI Orchestrator coordinates agents and operational integrations across product
repositories. Product code remains in its owning repository; product-specific
access is declared under `projects/`.

## Agent roles

Routing between workers is deterministic code (`tools/agent_router.py`,
`config/agent-registry.yaml`), not a model decision.

Codex CLI (worker):
- code implementation, refactoring, debugging, tests
- runs as `codex exec -s workspace-write` inside a per-task worktree,
  limited to the task's `allowed_paths`; never merges or pushes

Claude Code (reviewer, interactive engineer):
- independent review of high-risk tasks through `tools/review_gate.py`
  (read-only, settings from `config/claude-review-settings.json`)
- in interactive sessions: architecture, specs, PRs (see `CLAUDE.md`)

Cross-model rule: the model that wrote a change does not review it. Codex
reviews Claude's branches with `codex review --base main`.

Hermes (planner / owner communication) is not part of this repository's
runtime; its role is an open owner decision.

## Cost policy

- Deterministic code first; a model is used only where code cannot decide.
- Use `workspace-write` sandbox only.
- Do not use premium models automatically.
- Invoke a second model only through the review gate, for high-risk or
  sensitive tasks; never for routine work.
- Full policy, budgets and enforcement status: `docs/TOKEN_POLICY.md`.

## Repository safety

- Work only inside this repository.
- Never read or modify `~/.hermes`, `~/.codex`, SSH keys, or system credentials.
- Never expose `.env` values.
- Never use `danger-full-access`.
- Never commit, push, deploy, or create external issues without explicit approval.

## Development workflow

1. Check `git status`.
2. Inspect relevant files.
3. Make the smallest necessary change.
4. Add or update tests.
5. Run tests with `python -m pytest` (bare `pytest` cannot import `tools`).
6. Show `git diff`.
7. Workers leave changes uncommitted; the daemon commits verified work to
   `task/<id>-a<n>`. Interactive sessions follow the trunk-based flow in
   `CLAUDE.md` (short branch, PR, green CI, squash merge).

## Code quality

- Prefer small modules.
- Include error handling.
- Add type hints where appropriate.
- Avoid unnecessary dependencies.
- Document non-obvious decisions.

## Compiled wiki workflow

- Search the compiled wiki with `python tools/wiki_layer.py query "<question>"`
  before repeatedly reading raw project notes.
- Treat files under `knowledge/raw/` as immutable after ingest.
- Use `python tools/wiki_layer.py ingest` for new sources.
- Curate generated draft pages under `knowledge/wiki/pages/`; preserve source
  paths and SHA-256 provenance.
- File durable conclusions back into the wiki with cross-links instead of
  leaving them only in chat history.
- Run `python tools/wiki_layer.py reindex` and
  `python tools/wiki_layer.py lint` after wiki edits.
- Read raw sources only for citation verification or documented knowledge gaps.
