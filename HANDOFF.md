# HANDOFF — модуль вихідних вебхуків

**Гілка:** `feat-webhooks` → чекпойнт `ep05-end`
**Оновлено:** кінець Серії 05

## Зроблено
- Обрано outbox у PostgreSQL — `docs/decisions/004-webhook-outbox.md`.
- Специфікація — `docs/specs/2026-11-webhooks-design.md`.
- Шар 1 (контракти): `services/api/webhooks/schemas.py`, `services/api/webhooks/models.py`, міграція `0002_webhook_deliveries`.
- Окремо (через `/fork`): виправлено витік з'єднань у `workers/billing_retry.py` — тепер спільний клієнт `core/http.py` (причина падіння з `logs/worker-crash.log`).

## Серія 05
- Тести за специфікацією написано до реалізації (`services/api/tests/unit/test_webhooks.py`).
- Реалізація: `webhooks/crypto.py`, `webhooks/handler.py`, `webhooks/worker.py`.
- Рев'ю знайшло гонку `SELECT` → `INSERT` ключа ідемпотентності і підпис у логах; виправлено атомарним `INSERT … ON CONFLICT DO NOTHING`, додано регресійні тести.

## Поточний чекпойнт
Модуль готовий до PR, `make check` зелений (18 тестів).

## Знайдені обмеження
- У тестах SQLite: `ON CONFLICT DO NOTHING` є і там, але вставку треба робити через діалект (`sqlalchemy.dialects.postgresql` / `sqlite`).
- Секрет підпису ще не заведено в `.env.example` для всіх оточень — лише заглушка.

## Далі (Сезон 2)
1. Хук `Stop`, який не дає завершити сесію з червоним `make check` (Серія 06).
2. Виклик `enqueue_order_event` у зміні статусу замовлення в тій самій транзакції.
3. Метрика віку найстарішої `pending`-доставки (умова переходу на брокер з ADR 004).
