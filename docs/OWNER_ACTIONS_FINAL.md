# Owner Actions — Final

> Last updated: 2026-06-29

## 🔴 Critical (блокують функціональність)

| # | Дія | Де | Час |
|---|-----|-----|-----|
| 1 | **Видалити скомпрометований GitHub PAT** `ghp_7pt...` | GitHub → Settings → Developer settings → Tokens → Delete | 1 хв |
| 2 | **Перевірити LINEAR_PROJECT_ID** в staging secrets | GitHub → IIIH23/earth-pulse-poc → Settings → Environments → staging | 1 хв |
| 3 | **Запустити Linear Sync workflow** | GitHub → Actions → Linear Sync → Run workflow | 1 хв |

## 🟡 Important (покращують функціональність)

| # | Дія | Де | Час |
|---|-----|-----|-----|
| 4 | **Створити Obsidian private repo** `IIIH23/obsidian-pulse-of-earth` | GitHub → New repository → Private | 1 хв |
| 5 | **Встановити Obsidian Git plugin** | Obsidian → Settings → Community plugins → Browse → Git → Install | 3 хв |
| 6 | **Налаштувати Git plugin** | Vault settings → Git → configure repo URL + auto-sync | 5 хв |
| 7 | **Додати STAGING_SSH_KEY** якщо ще не додано | GitHub → staging secrets → Add secret | 1 хв |

## 🟢 Після того як критичне готово

| # | Дія | Де | Час |
|---|-----|-----|-----|
| 8 | **Перевірити Linear issues** | linear.app → Pulse of Earth → Issues | 2 хв |
| 9 | **Перевірити CI status** | GitHub → Actions → останні runs | 1 хв |
| 10 | **Запустити staging deploy** | GitHub → Actions → CI → Run workflow | 1 хв |
| 11 | **Перевірити staging health** | curl https://earthbit.staging.terrabits.org/health | 30 сек |

## Контрольний список

- [ ] Скомпрометований PAT видалено
- [ ] LINEAR_PROJECT_ID додано
- [ ] Linear Sync запущено
- [ ] Obsidian repo створено
- [ ] Obsidian Git plugin налаштовано
- [ ] Staging health check пройдено
