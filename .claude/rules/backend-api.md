---
paths:
  - "services/api/**/*.py"
---

# Правила бекенду (FastAPI + SQLAlchemy 2.0 async)

## Роутери й контракти
- Роутер тонкий: валідація Pydantic v2 → виклик `services/api/domain/` → мапінг доменних помилок у HTTP-статуси.
- Схеми відповідей — `ConfigDict(from_attributes=True)`; застарілий `orm_mode` не використовувати.
- Грошові поля — `int` із суфіксом `_cents`.

## База даних
- Лише синтаксис SQLAlchemy 2.0: `select()`, `AsyncSession`, `Mapped[...]`, `mapped_column(...)`; `session.query()` заборонено.
- Запис — атомарний у межах однієї функції domain-шару.
- Унікальність, від якої залежить коректність (ключі ідемпотентності тощо), — обмеженням у БД, а не перевіркою `SELECT` перед `INSERT`.

## Міграції (`services/api/migrations/`)
- Кожна міграція має робочий `downgrade()`.
- `NOT NULL` на живу таблицю — у два кроки (expand → backfill → contract).

## Перевірка після змін
1. `uv run ruff check services/api && uv run mypy services/api`
2. `uv run pytest services/api/tests/unit -k <module> -q`
