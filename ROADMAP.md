# Pulse of Earth Roadmap

Pulse of Earth is a research and software project for collecting, processing, analyzing, and visualizing Earth-related data.

## 1. Audit

- Objectives: Review repository structure, current assets, assumptions, and missing project controls.
- Success criteria: Inventory exists, gaps are ranked, and immediate risks are visible.
- Estimated effort: S
- Progress: Created audit/FILE_INVENTORY.md (commit 6ec83a1)
- Next actionable task: Analyze inventory and rank gaps.

## 2. Port Logic

- Objectives: Move useful existing logic into the repository with clear ownership and minimal dependencies.
- Success criteria: Core logic runs locally and has a documented entry point.
- Estimated effort: M
- Next actionable task: Identify the first logic source to port and record its expected inputs and outputs.

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

## 7. Tests & Smoke-Tests

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
