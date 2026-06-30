# Hermes Autonomous Verification, Delegation and Recovery Loop

## Мета

Перебудуй TerraBits Orchestrator так, щоб власник не керував кожним кроком вручну і не перевіряв за Hermes, чи інтеграція реально спрацювала.

Поточна проблема:

- Hermes часто повідомляє `SUCCESS`, коли workflow лише завершився без помилки;
- реальний бізнес-результат не завжди перевіряється;
- owner змушений вручну відкривати GitHub, Linear, Telegram, staging та інші системи;
- Codex, Claude Code, MCP tools і сторонні агенти не завжди викликаються автоматично;
- Hermes зупиняється після створення структури або документації замість перевірки живого результату;
- відсутній жорсткий цикл:
  plan → execute → verify externally → diagnose → delegate → repair → re-test → report.

Потрібно створити автономний verification and delegation loop.

Працюй у feature branch:

```text
feat/autonomous-verification-loop
```

Не змінюй secrets, cloud resources, DNS, firewall, paid subscriptions або production без explicit owner approval.

---

# 1. Основний принцип

Hermes не має права вважати задачу завершеною лише тому, що:

- команда повернула exit code 0;
- GitHub Action має статус success;
- файл створений;
- workflow запущений;
- API відповів 200;
- dry-run пройшов;
- документація написана;
- wrapper існує;
- інтеграція “налаштована”.

Completion дозволений лише після підтвердження зовнішнього результату.

Приклади:

## Linear

Недостатньо:

```text
workflow success
```

Потрібно:

```text
issue реально існує в Linear
identifier отримано
project/team правильні
другий запуск не створив duplicate
```

## Telegram

Недостатньо:

```text
API request 200
```

Потрібно:

```text
message_id отримано
chat_id відповідає environment
delivery recorded
```

## Staging

Недостатньо:

```text
docker compose up завершився
```

Потрібно:

```text
container healthy
HTTPS endpoint відповідає
version правильна
rollback перевірений
```

## Codex

Недостатньо:

```text
wrapper exists
```

Потрібно:

```text
Codex CLI реально викликаний
diff створений
tests пройдені
result artifact збережений
```

## Claude Code

Недостатньо:

```text
review script exists
```

Потрібно:

```text
Claude Code реально викликаний
review artifact існує
verdict отримано
```

---

# 2. Автономний execution loop

Для кожної задачі використовуй обов’язковий цикл:

```text
INTAKE
→ CLASSIFY
→ PLAN
→ DEFINE EVIDENCE
→ SELECT WORKERS
→ EXECUTE
→ VERIFY LOCALLY
→ VERIFY EXTERNALLY
→ DIAGNOSE
→ DELEGATE REPAIR
→ RE-TEST
→ ACCEPT OR BLOCK
→ UPDATE SYSTEMS
→ REPORT OWNER
```

Hermes не може пропускати `VERIFY EXTERNALLY`.

---

# 3. Evidence-first Definition of Done

Перед виконанням кожної задачі створи список evidence.

Формат:

```yaml
definition_of_done:
  - requirement: "Linear issue created"
    evidence_type: "api_query"
    expected: "issue.identifier exists"
  - requirement: "No duplicate on second sync"
    evidence_type: "repeat_run"
    expected: "same issue identifier"
```

Для кожної вимоги зберігай:

- expected result;
- verification method;
- actual result;
- evidence artifact;
- status.

Не використовуй `COMPLETED`, якщо хоча б одна mandatory evidence-вимога не підтверджена.

---

# 4. Worker routing

Створи routing policy.

## Hermes

Використовуй для:

- intake;
- context;
- orchestration;
- planning;
- risk classification;
- evidence design;
- aggregation;
- owner communication.

Hermes не повинен сам виконувати великий coding task, якщо Codex доступний.

## Codex

Автоматично залучай для:

- code;
- tests;
- scripts;
- CI/CD;
- Docker;
- Terraform plan;
- refactoring;
- debugging;
- adapters;
- API clients;
- validation tools;
- repair patches.

Після помилки:

```text
Hermes diagnosis
→ Codex patch
→ Hermes verification
```

## Claude Code

Автоматично залучай для:

- high-risk review;
- security;
- authentication;
- permissions;
- infrastructure;
- rollback;
- database;
- production;
- architecture disagreements;
- second review після двох невдалих Codex attempts.

Claude Code не виконує зміни напряму.

## OpenRouter models

Використовуй різні моделі за ролями:

- orchestration/reasoning;
- cheap validation;
- fallback;
- summarization;
- independent critique.

Не використовуй одну модель для плану, реалізації та acceptance без незалежної перевірки.

## MCP tools / external agents

Автоматично використовуй доступні trusted MCP/tools для:

- GitHub;
- Linear;
- filesystem;
- Obsidian;
- browser/research;
- Cloudflare;
- monitoring;
- documentation;
- database;
- testing.

Не встановлюй нові MCP/tools без security review і approval.

---

# 5. Tool and agent registry

Створи:

```text
config/agent-registry.yaml
config/tool-registry.yaml
schemas/agent-registry.schema.json
schemas/tool-registry.schema.json
```

Для кожного агента:

```yaml
id:
name:
type:
capabilities:
risk_level:
auth_method:
cost_class:
available:
healthcheck:
timeout:
fallback:
allowed_actions:
forbidden_actions:
```

Для кожного tool/MCP:

```yaml
id:
name:
capabilities:
read_access:
write_access:
secret_access:
risk_level:
healthcheck:
fallback:
```

Створи:

```text
tools/agent_router.py
tools/tool_router.py
tools/agent_healthcheck.py
```

---

# 6. Automatic delegation policy

Hermes має сам вирішувати:

- який агент потрібен;
- які tools потрібні;
- чи потрібен reviewer;
- чи потрібен second opinion;
- коли зупинитися;
- коли ескалювати owner.

Приклади:

## Coding task

```text
Hermes plan
→ Codex implementation
→ local tests
→ CI
→ Hermes verifies result
→ Claude review only if risk medium/high
```

## Integration failure

```text
Hermes detects mismatch
→ relevant MCP/API query
→ Codex diagnoses adapter/workflow
→ tests
→ external verification
```

## Research

```text
Hermes
→ research-capable MCP/tool
→ source validation
→ reasoning model
→ optional independent critique
```

## Security

```text
Hermes
→ Codex prepares safe change
→ Claude Code review
→ owner approval
→ execution
→ verification
```

---

# 7. Failure diagnosis and recovery

Створи state machine:

```text
NEW
PLANNED
EXECUTING
VERIFYING
REPAIRING
NEEDS_APPROVAL
BLOCKED
COMPLETED
FAILED
```

При verification failure:

1. Не повідомляй success.
2. Збери evidence.
3. Класифікуй failure:
   - config;
   - auth;
   - code;
   - environment;
   - permission;
   - missing data;
   - external service;
   - owner action.
4. Делегуй відповідному worker.
5. Повтори verification.
6. Максимум 2 automatic repair attempts.
7. Після 2 невдалих спроб:
   - залучи independent reviewer;
   - або створи owner action.

Захисти систему від нескінченних циклів.

---

# 8. External verification adapters

Створи або доповни adapters:

```text
tools/verify_github.py
tools/verify_linear.py
tools/verify_telegram.py
tools/verify_staging.py
tools/verify_obsidian.py
tools/verify_codex.py
tools/verify_claude.py
```

## Linear verification

Має перевіряти:

- team;
- project;
- issue;
- identifier;
- state;
- duplicate count;
- second-run idempotency.

## GitHub verification

Має перевіряти:

- branch;
- commit;
- PR;
- CI;
- required checks;
- merge status;
- workflow conclusion.

## Telegram verification

Має перевіряти:

- API response;
- message_id;
- correct chat;
- timestamp;
- environment.

## Staging verification

Має перевіряти:

- SSH;
- compose status;
- container health;
- HTTPS;
- endpoint;
- version;
- logs;
- rollback target.

## Obsidian verification

Має перевіряти:

- note exists;
- sync commit exists;
- correct project folder;
- no overwrite conflict;
- no secret content.

---

# 9. Integration-specific rules

## Linear

Hermes сам:

1. перевіряє `LINEAR_PROJECT_ID`;
2. створює test issue;
3. читає issue назад;
4. запускає sync вдруге;
5. перевіряє duplicate count;
6. закриває test issue;
7. зберігає report.

Не проси owner вручну дивитися Linear, якщо API доступний.

## GitHub

Hermes сам:

- читає workflow logs;
- перевіряє outputs;
- не покладається лише на green check;
- перевіряє artifacts і actual side effects.

## Telegram

Hermes сам:

- перевіряє delivery response;
- зберігає message ID;
- перевіряє правильний chat mapping.

## Staging

Hermes сам:

- deploy;
- health;
- version;
- logs;
- rollback;
- final state.

Owner потрібен лише для high-risk approval.

---

# 10. Owner interaction policy

Owner не повинен:

- копіювати workflow logs;
- вручну перевіряти Linear;
- вручну перевіряти Telegram delivery;
- вручну перевіряти container health;
- вручну визначати, який агент потрібен;
- вручну вирішувати, чи Codex або Claude Code слід викликати.

Owner має:

- давати задачу;
- надавати approval для high-risk;
- виконувати account-level UI actions, які Hermes не може зробити;
- приймати продуктове рішення.

Кожен owner action має бути мінімальним і конкретним.

---

# 11. Autonomous acceptance report

Для кожної задачі створюй:

```text
artifacts/executions/<task-id>.json
docs/executions/<task-id>.md
```

Обов’язкові поля:

```json
{
  "task_id": "",
  "project_id": "",
  "risk": "",
  "status": "",
  "workers_selected": [],
  "tools_selected": [],
  "definition_of_done": [],
  "local_verification": [],
  "external_verification": [],
  "repair_attempts": [],
  "evidence": [],
  "owner_actions": [],
  "final_verdict": ""
}
```

---

# 12. Autonomous test scenarios

Проведи реальні тести.

## Scenario A: Linear

- створити test issue;
- прочитати назад;
- sync twice;
- no duplicate;
- close issue.

## Scenario B: Codex

- реальний coding task;
- test;
- diff;
- verification.

## Scenario C: Claude Code

- реальний review;
- artifact;
- verdict.

## Scenario D: Telegram

- send test alert;
- record message_id;
- correct chat.

## Scenario E: Staging

- deploy test app;
- verify HTTPS;
- verify version;
- rollback test.

## Scenario F: Multi-agent repair

- навмисно створити безпечний failure;
- Hermes діагностує;
- Codex виправляє;
- Hermes re-verifies;
- Claude review, якщо threshold досягнуто.

---

# 13. Scheduled autonomous checks

Створи:

## Quick check

Кожні 2 години:

- active tasks;
- failed workflows;
- pending verification;
- staging health;
- notification failures;
- blocked owner actions.

## Daily full verification

Раз на добу:

- integrations;
- agents;
- tools;
- auth health;
- stale tasks;
- execution gaps;
- drift;
- duplicate issues;
- failed syncs.

## Weekly optimization

Раз на тиждень:

- model usage;
- agent success rate;
- repair success rate;
- cost;
- latency;
- flaky tests;
- unused tools;
- missing capabilities.

Не виконувати high-risk changes автоматично.

---

# 14. Metrics

Створи:

```text
docs/AUTONOMY_METRICS.md
artifacts/metrics/autonomy.json
```

Метрики:

- tasks completed without owner intervention;
- tasks requiring owner action;
- verification failures;
- repair success rate;
- Codex invocation count;
- Claude Code invocation count;
- MCP/tool invocation count;
- false success count;
- duplicate issue count;
- average task completion time;
- model/API cost.

Головний KPI:

```text
Owner manual verification rate < 10%
```

---

# 15. Safe autonomy boundaries

Hermes може самостійно:

- read-only API checks;
- low-risk code changes;
- tests;
- feature branches;
- PR creation;
- Linear test issue creation;
- Telegram test messages;
- staging health checks;
- dry-runs;
- low-risk repair.

Owner approval потрібен для:

- secrets;
- credential rotation;
- DNS;
- firewall;
- cloud resources;
- production;
- database migration;
- destructive operations;
- paid services;
- public repositories;
- medium/high-risk merge.

---

# 16. Deliverables

Створи або онови:

```text
config/agent-registry.yaml
config/tool-registry.yaml
tools/agent_router.py
tools/tool_router.py
tools/agent_healthcheck.py
tools/verify_github.py
tools/verify_linear.py
tools/verify_telegram.py
tools/verify_staging.py
tools/verify_obsidian.py
tools/verify_codex.py
tools/verify_claude.py
tests/test_autonomous_loop.py
tests/test_agent_routing.py
tests/test_external_verification.py
docs/AUTONOMOUS_ORCHESTRATION_ARCHITECTURE.md
docs/AUTONOMY_POLICY.md
docs/AUTONOMY_METRICS.md
docs/OWNER_INTERACTION_POLICY.md
docs/AUTONOMOUS_VERIFICATION_REPORT.md
```

---

# 17. Git policy

- branch: `feat/autonomous-verification-loop`;
- push лише feature branch;
- low-risk PR можна створити автоматично;
- не merge medium/high-risk без approval;
- clean working tree;
- окремі commits;
- не використовуй compromised credentials.

---

# 18. Final acceptance

Оркестр вважається автономним лише якщо:

- Hermes сам перевіряє зовнішній результат;
- Hermes сам викликає Codex для implementation/repair;
- Hermes сам викликає Claude Code для independent review;
- Hermes сам використовує доступні MCP/tools;
- false success більше не допускається;
- owner не перевіряє Linear/GitHub/Telegram/staging вручну;
- repair loop працює;
- loop protection працює;
- evidence artifacts створюються;
- owner manual verification rate нижче 10%.

---

# 19. Final Telegram report

До 200 слів:

- autonomy verdict;
- real agents used;
- MCP/tools used;
- Linear live verification;
- Telegram live verification;
- staging verification;
- repair loop result;
- owner manual verification rate;
- blockers;
- approvals;
- commit;
- PR.

Не заявляй `AUTONOMOUS` без реальних end-to-end evidence.
