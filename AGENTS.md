# AI Orchestrator Agent Instructions

## Project

AI Orchestrator coordinates agents and operational integrations across product
repositories. Product code remains in its owning repository; product-specific
access is declared under `projects/`.

## Agent roles

Hermes:
- task routing
- planning
- summaries
- tool coordination
- project memory
- final reports

Codex:
- code implementation
- refactoring
- debugging
- tests
- repository analysis

## Cost policy

- Use GPT-5 mini for routing and concise coordination.
- Delegate substantial coding work to Codex CLI.
- Use `workspace-write` sandbox only.
- Do not use premium models automatically.
- Do not invoke a second model unless explicitly requested.

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
5. Run targeted tests.
6. Show `git diff`.
7. Leave changes uncommitted unless explicitly requested.

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
