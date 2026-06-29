# Owner Actions — Final

> Last updated: 2026-06-29

## 🔴 Critical

| # | Дія | Де | Час |
|---|-----|-----|-----|
| 1 | Видалити скомпрометований PAT `ghp_7pt...` | GitHub → Settings → Tokens → Delete | 1 хв |
| 2 | Видалити скомпрометований Linear API Key (old) | Linear → Settings → API → Delete | 1 хв |
| 3 | Перевірити LINEAR_PROJECT_ID в staging secrets | GitHub → Environments → staging | 1 хв |

## � Important

| # | Дія | Де | Час |
|---|-----|-----|-----|
| 4 | Перевірити Codex CLI auth | Run `codex auth status` | 1 хв |
| 5 | Перевірити Claude Code auth | Run `claude auth status` | 1 хв |
| 6 | Створити Obsidian private repo | GitHub → New repo `IIIH23/obsidian-pulse-of-earth` | 1 хв |
| 7 | Встановити Obsidian Git plugin | Obsidian → Community plugins → Git | 3 хв |
| 8 | Запустити Linear Sync workflow | GitHub → Actions → Linear Sync → Run | 1 хв |
| 9 | Merge PR `feat/orchestrator-acceptance-subscription-audit` | GitHub → Pull requests | 2 хв |

## 🟢 After critical is done

| # | Дія | Де | Час |
|---|-----|-----|-----|
| 10 | Запустити CI (verify test + security pass) | GitHub → Actions → CI → Run | 1 хв |
| 11 | Перевірити staging health | `ssh deploy@157.180.125.174 'docker ps'` | 1 хв |
| 12 | Перевірити staging domain | `https://earthbit.staging.terrabits.org` | 30 сек |

## Контрольний список

- [ ] Скомпрометований PAT видалено
- [ ] Скомпрометований Linear key відкликано
- [ ] Codex auth status verified
- [ ] Claude Code auth status verified
- [ ] Linear Sync запущено
- [ ] E2E test пройдено
- [ ] PR merg

---

**70% завершення. Далі: staging deploy, Obsidian setup, production hardening.**
