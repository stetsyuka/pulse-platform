# HANDOFF — модуль вихідних вебхуків

**Гілка:** `wip/webhooks-outbox` → чекпойнт `ep04-end`
**Оновлено:** кінець Серії 04

## Зроблено
- Обрано outbox у PostgreSQL — `docs/decisions/004-webhook-outbox.md`.
- Специфікація — `docs/specs/2026-11-webhooks-design.md`.
- Шар 1 (контракти): `services/api/webhooks/schemas.py`, `services/api/webhooks/models.py`, міграція `0002_webhook_deliveries`.
- Окремо (через `/fork`): виправлено витік з'єднань у `workers/billing_retry.py` — тепер спільний клієнт `core/http.py` (причина падіння з `logs/worker-crash.log`).

## Поточний чекпойнт
Контракти є, логіки немає. `make check` зелений.

## Знайдені обмеження
- У тестах SQLite: `ON CONFLICT DO NOTHING` є і там, але вставку треба робити через діалект (`sqlalchemy.dialects.postgresql` / `sqlite`).
- Секрет підпису ще не заведено в `.env.example` для всіх оточень — лише заглушка.

## Перші 3 кроки на завтра (Серія 05)
1. У worktree `feat-webhooks` написати ТІЛЬКИ тести за специфікацією у `services/api/tests/unit/test_webhooks.py`.
2. Реалізувати `webhooks/crypto.py`, `webhooks/handler.py`, `webhooks/worker.py` до зелених тестів, не чіпаючи тести.
3. `make check`, `/simplify`, `/code-review ultra`, PR.
