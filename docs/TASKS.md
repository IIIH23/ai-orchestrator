# Робочий список завдань

> Оновлено: 2026-06-28
> Решта завдань, які потребують вашої участї (ті, що вже зроблено, відмічені ✅)

---

## � Критичні (блокують CI/CD pipeline)

| # | ✅ | Дія | Де зробити | Час |
|---|-----|-----|------------|-----|
| 1 | ✅ | GitHub репозиторій створений, код запушений | github.com/IIIH23/earth-pulse-poc | - |
| 2 | ✅ | Branch Protection налаштований | GitHub API | - |
| 3 | ✅ | Staging Environment створений | GitHub API | - |
| 4 | ✅ | STAGING_HOST, STAGING_USER додані | GitHub API | - |
| 5 | � | Зазначте STAGING_SSH_KEY у секретах staging environment | GitHub → Secrets | 1 хв |
| 6 | ☑️ | Cloudflare DNS A-запис створений (вручну) | dash.cloudflare.com | - |

### Що залишилось критичним:

**5. Зазначте STAGING_SSH_KEY у секретах staging environment**

Без цього CI/CD не зможе підключитись до staging VPS для deploy.

GitHub → IIIH23/earth-pulse-poc → Settings → Environments  staging → Add secret

| Назва | Значення |
|-------|----------|
| STAGING_SSH_KEY | Приватний deploy key (починається з `-----BEGIN OPENSSH PRIVATE KEY-----`) |

Якщо ви не хочете додавати SSH ключ в GitHub secrets — я можу згенерувати нову пару і додати публічну частину на staging через SSH.

---

## � Важливі

| # | Дія | Де зробити | Час |
|---|-----|------------|-----|
| 7 | Створити Cloudflare API Token з правами DNS Edit | dash.cloudflare.com → My Profile → API Tokens | 2 хв |
| 8 | Створити Linear API Key та надати Hermes | linear.app → Settings → API → Personal API tokens → Create | 2 хв |
| 9 | Надати Telegram Bot Token + Staging Chat ID + Production Chat ID | Попросите у власника бота | 1 хв |
| 10 | Вказати шлях до Obsidian Vault | Мені для синхронізації | 30 сек |
| 11 | Видалити старий Cloudflare API Token з правами READ-ONLY | dash.cloudflare.com → My Profile → API Tokens | 1 хв |
| 12 | Змінити тип Cloudflare Token в налаштуваннях | Cloudflare → DNS → запис → перевірти що він "не proxied" (DNS only) | 1 хв |

---

## � Після того як критичні готові

| # | Дія | Де зробити | Час |
|---|-----|------------|-----|
| 13 | Запустити CI вручну для перевірки | GitHub → Actions → CI → Run workflow | 1 хв |
| 14 | Перевірити що staging deploy працює | GitHub → Actions → переглянути логи | 3 хв |
| 15 | Staging відповідає через домен | httpsaging.example.org/health | 30 сек |
| 16 | Зробити скріншот/опис результату | Для мене | 1 хв |

---

## � Нижче — детальні інструкції для кожного кроку

### Крок 5: STAGING_SSH_KEY

Я вже маю deploy private key локально (`~/.ssh/deploy_staging_ed25519`). Якщо ви хочете його використати:

1. Я надішлю вам повний private key (екранований в чат — не зберігайте його далі як секретний файл)
2. Ви додаєте його у секрети staging environment

**АБО**

1. Я згенерую нову пару ключів
2. Публічний додам на staging VPS через SSH
3. Приватний надішлю вам для GitHub Secrets

Який варіант обираєте?

---

### Крок 7: Cloudflare API Token (DNS Edit)

1. Перейдіть до https://dash.cloudflare.com/profile/api-tokens
2. Натисність **Create Token**
3. Виберіть шаблон **"Edit zone DNS"** (або Custom Token):
   - Zone Resources: **Include** → Specific zone → `example.org`
   - TTL: виберіть 1 рік
4. Натисність **Continue to summary** → **Create Token**
5. Скопіюйте та видаліть з системи фрагменти які не повинні бути публічними

Формат: довгий BASE64 рядок (поза префіксом `cfat_`)

---

### Крок 8: Linear API Key

1. https://linear.app → Settings → API → Personal API tokens → Add
2. Name: `hermes-bot`
3. Scopes: Read, Write (automatic)
4. Скопіюйте ключ (починається з `lin_api_`)

** Після надання:**
- Я сконфігурю workspace та labels
- Створюю issues відповідно до ROADMAP.md
- Встановлюю двонаправлений sync

---

### Крок 9: Telegram

Напишіть мені:
- Bot token (який ви отримали від BotFather)
- Staging chat ID (додайте бота у групу → https://api.telegram.org/bot<TOKEN>/getUpdates → знайдіть "chat":{"id":-123456789)
- Production chat ID (той самий метод)

---

### Крок 10: Obsidian Vault

Вкажіть шлях:
- **Windows:** `C:\Users\<username>\Obsidian\Pulse of Earth` або `C:\Obsidian\Pulse of Earth`
- **Mac:** `/Users/<username>/Obsidian/Pulse%20of%20Earth`
- **Linux:** `/home/<username>/Obsidian/Pulse of Earth`

Або якщо vault ще не існує — вкажіть де створити.

**Обидва варіанти працюють**.

---

## � Контакти для швидкого старту

Якщо хочете почати з чогось конкретного — напишіть "почни з X" і я дам інструкції.

Успіхів!
