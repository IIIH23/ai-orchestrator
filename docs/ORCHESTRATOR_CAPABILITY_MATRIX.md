# Orchestrator Capability Matrix

> Last updated: 2026-06-29
> Audit branch: audit/orchestrator-capability-fit

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Implemented + Tested + Activated |
| ⚠️ | Implemented but not E2E tested |
| �️ | Documented but not active |
| ❌ | Not implemented |

## A. Unified Intake

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Idea intake via Telegram | ✅ | Hermes receives messages | |
| Text/code review requests | ✅ | Direct chat | |
| File ingestion | ⚠️ | Telegram file API not configured | No auto-download |
| Repository link analysis | ⚠️ | Manual clone + analysis | No auto-fetch |
| Bug report intake | ✅ | Direct chat | |
| Research request | ⚠️ | Web search tool available | No browser tool |
| Product requirement intake | ✅ | Direct chat | |
| Multi-project context switch | ❌ | Single repo context | No isolation |

## B. Discovery & Product Thinking

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Problem statement | ✅ | LLM reasoning | |
| Target user analysis | ✅ | LLM reasoning | |
| Value proposition | ✅ | LLM reasoning | |
| Feasibility analysis | ✅ | LLM reasoning | |
| Risk identification | ✅ | LLM reasoning | |
| MVP scope | ✅ | LLM reasoning | |
| Architecture outline | ✅ | LLM reasoning | |
| Roadmap generation | ✅ | ROADMAP.md exists | |
| Acceptance criteria | ✅ | LLM reasoning | |

## C. Coding & Review

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Codex invocation | ⚠️ | CLI available, not auto-invoked | No structured task handoff |
| Code creation | ⚠️ | Via Codex CLI | No Hermes→Codex bridge |
| Unit test creation | ✅ | test_orchestrator_e2e.py | |
| Integration test creation | ⚠️ | Manual scripts | No auto-generation |
| Diff verification | ⚠️ | Manual review | No automated check |
| Claude Code review | ⚠️ | skill available, not invoked | No automatic high-risk trigger |
| PR creation | ⚠️ | gh CLI available | No auto-PR from changes |
| PR comment/update | ⚠️ | gh CLI available | Not automated |

## D. Research

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Web search | ⚠️ | Basic web_search tool | No deep research |
| Official documentation fetch | ⚠️ | curl/web_fetch | No structured API |
| Source citation | ✅ | Manual LLM | |
| Research notes storage | ✅ | Can write to docs/ | |
| Multi-source comparison | ✅ | LLM capability | |

## E. Knowledge & Memory

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| ADR creation | ✅ | Can write ADRs | |
| Decision log | ⚠️ | DECISIONS.md exists | Not auto-updated |
| Searchable history | ⚠️ | Session search | No global index |
| Obsidian bridge | � NOT ACTIVE | Decision documented | No private Git repo, no plugin |
| Long-term project memory | ✅ | Memory tool works | |
| Cross-task context reuse | ⚠️ | Session-based | No persistent KB |

## F. Multi-Project Orchestration

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Separate project IDs | ❌ | Single repo | No project registry |
| Separate repositories | ⚠️ | клон/manual | No auto-create |
| Separate Linear projects | ⚠️ | Via API | No project registry |
| Separate Obsidian folders | � | No bridge | |
| Separate execution records | ✅ | JSON per task | |
| Separate budgets | ❌ | No budget tracking | |
| Context isolation | ❌ | Single Hermes context | No profile switching |

## G. CI/CD

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Lint stage | ✅ | ci.yml | |
| Test stage | ✅ | ci.yml | |
| Security scan (Trivy) | ✅ | ci.yml | |
| Docker build | ⚠️ | Workflow exists | Action version issue |
| SBOM generation | ⚠️ | anchore/sbom-action | Not tested |
| Cosign signing | ⚠️ | sigstore action | Not tested |
| GHCR push | ⚠️ | docker/build-push | Not working yet |
| Auto deploy to staging | ⚠️ | appleboy/ssh-action | Not tested |

## H. Staging

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Docker running | ✅ | Smoke test | |
| UFW active | ✅ | Smoke test | |
| Fail2ban active | ✅ | Smoke test | |
| Deploy user SSH | ✅ | Smoke test | |
| Automated deploy | ❌ | No app deployed | |
| Health check endpoint | ❌ | No app deployed | |
| Caddy reverse proxy | ❌ | Not configured | |
| HTTPS | ❌ | Not configured | |
| Rollback automation | ⚠️ | rollback.sh script | Not tested with real app |

## I. Notifications

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Telegram delivery | ✅ | Bot configured | |
| GitHub PR comment | ⚠️ | gh CLI available | Not automated |
| Linear update | ⚠️ | API configured | Not automated |
| Retry on failure | ❌ | No retry logic | |
| Deduplication | ⚠️ | Some checks | Not comprehensive |

## J. Security

| Capability | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Secrets in GitHub Secrets | ✅ | All secrets externalized | |
| Fork PR safety | ⚠️ | dependency-review-action | Only on PR |
| Third-party action pinning | ⚠️ | Version tags only | Not pinned to SHA |
| Shell injection prevention | ⚠️ | set -euo pipefail | Not comprehensive |
| SSH key permissions | ✅ | 600 on server | |
| Docker socket isolation | N/A | No DinD | |
| Rollback safety | ✅ | rollback.sh | |

## K. Knowledge Tools

| Tool | Status | Gap |
|------|--------|-----|
| Obsidian sync | 🔴 NOT ACTIVE | No bridge |
| NotebookLM | ❌ | Not integrated |
| Linear | ⚠️ API key only | No real sync yet |
| Sentry | ❌ | Not installed |
| Prometheus/Grafana | ❌ | Excluded by Storage | ❌ | Not created |

## Summary

| Category | Score | Status |
|----------|-------|--------|
| Discovery & Planning | 5/5 | ✅ |
| Intake | 3/5 | ⚠️ |
| Coding & Review | 2/5 | ⚠️ |
| Knowledge & Memory | 2/5 | ⚠️ |
| CI/CD | 3/5 | ⚠️ |
| Staging | 2/5 | ⚠️ |
| Multi-project | 1/5 | ❌ |
| Research | 3/5 | ⚠️ |
| Notifications | 2/5 | ⚠️ |
| Security | 3/5 | ⚠️ |

**Overall: FIT_WITH_LIMITATIONS** — core reasoning works, but coding delegation, knowledge loop, multi-project isolation, and full E2E deployment need activation.

---

## Critical Gaps (P0/P1)

1. **P0: Obsidian bridge not active** — knowledge loop broken
2. **P0: Multi-project isolation** — cannot safely manage multiple projects
3. **P1: Real Codex delegation bridge** — Codex not auto-invoked
4. **P1: Real Claude Code review** — not triggered for high-risk tasks
5. **P1: Full E2E deployment** — no real app deployed to staging
6. **P1: Research capability** — no browser tool in sandbox

## Owner Actions for Gaps

| Gap | Action | Effort |
|-----|--------|--------|
| Obsidian bridge | Create private Git repo + install plugin | 15 хв |
| Multi-project | Configure Hermes profiles | 30 хв |
| Codex bridge | Define structured handoff protocol | 1 год |
| Claude Review | Test interactive Claude review | 1 год |
| E2E deploy | Create minimal app + Caddy + deploy | 2 год |
| Research | Add research provider or document limitation | 30 хв |
