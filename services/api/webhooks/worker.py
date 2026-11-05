import json
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.http import get_http_client
from core.logging import get_logger
from webhooks.crypto import sign
from webhooks.models import WebhookDelivery

log = get_logger("webhooks.worker")
MAX_ATTEMPTS = 3


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def _attempt(delivery: WebhookDelivery, now: datetime) -> None:
    settings = get_settings()
    body = json.dumps(delivery.payload, separators=(",", ":")).encode()
    headers = {
        "Content-Type": "application/json",
        "Idempotency-Key": delivery.idempotency_key,
        **sign(body, settings.webhook_signing_secret),
    }
    delivery.attempts += 1
    log.info(f"delivering {delivery.id} attempt {delivery.attempts} headers={headers}")
    try:
        resp = await get_http_client().post(
            settings.webhook_endpoint_url, content=body, headers=headers
        )
    except httpx.TransportError as e:
        delivery.last_error = type(e).__name__
        resp = None
    if resp is not None and resp.is_success:
        delivery.status = "delivered"
        delivery.last_error = None
        return
    if resp is not None:
        delivery.last_error = f"HTTP {resp.status_code}"
        if 400 <= resp.status_code < 500 and resp.status_code != 429:
            delivery.status = "failed"
            return
    if delivery.attempts >= MAX_ATTEMPTS:
        delivery.status = "failed"
    else:
        delivery.next_attempt_at = now + timedelta(seconds=2**delivery.attempts)


async def deliver_due(session: AsyncSession, now: datetime | None = None, limit: int = 50) -> int:
    now = now or datetime.now(UTC)
    rows = await session.scalars(
        select(WebhookDelivery)
        .where(WebhookDelivery.status == "pending")
        .order_by(WebhookDelivery.id)
        .limit(limit)
    )
    due = [d for d in rows if _as_utc(d.next_attempt_at) <= now]
    for delivery in due:
        await _attempt(delivery, now)
    await session.commit()
    return len(due)
