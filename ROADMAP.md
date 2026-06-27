# Pulse of Earth Roadmap

Pulse of Earth is a research and software project for collecting, processing, analyzing, and visualizing Earth-related data.

## 1. Audit

- Objectives: Review repository structure, current assets, assumptions, and missing project controls.
- Success criteria: Inventory exists, gaps are ranked, and immediate risks are visible.
- Estimated effort: S
- Progress: Created audit/FILE_INVENTORY.md (commit 6ec83a1). Latest audit executed by night-shift autopilot; see logs/AUTOPILOT_LOG.md for details.
- Next actionable task: Create minimal smoke tests and CI workflow skeleton to validate repository invariants.
- Recent update: Minimal smoke test and CI workflow skeleton files were created locally (tests/smoke_test.sh, .github/workflows/smoke.yml). Local smoke test passed ("Smoke test passed: 2 required files found; 0 Python file(s) compiled."). Commit was created locally in this cycle (autopilot cycle 6).

## 2. Port Logic

- Objectives: Move useful existing logic into the repository with clear ownership and minimal dependencies.
- Success criteria: Core logic runs locally and has a documented entry point.
- Estimated effort: M
- Next actionable task: Identify the first logic source to port and record its expected inputs and outputs.
- Recent update: Selected the audit/file-inventory generator (audit/FILE_INVENTORY.md) as the first logic source to port. A specification has been recorded at docs/PORTING_FIRST_SOURCE.md describing inputs, outputs, and minimal CLI surface.
- New progress (2026-06-27T03:55:33Z): Implemented tools/inventory.py (stdlib-only CLI) and tests/test_inventory.sh (fixture-based smoke test). Ran tests: inventory test and repository smoke test — PASSED.
- Next actionable task: Wire the script into .github/workflows/smoke.yml so the inventory runs in CI and continue adding focused tests.

## 3. Hermes-Obsidian

- Objectives: Define how Hermes project memory syncs with Obsidian notes.
- Success criteria: Note structure, sync direction, and conflict behavior are documented.
- Estimated effort: M
- Next actionable task: Draft the target Obsidian folder and note naming scheme.

## 4. Hermes-Linear

- Objectives: Define how Hermes coordinates planning and task tracking with Linear.
- Success criteria: Project labels, issue lifecycle, and update cadence are documented.
- Estimated effort: M
- Next actionable task: Draft the Linear issue fields needed for Pulse of Earth work.

## 5. Deterministic Workflows With n8n

- Objectives: Design repeatable n8n workflows for scheduled or event-driven project automation.
- Success criteria: Initial workflow specs include triggers, inputs, outputs, retries, and failure handling.
- Estimated effort: L
- Next actionable task: Choose one workflow candidate and write its trigger and expected output.

## 6. GitHub Sync

- Objectives: Establish repository sync expectations for issues, docs, status, and automation outputs.
- Success criteria: Sync scope and manual approval boundaries are documented.
- Estimated effort: M
- Next actionable task: Define which project artifacts should be mirrored to GitHub.

## 7. Deterministic Workflows & Tests

- Objectives: Add focused checks that validate core logic and basic operational workflows.
- Success criteria: Targeted tests and smoke-tests can run locally with documented commands.
- Estimated effort: M
- Next actionable task: Add a smoke-test checklist for the first runnable workflow.

## 8. Docs & Backup/Restore

- Objectives: Document project setup, operations, backup scope, and restore procedure.
- Success criteria: A clean checkout can be configured, backed up, and restored from documented steps.
- Estimated effort: M
- Next actionable task: Draft the backup inventory for repository, notes, workflow exports, and credentials references.

## 9. Partner Profile

- Objectives: Capture collaboration preferences, role boundaries, and operating principles for project partners.
- Success criteria: Partner profile is documented and referenced by planning workflows.
- Estimated effort: S
- Next actionable task: Create a profile template with role, preferences, responsibilities, and escalation notes.
- Progress: Partner profile template created at docs/PARTNER_PROFILE_TEMPLATE.md

## Production automation roadmap

1. Skills and dependency audit
2. Test foundation
3. Python project configuration
4. Dependency locking
5. CI validation
6. Container templates
7. Security scanning
8. Backup and restore
9. Observability
10. GitHub synchronization
11. Obsidian integration
12. Linear integration
13. n8n deterministic workflows
14. Staging environment
15. Production deployment approval

## Recent updates (autopilot)

- 2026-06-27T06:39:54Z: Wired tools/inventory.py into the CI smoke workflow so the inventory script is exercised in CI; local smoke tests passed.
- 2026-06-27T08:43:43Z: Added a focused pytest (tests/test_inventory_pytest.py) to exercise tools/inventory.collect_files and render_inventory, created with Codex (sandbox: workspace-write). Verification could not be completed here because `pytest` is not installed in this environment; execution and commit are deferred until pytest is available.
