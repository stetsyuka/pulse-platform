import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.ext.asyncio import AsyncSession

from webhooks.models import WebhookDelivery
from webhooks.schemas import OrderStatusChanged


def idempotency_key(event: OrderStatusChanged) -> str:
    raw = f"{event.event_type}:{event.order_id}:{event.status}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def enqueue_order_event(session: AsyncSession, event: OrderStatusChanged) -> int:
    """Одна подія = один рядок навіть за паралельних викликів.

    Унікальність гарантує UNIQUE (idempotency_key) у БД: SELECT перед INSERT
    лишає вікно, в якому два виклики обидва не бачать рядка й обидва вставляють.
    """
    key = idempotency_key(event)
    now = datetime.now(UTC)
    values = {
        "idempotency_key": key,
        "event_type": event.event_type,
        "payload": event.model_dump(mode="json"),
        "status": "pending",
        "attempts": 0,
        "next_attempt_at": now,
        "created_at": now,
    }
    dialect = postgresql if session.get_bind().dialect.name == "postgresql" else sqlite
    stmt = dialect.insert(WebhookDelivery).values(**values)
    await session.execute(stmt.on_conflict_do_nothing(index_elements=["idempotency_key"]))
    await session.commit()
    delivery_id = await session.scalar(
        select(WebhookDelivery.id).where(WebhookDelivery.idempotency_key == key)
    )
    assert delivery_id is not None
    return delivery_id
