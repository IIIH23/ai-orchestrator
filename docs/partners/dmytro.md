# Partner Profile — Dmytro

- **Name:** Dmytro
- **Role(s):** Project owner, Hermes operator, autopilot designer
- **Responsibilities:**
  - Define project direction, priorities, and acceptance criteria
  - Configure and maintain Hermes Agent (cron jobs, skills, cost policy)
  - Review autopilot outputs and approve commits/pushes
  - Own secrets, gateway config, and deployment credentials
- **Availability / Timezone:** EEST (UTC+3)
- **Communication preferences:**
  - Frequency: async, as-needed
  - Channels: Hermes chat, GitHub
  - Escalation path: N/A (single point of contact for project decisions)
- **Access constraints:**
  - Full access to repository and documentation
  - Authorized to configure Hermes cron, skills, and inference providers
  - Only human authorized to push/deploy
- **Security & privacy notes:**
  - No PII stored in repo
  - Secrets managed via Hermes auth or environment, never committed
- **Onboarding checklist:**
  - [x] Read ROADMAP.md and AGENTS.md
  - [x] Review cost-policy and codex skills
  - [x] Verify Hermes cron jobs and autopilot state
- **Offboarding checklist:**
  - [ ] Revoke Hermes credentials
  - [ ] Transfer repository ownership
  - [ ] Archive decision records

## Operating principles

1. **One small completable task per cycle** — autopilot advances incrementally.
2. **Direct implementation for doc-only changes** — Codex delegation only for substantial code.
3. **Test after every change** — canonical test command is `python3 -m pytest tests/ -q`.
4. **Local commit, no push** — autopilot never pushes without explicit approval.
5. **State files are source of truth** — ROADMAP, AUTOPILOT_STATE, AUTOPILOT_LOG must reflect reality after each cycle.
6. **Stale cron prompts** — always verify against current state before acting.
