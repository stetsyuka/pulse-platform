import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from webhooks.models import WebhookDelivery
from webhooks.schemas import OrderStatusChanged


def idempotency_key(event: OrderStatusChanged) -> str:
    raw = f"{event.event_type}:{event.order_id}:{event.status}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def enqueue_order_event(session: AsyncSession, event: OrderStatusChanged) -> int:
    key = idempotency_key(event)
    existing = await session.scalar(
        select(WebhookDelivery.id).where(WebhookDelivery.idempotency_key == key)
    )
    if existing is not None:
        return existing
    now = datetime.now(UTC)
    delivery = WebhookDelivery(
        idempotency_key=key,
        event_type=event.event_type,
        payload=event.model_dump(mode="json"),
        status="pending",
        attempts=0,
        next_attempt_at=now,
        created_at=now,
    )
    session.add(delivery)
    await session.commit()
    return delivery.id
