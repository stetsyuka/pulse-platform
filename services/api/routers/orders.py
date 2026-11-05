"""Еталонний роутер: тонкий шар — валідація, виклик domain/, мапінг помилок у HTTP."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from domain import orders as domain

router = APIRouter(prefix="/orders", tags=["orders"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class OrderCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64)
    subtotal_cents: int = Field(gt=0)
    discount_percent: int = Field(default=0, ge=0, le=100)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: str
    subtotal_cents: int
    discount_cents: int
    status: str
    created_at: datetime


@router.post("", response_model=OrderOut, status_code=201)
async def create_order(payload: OrderCreate, session: SessionDep) -> OrderOut:
    try:
        order = await domain.create_order(
            session, payload.customer_id, payload.subtotal_cents, payload.discount_percent
        )
    except domain.InvalidDiscountError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return OrderOut.model_validate(order)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, session: SessionDep) -> OrderOut:
    try:
        return OrderOut.model_validate(await domain.get_order(session, order_id))
    except domain.OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail="order not found") from e


@router.get("", response_model=list[OrderOut])
async def list_orders(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[OrderOut]:
    return [OrderOut.model_validate(o) for o in await domain.list_orders(session, limit, offset)]
