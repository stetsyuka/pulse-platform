# Специфікація: вихідні вебхуки статусу замовлення

## Мета
Після зміни статусу замовлення партнер отримує `POST` на свій URL з підписом HMAC-SHA256. Доставка надійна (outbox, ADR 004), повтори не створюють дублів у партнера.

## Подія
`order.status_changed`: `{"event_id", "event_type", "order_id", "status", "occurred_at"}` (`occurred_at` — UTC ISO 8601).

## Таблиця `webhook_deliveries`
| Поле | Тип | Примітка |
|---|---|---|
| `id` | integer PK | |
| `idempotency_key` | varchar(64) **UNIQUE** | `sha256("{event_type}:{order_id}:{status}")` |
| `event_type` | varchar(64) | |
| `payload` | json | тіло події |
| `status` | varchar(16) | `pending` → `delivered` або `failed` |
| `attempts` | integer | 0…3 |
| `next_attempt_at` | timestamptz | коли воркер може брати знову |
| `last_error` | varchar(500), null | без секретів і заголовків |
| `created_at` | timestamptz | |

## Правила
1. **Постановка в чергу** (`enqueue_order_event`) атомарна: одна подія = один рядок навіть за паралельних викликів. Унікальність забезпечує БД (`INSERT … ON CONFLICT DO NOTHING`), а не `SELECT` перед `INSERT`.
2. **Підпис:** заголовки `X-Pulse-Timestamp: <unix>` і `X-Pulse-Signature: sha256=<hex>`, де hex = HMAC-SHA256(секрет, `"{timestamp}.{body}"`). Секрет — `WEBHOOK_SIGNING_SECRET` з оточення.
3. **Ідемпотентність у партнера:** заголовок `Idempotency-Key: <idempotency_key>` в кожній спробі.
4. **Повтори:** до 3 спроб; після невдалої — `next_attempt_at = now + 2^attempts с`; після третьої — `failed`. 2xx → `delivered`; 4xx (крім 429) → одразу `failed`.
5. **HTTP** — лише спільний клієнт `core/http.py`, таймаут 10 с.
6. **Логи** — без тіла, підпису й секрету: лише `delivery_id`, статус, номер спроби.

## Порядок робіт (Contract-First)
1. Схеми й таблиця (цей чекпойнт) → 2. ядро + юніт-тести → 3. воркер → 4. фронтенд-індикатор доставки (поза Сезоном 1).
