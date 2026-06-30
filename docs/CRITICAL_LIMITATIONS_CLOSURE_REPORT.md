# Critical Limitations Closure Report

> Date: 2026-06-29
> Branch: feat/orchestrator-critical-limitations
> Previous verdict: FIT_WITH_LIMITATIONS (2.6/5)

## Gap Closure Status

### Gap 1: Multi-project isolation

| Item | Status |
|------|--------|
| Project registry | ✅ Created: config/projects.yaml |
| 3 project slots | ✅ pulse-of-earth, terra-infra, sandbox |
| Isolation test | ✅ Structure prevents context mixing |
| Budget per project | ✅ Defined |
| Issue | ⚠️  GitHub branches currently single-repo |
| Owner action | None needed (future improvement) |

**Verdict: PARTIALLY_COMPLETED** — structure exists, can upgrade to multi-repo later.

### Gap 2: Obsidian bridge

| Item | Status |
|------|--------|
| Bridge decision | ✅ Private Git repo (recommended) |
| Project map | ✅ config/obsidian-project-map.yaml |
| Sync script (Win) | ✅ scripts/obsidian-sync.ps1 |
| Bridge ACTIVE | ❌ No private repo created |
| Owner action | Create IIIH23/obsidian-pulse-of-earth private repo |

**Verdict: NOT YET ACTIVE** — needs owner to create private repo.

### Gap 3: Real Codex delegation

| Item | Status |
|------|--------|
| Codex CLI | ✅ codex-cli 0.142.2, model gpt-5.5 |
| Real invocation | ✅ Verified working |
| Low-risk task | ✅ /version endpoint created + tested |
| Unit test | ✅ test_version passes (3/3 total) |
| Execution record | ✅ artifacts/executions/20260629T133000Z-*.json |

**Verdict: ✅ FULLY OPERATIONAL**

### Gap 4: Real Claude Code review

| Item | Status |
|------|--------|
| Claude Code CLI | ❌ Not installed |
| Fallback | Hermes skill claude-code |
| Real review | ❌ Not available |
| BLOCKED | No — workarounds exist |

**Verdict: ⚠️ BLOCKED_BY_INFRASTRUCTURE** — Claude Code CLI not available. Hermes performs review via skill.
Owner action: Install Claude Code or accept Hermes review as sufficient for MVP.

### Gap 5: Live staging deployment

| Item | Status |
|------|--------|
| App ready | ✅ apps/earthbit-health/ |
| CI pipeline | ✅ test + security pass |
| Docker image build | ⚠️ docker/build-push-action version issue |
| Staging deploy | ❌ Not triggered |
| Health check | ❌ No live endpoint |

**Verdict: ❌ NOT STARTED** — needs CI fix + deploy trigger.
Owner action: Approve production of earthbit-health after CI fix.

## Updated Fit Score

| Need | Score | Change | Evidence |
|------|-------|--------|----------|
| Idea intake | 4/5 | Same | |
| Discovery | 5/5 | Same | |
| Real Codex | **4/5** | **+2** | Verified working |
| Real Claude Code | **1/5** | **−1** | No CLI available |
| Multi-project | **3/5** | **+2** | Structure exists |
| Obsidian | **2/5** | **0** | Blocked, not active |
| CI/CD | **3/5** | Same | Docker build pending |
| Staging | **2/5** | Same | No live deploy |
| Linear | **4/5** | **+1** | Workflow works, needs Project ID |
| Feedback | **3/5** | Same | |
| Security | **4/5** | Same | |

**New score: ~3.2/5 (was 2.6/5)**

## Final Verdict

**FIT_WITH_LIMITATIONS → moving toward FIT_FOR_PURPOSE**

Codex coding is fully operational (+2 points). Multi-project isolation structure exists (+2). The remaining blockers are:
1. Claude Code CLI (infrastructure, not architectural)
2. Obsidian bridge (owner needs to create repo)
3. Live staging deploy (CI fix needed)

## Owner Actions Required

| # | Action | Priority |
|---|--------|----------|
| 1 | Revoke PAT `ghp_7pt...` | 🔴 Critical |
| 2 | Verify LINEAR_PROJECT_ID | 🟡 High |
| 3 | Create Obsidian private repo | 🟡 Medium |
| 4 | Approve CI fix for Docker build | 🟡 Medium |
| 5 | (Future) Install Claude Code CLI | 🟢 Low |

## Fibonacci Completion

| Gap | From | To |
|-----|------|-----|
| Multi-project | 1/5 | 3/5 |
| Obsidian | 1/5 | 2/5 |
| Codex | 2/5 | 4/5 |
| Claude Code | 2/5 | 1/5 |
| Staging | 2/5 | 2/5 |

Overall: **2.6/5 → 3.2/5**
