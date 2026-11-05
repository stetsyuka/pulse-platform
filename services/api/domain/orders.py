from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Order


class OrderNotFoundError(Exception):
    pass


class InvalidDiscountError(Exception):
    pass


def calculate_discount_cents(subtotal_cents: int, percent: int) -> int:
    if not 0 <= percent <= 100:
        raise InvalidDiscountError(f"discount percent out of range: {percent}")
    return int(subtotal_cents * (percent / 100))


async def create_order(
    session: AsyncSession, customer_id: str, subtotal_cents: int, discount_percent: int = 0
) -> Order:
    order = Order(
        customer_id=customer_id,
        subtotal_cents=subtotal_cents,
        discount_cents=calculate_discount_cents(subtotal_cents, discount_percent),
        status="new",
        created_at=datetime.utcnow(),  # noqa: DTZ003
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order:
    order = await session.get(Order, order_id)
    if order is None:
        raise OrderNotFoundError(order_id)
    return order


async def list_orders(session: AsyncSession, limit: int, offset: int) -> list[Order]:
    result = await session.execute(select(Order).order_by(Order.id).limit(limit).offset(offset))
    return list(result.scalars())
