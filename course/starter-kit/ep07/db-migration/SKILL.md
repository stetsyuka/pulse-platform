---
name: db-migration
description: Створює й перевіряє безпечні міграції Alembic для PostgreSQL у pulse-platform без блокування живих таблиць. Викликай, коли просять додати чи змінити таблицю, колонку, індекс або зовнішній ключ, або кажуть «створи міграцію», «онови схему БД», «нова ревізія». Для відкату вже застосованої ревізії не підходить — це робить людина вручну.
argument-hint: "[що змінити в схемі]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(uv run alembic *), Bash(python3 *), Bash(make check)
---

# Міграція БД без простою (`db-migration`)

Регламент створення міграцій схеми PostgreSQL, які не блокують запис у живі таблиці.
Конвенції назв і типів — у `docs/architecture/db-conventions.md`, не дублюй їх тут.
Великі таблиці (понад мільйон рядків) — спершу прочитай `references/zero-downtime-patterns.md`.

## Стан перед стартом

- Голова Alembic: !`cd services/api && uv run alembic current 2>/dev/null | tail -n 1 || echo "немає підключення до БД"`
- Останні ревізії: !`ls services/api/migrations/versions | tail -n 3`
- Запит: $ARGUMENTS

## Крок 0 — факти, без яких не починати

| Факт | Звідки |
|---|---|
| Таблиця і модель SQLAlchemy | `services/api/db/models.py` |
| Нова таблиця чи жива з трафіком | код або питання людині |
| Чи потрібен `NOT NULL` у фінальному стані | задача |
| Поточна голова (уникнути двох heads) | `uv run alembic heads` у `services/api` |

**Питай, а не вгадуй.** Якщо факт не встановити з коду — постав одне коротке питання.

## Кроки

1. Онови модель у `services/api/db/models.py`.
2. Створи ревізію в `services/api/migrations/versions/` з наступним номером (`0003_…`), `down_revision` — поточна голова.
3. Приведи `upgrade()` і `downgrade()` до правил нижче.
4. Перевір блокування (код скрипта читати не треба):
   `python3 "${CLAUDE_SKILL_DIR}/scripts/check_locks.py" services/api/migrations/versions/`
5. `make check` — типи, лінтер, тести, smoke.

## Правила (з реальних інцидентів)

- Індекс на живій таблиці — лише `postgresql_concurrently=True` всередині
  `with op.get_context().autocommit_block():`. Звичайний `create_index` блокує запис до кінця побудови.
- `NOT NULL` колонка на живій таблиці — спершу `nullable=True` або `server_default`, заповнення окремим кроком.
- Зовнішній ключ — `postgresql_not_valid=True`, а `VALIDATE CONSTRAINT` окремою ревізією.
- `downgrade()` завжди симетричний; `pass` заборонено.

## Готово, коли

1. `check_locks.py` повернув `OK (0 lock hazards found)`.
2. `make check` зелений.
3. У відповіді людині — одне речення, чому обрано саме такий спосіб.
