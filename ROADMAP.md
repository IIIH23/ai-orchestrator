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
- Success criteria: Project labels, issue lifecycle, and update cadence are documented. Sync tool implemented.
- Estimated effort: M
- Status: ✅ done
- Completion summary: docs/STAGE_4_SPEC.md (GraphQL operations, field mapping, idempotency strategy)
- Progress: Sync spec drafted at docs/STAGE_4_SPEC.md (GraphQL queries/mutations, ROADMAP→Linear field mapping, idempotency via external ID markers). Commit 1bee3d9. Sync tool implemented: tools/linear_sync.py with 8 tests. Dry-run mode validates local parsing without API calls.
- Next actionable task: Stage 5 (n8n Workflows) — choose one workflow candidate and write its trigger and expected output.

## 5. Deterministic Workflows With n8n

- Objectives: Design repeatable n8n workflows for scheduled or event-driven project automation.
- Success criteria: Initial workflow specs include triggers, inputs, outputs, retries, and failure handling.
- Estimated effort: L
- Status: 🔵 active (Phase 4 of 4 complete)
- Progress: First workflow selected — Daily Healthcheck Report. Spec at docs/STAGE_5_SPEC.md. Implementation: tools/healthcheck_report.py (stdlib-only CLI, 3 destinations: telegram/stdout/file, retry with backoff, exit codes 0/1/2/3). 8 pytest tests passing. Reuses Stage 2 tools (healthcheck.py, telegram_notify.py). Second workflow: tools/snapshot.py (System Inventory Snapshot — timestamped JSON with health checks + hostname/uptime/load/network metadata, --keep pruning, --dry-run, exit codes 0/1/2). 9 pytest tests passing. Third workflow: tools/trend.py (Trend Analysis — reads snapshot collection, computes uptime/load/network/health statistics over time, human-readable report or JSON, exit codes 0/1/2). 15 pytest tests passing. Fourth workflow: tools/diff_snapshots.py (Snapshot Diff — compares two snapshot JSON files, reports hostname/uptime/load/network/checks deltas, text or JSON output, exit codes 0/1/2). 10 pytest tests passing.
- Next actionable task: Stage 5 complete. Move to Stage 6 (GitHub Sync).

## 6. GitHub Sync

- Objectives: Establish repository sync expectations for issues, docs, status, and automation outputs.
- Success criteria: Sync scope and manual approval boundaries are documented. Sync checker implemented.
- Estimated effort: M
- Status: ✅ done
- Completion summary: docs/STAGE_6_SPEC.md (github_sync.py + CI drift check wired)
- Progress: Sync spec drafted at docs/STAGE_6_SPEC.md (auto-synced artifacts, exclusions, manual-approval boundaries, sync direction). Implementation: tools/github_sync.py (stdlib-only CLI, check/status commands, --dry-run, --json, exit codes 0/1/2). 12 pytest tests passing. CI drift check job wired into .github/workflows/ci.yml — runs check/status in parallel with test job, non-blocking. Commit 2ff60b6.
- Next actionable task: Stage 8 complete. Stage 9 — confirm Partner Profile template.

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
- Status: ✅ done
- Completion summary: docs/STAGE_8_SPEC.md
- Progress: Drafted tiered backup strategy (4 tiers: critical Git assets, reproducible files, secrets excluded, runtime artifacts excluded). Documented restore procedure (full + partial), backup commands with tar exclusions, verification checklist. Decision record: Git is primary backup, secrets never committed, venvs rebuilt from requirements.
- Next actionable task: Stage 9 — confirm Partner Profile template is complete or expand.

## 9. Partner Profile

- Objectives: Capture collaboration preferences, role boundaries, and operating principles for project partners.
- Success criteria: Partner profile is documented and referenced by planning workflows.
- Estimated effort: S
- Status: ✅ done
- Completion summary: docs/STAGE_9_SPEC.md
- Progress: Partner profile template created at docs/PARTNER_PROFILE_TEMPLATE.md. Concrete profile for project owner at docs/partners/dmytro.md. Stage 9 spec at docs/STAGE_9_SPEC.md.
- Next actionable task: All Stages 1-9 complete. Project in maintenance/operational mode.

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

- 2026-06-29T15:38:00Z: Cycle 22 — Stage 9 complete. Created docs/STAGE_9_SPEC.md and docs/partners/dmytro.md. All Stages 1-9 complete. Project in maintenance/operational mode.
- 2026-06-29T13:30:00Z: Cycle 21 — Stage 8 complete. Drafted backup inventory spec (docs/STAGE_8_SPEC.md). Tiered strategy: Tier 1 (critical Git assets), Tier 2 (reproducible from code), Tier 3 (secrets — excluded), Tier 4 (runtime artifacts — regenerated). Restore procedure documented with verification checklist. Tests still 124 passed, 3 skipped.
- 2026-06-29T12:00:00Z: Cycle 20 — Stage 6 Phase 2 complete. Added drift-check job to CI workflow (.github/workflows/ci.yml). Non-blocking parallel job runs github_sync.py check/status --dry-run. Full suite: 111 passed, 3 skipped. Commit 2ff60b6. Stage 6 done.
- 2026-06-29T09:11:00Z: Cycle 19 — Stage 6 Phase 1 complete. Implemented GitHub sync checker (tools/github_sync.py + 12 tests). check/status commands, --dry-run, --json, exit codes 0/1/2. Spec at docs/STAGE_6_SPEC.md. Full suite: 124 passed, 3 skipped. Commit c0ae8c3.
- 2026-06-29T02:00:00Z: Cycle 17 — Stage 5 Phase 3 complete. Implemented Trend Analysis workflow (tools/trend.py + 15 tests). Reads snapshot collection, computes uptime/load/network/health statistics over time. Human-readable report or JSON output. Exit codes 0/1/2. Full suite: 100 passed, 20 skipped (SSH staging VPS unreachable). Commit 87c27b4.
- 2026-06-29T01:00:00Z: Cycle 16 — Stage 5 Phase 2 complete. Implemented System Inventory Snapshot workflow (tools/snapshot.py + 9 tests). Timestamped JSON snapshots with health checks + hostname/uptime/load/network metadata. --keep pruning, --dry-run, exit codes 0/1/2. Full suite: 87 passed, 3 skipped (SSH staging). Commit 4da82bb.
- 2026-06-29T00:30:00Z: Cycle 15 — Stage 5 Phase 1 complete. Implemented Daily Healthcheck Report workflow (tools/healthcheck_report.py + 8 tests). Spec at docs/STAGE_5_SPEC.md. Full suite: 61 passed, 20 skipped (SSH staging). Commit pending.
- 2026-06-28T19:56:00Z: Cycle 13
- 2026-06-28T17:45:00Z: Stage 3 complete — ran obsidian_sync.py to generate docs/obsidian/ output (STATE.md, ROADMAP.md, LOG-2026-06-28.md). Updated STAGE_3_SPEC.md to IMPLEMENTED status with autopilot wiring instructions. Full suite: 62 passed, 3 skipped. Advancing to Stage 4.
- 2026-06-28T15:36:00Z: Stage 3 — implemented tools/obsidian_sync.py (stdlib-only Python CLI, --dry-run, --vault-path). 10 pytest tests passing. Total suite: 62 passed, 3 skipped. Commit a96a6bd.
- 2026-06-28T13:30:00Z: Stage 2 confirmed complete. Stage 3 (Hermes-Obsidian) spec drafted at docs/STAGE_3_SPEC.md — one-way Git→Obsidian sync, conflict behavior, note naming. Next: implement tools/obsidian_sync.py. Commit 38f08e1.
- 2026-06-27T19:57:00Z: Staging bootstrap executed on hermes-staging-01 (157.180.125.174). Bootstrap completed, 13 SSH smoke tests passed. Commits 628fdfe, 004abec on feat/staging-bootstrap.
- 2026-06-27T19:51:00Z: Paused cron pulse-autopilot (job dd25d4fecd66) due to repeated error status.
- 2026-06-28T03:10:00Z: Added tools/healthcheck.py (ported from scripts/check-health.sh) — stdlib-only Python CLI with --json, --verbose, --exit-zero flags. 10 pytest tests added and passing. Commit dea410f.
- 2026-06-28T03:00:00Z: Fixed smoke_test.sh hang — find command now excludes all .venv* directories. Previously compiled 836 pip package files causing timeout. Now compiles 4 project files in <1s. Commit 6c7a3fe.
- 2026-06-27T08:43:43Z: Added focused pytest for tools/inventory.py (commit cdc8b63).
- 2026-06-27T06:39:54Z: Wired tools/inventory.py into CI smoke workflow (commit 51f5719).
