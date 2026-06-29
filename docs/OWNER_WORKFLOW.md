# Owner Workflow

> Last updated: 2026-06-29

## Як надіслати ідею

**Telegram → TerraBits Infra Bot:**
```
New idea: <one sentence>

Problem: <what problem?>
Target user: <who benefits?>
Value: <what value?>
```

Або просто пишіть — Hermes розпізнає intent.

**Result:** Discovery, feasibility, MVP plan → Telegram summary (до 200 слів)

## Як надіслати код

**Telegram:**
```
Review this code:
[paste code]
```

**Result:** Code analysis, suggestions, опціонально — Codex refactor

## Як створити новий проєкт

**Telegram:**
```
New project: <name>
Description: <what it does>
```

**Result:** Hermes створює:
- Private GitHub repo (needs approval)
- Linear project
- Obsidian folder
- Staging config

## Як попросити research

**Telegram:**
```
Research: <topic>
Sources: <preferred sources?>
```

**Result:** Research note у docs/research/, citations, product recommendation

## Як затвердити high-risk дію

1. надішліть Telegram команду з  "SECURITY CHANGE"
2. Опишіть exact дію, необхідність та rollback
3. Claude Code review поверне verdict:
   - APPROVED → виконується
   - APPROVED WITH CHANGES → виконується з обмовками
   - BLOCKED  → не виконується

## Як переглянути статус

**Вариант 1:** Session search: `hermes session list`
**Вариант 2:** GitHub → IIIH23/earth-pulse-poc → Actions
**Вариант 3:** Read `docs/ORCHESTRATOR_STATUS.md`

## Як отримати звіт

**Telegram:** `Report` або `Status`

**Result:** Останні задачі, gaps, commits, staging health, Telegram summary

## Як знайти PR

GitHub → Pull Requests → Filter by author `Hermes`

## Як знайти Linear task

Linear → Pulse of Earth → Issues

## Як відновити коніекст

**Telegram:** `нагадай про <topic>`

**Result:** Hermes шукає в session history + memory, підсумовує

## Як зупинити autopilot

```bash
hermes cron pause pulse-autopilot
```

## Як перевірити витрати

**Ask Hermes:** `report costs`

**Result:** Поточні відомі витрати + рекомендації

---

## Telegram Commands

| Command | Action |
|---------|--------|
| Idea: ... | Discovery flow |
| Code: ... | Code analysis |
| Research: ... | Research + notes |
| Build: ... | Deploy request |
| Report | Status summary |
| Stop | Pause autopilot |
| Resume | Resume autopilot |
| Approve <id> | Approve high-risk action |
| Deny <id> | Deny high-risk action |
