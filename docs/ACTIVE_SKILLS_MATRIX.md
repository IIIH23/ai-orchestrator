# Active Skills Matrix

> Last updated: 2026-06-29 17:03 EEST

## Core Skills

| Skill | Category | Status | Trigger | Tested | Needed |
|-------|----------|--------|---------|--------|--------|
| claude-code | autonomous-ai-agents | ✅ enabled | high-risk review | No | Yes |
| codex | autonomous-ai-agents | ✅ enabled | coding tasks | No | Yes |
| hermes-agent | autonomous-ai-agents | ✅ enabled | self-config | No | Yes |
| opencode | autonomous-ai-agents | ✅ enabled | alternative coding | No | Optional |

## Cost & Orchestration

| Skill | Category | Status | Trigger | Tested | Needed |
|-------|----------|--------|---------|--------|--------|
| cost-policy | orchestration | ✅ enabled | lean-dev bundle | Yes | Yes |

## Development

| Skill | Category | Status | Trigger | Tested | Needed |
|-------|----------|--------|---------|--------|--------|
| test-driven-development | software-development | � unknown | TDD workflows | No | Yes |
| python-testing-patterns | software-development | � unknown | Python tests | No | Yes |
| systematic-debugging | software-development | � unknown | Debug flow | No | Yes |
| requesting-code-review | software-development | ❓ unknown | PR review | No | Yes |
| improve-codebase-architecture | software-development | ❓ unknown | Architecture | No | Optional |

## DevOps

| Skill | Category | Status | Trigger | Tested | Needed |
|-------|----------|--------|---------|--------|--------|
| autopilot-verification | devops | ✅ enabled | Verification | No | Yes |
| github-pr-workflow | github | ❓ unknown | PR lifecycle | No | Yes |
| github-repo-management | github | ❓ unknown | Repo setup | No | Optional |
| github-auth | github | ❓ unknown | Auth setup | No | Optional |
| github-issues | github | ❓ unknown | Issue management | No | Optional |

## Research

| Skill | Category | Status | Trigger | Tested | Needed |
|-------|----------|--------|---------|--------|--------|
| arxiv | research | � unknown | Papers | No | Yes |
| blogwatcher | research | ❓ unknown | Blog monitoring | No | Optional |
| llm-wiki | research | ❓ unknown | LLM research | No | Optional |

## Unknown Status

Skills listed in completion prompt but not verified:
- brainstorming
- architecture-patterns
- documentation-writer
- executing-plans
- find-skills
- git-commit
- github-actions-docs
- playwright-best-practices
- python-performance-optimization
- skill-creator
- verification-before-completion
- security-audit

## Recommended Activations

1. **codex** → auto-activate for coding tasks
2. **claude-code** → auto-activate for high-risk files (SSH, firewall, secrets)
3. **cost-policy** → already active, keep for all cycles
4. **autopilot-verification** → activate after each deployment
