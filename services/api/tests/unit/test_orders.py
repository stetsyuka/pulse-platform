import pytest

from domain.orders import InvalidDiscountError, calculate_discount_cents


def test_discount_zero_percent():
    assert calculate_discount_cents(1999, 0) == 0


def test_discount_half():
    assert calculate_discount_cents(2000, 50) == 1000


def test_discount_out_of_range():
    with pytest.raises(InvalidDiscountError):
        calculate_discount_cents(1000, 101)


async def test_create_and_get_order(client):
    created = await client.post(
        "/orders", json={"customer_id": "acme", "subtotal_cents": 5000, "discount_percent": 10}
    )
    assert created.status_code == 201
    body = created.json()
    assert body["discount_cents"] == 500

    fetched = await client.get(f"/orders/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["customer_id"] == "acme"


async def test_get_missing_order_returns_404(client):
    resp = await client.get("/orders/999")
    assert resp.status_code == 404


async def test_list_orders_paginates(client):
    for i in range(3):
        await client.post("/orders", json={"customer_id": f"c{i}", "subtotal_cents": 100})
    resp = await client.get("/orders", params={"limit": 2, "offset": 1})
    assert [o["customer_id"] for o in resp.json()] == ["c1", "c2"]
