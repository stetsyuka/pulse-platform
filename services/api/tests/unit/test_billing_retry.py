import httpx

import core.http
from workers import billing_retry


async def test_charge_reuses_shared_client(monkeypatch):
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(id(request))
        return httpx.Response(200, json={"ok": True})

    shared = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(core.http, "_client", shared)
    created: list[httpx.AsyncClient] = []
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **kw: created.append(1) or shared)

    assert await billing_retry.charge_order(1, 500) is True
    assert await billing_retry.charge_order(2, 700) is True
    assert len(calls) == 2
    assert created == []  # жодного нового клієнта на запит
    await shared.aclose()
