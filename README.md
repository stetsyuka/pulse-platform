# pulse-platform

Навчальний проєкт курсу **«Архітектор проєктів з Claude Code»** (українською, Сезон 1). Невеликий B2B-сервіс замовлень: Python 3.12+ / FastAPI / SQLAlchemy 2.0 async / PostgreSQL (`services/api/`), Next.js App Router + Tailwind (`apps/web/`), спільні типи (`packages/contracts/`).

Увесь Сезон 1 ми ведемо **цей один репозиторій**: кожна серія щось у ньому змінює, а гілка-чекпойнт фіксує стан на кінець серії. Можна почати з будь-якої серії.

## Чекпойнти

| Гілка | Стан | Серія |
|---|---|---|
| `ep01-start` (= `main`) | робочий сервіс без `CLAUDE.md` і без налаштувань Claude Code | 01 — перший сеанс, гігієна середовища |
| `ep02-end` | `CLAUDE.md`, `AGENTS.md`, модульні правила `.claude/rules/`, документація конвенцій | 02 — контекст і пам'ять проєкту |
| `ep03-end` | `.claude/settings.json` з базовою бронею дозволів і пісочницею | 03 — дозволи, auto mode, безпека |
| `ep04-end` | специфікація й рішення щодо модуля вебхуків, `HANDOFF.md`, контракти (схеми, таблиця, міграція) | 04 — планування й декомпозиція |
| `ep05-end` | вебхуки реалізовано через TDD, атомарна ідемпотентність, `make check` зелений | 05 — верифікація, worktree, рев'ю |

```bash
git clone <url> ~/Projects/pulse-platform && cd ~/Projects/pulse-platform
git checkout ep02-end        # почати з потрібної серії
```

## Швидкий старт

```bash
uv sync                      # Python-залежності
cp .env.example .env         # локальні змінні (ніколи не комітьте .env)
make check                   # типи → лінтер → тести → smoke
make dev                     # API на http://localhost:8001 (без Postgres — SQLite за замовчуванням)
```

Із PostgreSQL: `docker compose up -d db`, потім `uv run alembic -c services/api/alembic.ini upgrade head`.
Фронтенд: `pnpm install && pnpm --filter web dev` (http://localhost:3000).

## Домашнє завдання Серії 01

На `ep01-start` у коді навмисно залишено **три слабкі місця** — такі, які легко пропустити на рев'ю. Відкрийте проєкт у режимі плану (`claude --permission-mode plan`), попросіть агента пояснити архітектуру й знайти їх, а потім перевірте себе: у `ep02-end` два з них виправлено за правилами `CLAUDE.md`, а третє — у Серії 04 (підказка: `logs/worker-crash.log`).

## Матеріали курсу

`course/starter-kit/ep01…ep05/` — шаблони до кожної серії (налаштування, `CLAUDE.md`/`AGENTS.md`, чеклісти, шаблони задач і передачі справ). Плейліст курсу — на YouTube-каналі InferenceLab.

Код — під ліцензією MIT (див. `LICENSE`).
