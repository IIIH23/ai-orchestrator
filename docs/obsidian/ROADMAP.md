# Pulse of Earth Roadmap

Pulse of Earth is a research and software project for collecting, processing, analyzing, and visualizing Earth-related data.

## 1. Audit

- Objectives: Review repository structure, current assets, assumptions, and missing project controls.
- Success criteria: Inventory exists, gaps are ranked, and immediate risks are visible.
- Estimated effort: S
- Status: ✅ done
- Progress: Created audit/FILE_INVENTORY.md (commit 6ec83a1). Smoke tests and CI workflow skeleton added (commits 51f5719, cdc8b63). VPS bootstrap automation added with 13 SSH smoke tests — all passed (commit 004abec).
- Next actionable task: Stage 2 — identify first logic source to port and record its expected inputs and outputs.

## 2. Port Logic

- Objectives: Move useful existing logic into the repository with clear ownership and minimal dependencies.
- Success criteria: Core logic runs locally and has a documented entry point.
- Estimated effort: M
- Status: ✅ done
- Completion summary: docs/STAGE_2_COMPLETION.md
- Progress: Ported 4 shell scripts to Python modules: tools/inventory.py, tools/healthcheck.py, tools/telegram_notify.py, tools/rollback.py. All 4 remaining shell scripts now delegate to Python backends. 52 tests passing, 3 skipped. VPS provisioning scripts (bootstrap-staging.sh, lockdown-staging-ssh.sh, verify-staging.sh, verify-staging-ssh.sh) remain as shell by design — they are infrastructure provisioning tools, not application logic.
- Next actionable task: Stage 2 is complete. Move to Stage 3 (Hermes-Obsidian).

## 3. Hermes-Obsidian

- Objectives: Define how Hermes project memory syncs with Obsidian notes.
- Success criteria: Note structure, sync direction, and conflict behavior are documented. Sync tool implemented.
- Estimated effort: M
- Status: ✅ done
- Completion summary: docs/STAGE_3_SPEC.md (IMPLEMENTED)
- Progress: Sync spec drafted at docs/STAGE_3_SPEC.md (one-way Git→Obsidian, naming convention, conflict behavior). Commit 38f08e1. Sync tool implemented: tools/obsidian_sync.py with 10 tests. Commit a96a6bd. docs/obsidian/ output generated (STATE.md, ROADMAP.md, LOG-2026-06-28.md). Autopilot wiring documented: run `python3 tools/obsidian_sync.py` after each state update before commit.
- Next actionable task: Stage 4 (Hermes-Linear) — draft Linear issue fields needed for Pulse of Earth work.

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
- Status: ✅ done (staging)
- Progress: Added tests/test_staging_smoke.py with 13 SSH smoke tests against hermes-staging-01 — all passed (commit 004abec). Added tests/test_inventory_pytest.py for inventory tool (commit cdc8b63). Repository smoke test (tests/smoke_test.sh) validates required files and Python compilation.
- Next actionable task: Add integration tests for ported logic as stage 2 progresses.

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
## 14. Staging Environment

- Objectives: Bootstrap hermes-staging-01 (Ubuntu 26.04 LTS) with Docker, UFW, Fail2ban, swap, deploy user.
- Success criteria: Bootstrap script runs idempotently, all 13 smoke tests pass, services active.
- Estimated effort: M
- Status: ✅ done
- Progress: Created scripts/bootstrap-staging.sh and scripts/verify-staging.sh (commit 628fdfe). Executed bootstrap on VPS 157.180.125.174 — Docker 29.6.1, UFW (22/80/443), Fail2ban, 2GB swap, deploy user, project dirs all provisioned. 13 SSH smoke tests passed (commit 004abec). Report at docs/STAGING_BOOTSTRAP_REPORT.md.
- Next actionable task: Verify deploy user SSH access with dedicated key before disabling root SSH (policy #9).
15. Production deployment approval

## Recent updates (autopilot)

- 2026-06-28T17:45:00Z: Stage 3 complete — ran obsidian_sync.py to generate docs/obsidian/ output (STATE.md, ROADMAP.md, LOG-2026-06-28.md). Updated STAGE_3_SPEC.md to IMPLEMENTED status with autopilot wiring instructions. Full suite: 62 passed, 3 skipped. Advancing to Stage 4.
- 2026-06-28T15:36:00Z: Stage 3 — implemented tools/obsidian_sync.py (stdlib-only Python CLI, --dry-run, --vault-path). 10 pytest tests passing. Total suite: 62 passed, 3 skipped. Commit a96a6bd.
- 2026-06-28T13:30:00Z: Stage 2 confirmed complete. Stage 3 (Hermes-Obsidian) spec drafted at docs/STAGE_3_SPEC.md — one-way Git→Obsidian sync, conflict behavior, note naming. Next: implement tools/obsidian_sync.py. Commit 38f08e1.
- 2026-06-27T19:57:00Z: Staging bootstrap executed on hermes-staging-01 (157.180.125.174). Bootstrap completed, 13 SSH smoke tests passed. Commits 628fdfe, 004abec on feat/staging-bootstrap.
- 2026-06-27T19:51:00Z: Paused cron pulse-autopilot (job dd25d4fecd66) due to repeated error status.
- 2026-06-28T03:10:00Z: Added tools/healthcheck.py (ported from scripts/check-health.sh) — stdlib-only Python CLI with --json, --verbose, --exit-zero flags. 10 pytest tests added and passing. Commit dea410f.
- 2026-06-28T03:00:00Z: Fixed smoke_test.sh hang — find command now excludes all .venv* directories. Previously compiled 836 pip package files causing timeout. Now compiles 4 project files in <1s. Commit 6c7a3fe.
- 2026-06-27T08:43:43Z: Added focused pytest for tools/inventory.py (commit cdc8b63).
- 2026-06-27T06:39:54Z: Wired tools/inventory.py into CI smoke workflow (commit 51f5719).
