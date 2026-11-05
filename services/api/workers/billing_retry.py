"""Повторні спроби списання за замовленнями, що впали на етапі білінгу."""

import asyncio

import httpx

from core.config import get_settings
from core.logging import get_logger

log = get_logger("workers.billing_retry")
MAX_ATTEMPTS = 5


async def charge_order(order_id: int, amount_cents: int) -> bool:
    settings = get_settings()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        client = httpx.AsyncClient(timeout=10.0)
        try:
            resp = await client.post(
                f"{settings.billing_api_url}/charges",
                json={"order_id": order_id, "amount_cents": amount_cents},
                headers={"Authorization": f"Bearer {settings.billing_api_token}"},
            )
            if resp.status_code < 500:
                return resp.is_success
            log.warning(f"billing 5xx for order {order_id}, attempt {attempt}")
        except httpx.TransportError as e:
            log.warning(f"billing transport error for order {order_id}: {e!r}")
        await asyncio.sleep(2**attempt)
    return False


async def run(order_ids: list[tuple[int, int]]) -> None:
    await asyncio.gather(*(charge_order(oid, amount) for oid, amount in order_ids))
