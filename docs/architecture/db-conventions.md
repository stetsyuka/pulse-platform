# Конвенції бази даних

- Назви таблиць — множина, `snake_case` (`orders`, `webhook_deliveries`).
- Первинний ключ — `id` (integer), часові мітки — `timestamptz` (`DateTime(timezone=True)`).
- Гроші — `integer` у центах, суфікс `_cents`.
- Унікальні бізнес-ключі (ідемпотентність, зовнішні ідентифікатори) — `UNIQUE`-обмеження в БД; вставка через `INSERT … ON CONFLICT DO NOTHING`.
- Кожна зміна схеми — міграція Alembic у тому ж PR; `alembic check` має бути чистим.
