"""Тести за docs/specs/2026-11-webhooks-design.md. Пишуться ДО реалізації."""

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import func, select

import core.http
from webhooks import crypto, handler, worker
from webhooks.models import WebhookDelivery
from webhooks.schemas import OrderStatusChanged

SECRET = "test-secret"


def _event(order_id: int = 42, status: str = "paid") -> OrderStatusChanged:
    return OrderStatusChanged(
        event_id=f"evt-{order_id}-{status}",
        order_id=order_id,
        status=status,
        occurred_at=datetime(2026, 11, 5, 12, 0, tzinfo=UTC),
    )


@pytest.fixture
def partner(monkeypatch):
    """Партнер, який відповідає заданими статусами й записує запити."""
    state: dict = {"responses": [200], "requests": []}

    def handle(request: httpx.Request) -> httpx.Response:
        state["requests"].append(request)
        code = state["responses"].pop(0) if state["responses"] else 200
        return httpx.Response(code)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
    monkeypatch.setattr(core.http, "_client", client)
    monkeypatch.setenv("WEBHOOK_SIGNING_SECRET", SECRET)
    return state


def test_signature_matches_spec():
    body = b'{"a":1}'
    headers = crypto.sign(body, SECRET, timestamp=1_700_000_000)
    expected = hmac.new(SECRET.encode(), b'1700000000.{"a":1}', hashlib.sha256).hexdigest()
    assert headers["X-Pulse-Timestamp"] == "1700000000"
    assert headers["X-Pulse-Signature"] == f"sha256={expected}"


def test_idempotency_key_is_stable_per_event():
    assert handler.idempotency_key(_event()) == handler.idempotency_key(_event())
    assert handler.idempotency_key(_event(status="paid")) != handler.idempotency_key(
        _event(status="shipped")
    )


async def test_enqueue_twice_creates_one_delivery(session):
    first = await handler.enqueue_order_event(session, _event())
    second = await handler.enqueue_order_event(session, _event())
    assert first == second
    count = await session.scalar(select(func.count()).select_from(WebhookDelivery))
    assert count == 1


async def test_worker_delivers_signed_request_with_idempotency_key(session, partner):
    delivery_id = await handler.enqueue_order_event(session, _event())
    await worker.deliver_due(session)

    delivery = await session.get(WebhookDelivery, delivery_id)
    assert delivery is not None and delivery.status == "delivered"
    request = partner["requests"][0]
    assert request.headers["Idempotency-Key"] == delivery.idempotency_key
    expected = crypto.sign(request.content, SECRET, int(request.headers["X-Pulse-Timestamp"]))
    assert request.headers["X-Pulse-Signature"] == expected["X-Pulse-Signature"]
    assert json.loads(request.content)["order_id"] == 42


async def test_worker_retries_with_backoff_then_fails(session, partner):
    partner["responses"] = [503, 503, 503]
    delivery_id = await handler.enqueue_order_event(session, _event())

    for hours in (1, 2, 3):  # кожен прогін — пізніше за наступну спробу
        await worker.deliver_due(session, now=datetime.now(UTC) + timedelta(hours=hours))

    delivery = await session.get(WebhookDelivery, delivery_id)
    assert delivery is not None
    assert delivery.attempts == 3
    assert delivery.status == "failed"
    assert len(partner["requests"]) == 3


async def test_client_error_fails_without_retry(session, partner):
    partner["responses"] = [400]
    delivery_id = await handler.enqueue_order_event(session, _event())
    await worker.deliver_due(session)
    delivery = await session.get(WebhookDelivery, delivery_id)
    assert delivery is not None and delivery.status == "failed" and delivery.attempts == 1


async def test_concurrent_enqueue_creates_single_delivery(tmp_path):
    """Регресія з /code-review ultra: дві паралельні постановки однієї події."""
    import asyncio

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from db.base import Base

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/race.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def enqueue() -> int:
        async with maker() as s:
            return await handler.enqueue_order_event(s, _event())

    ids = await asyncio.gather(*(enqueue() for _ in range(5)))
    async with maker() as s:
        count = await s.scalar(select(func.count()).select_from(WebhookDelivery))
    await engine.dispose()
    assert count == 1
    assert len(set(ids)) == 1


async def test_worker_never_logs_signature(session, partner, caplog):
    caplog.set_level("INFO", logger="webhooks.worker")
    await handler.enqueue_order_event(session, _event())
    await worker.deliver_due(session)
    out = "\n".join(r.getMessage() for r in caplog.records)
    assert out  # воркер щось логує
    assert "X-Pulse-Signature" not in out
    assert "sha256=" not in out
