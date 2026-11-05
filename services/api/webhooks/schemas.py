from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class OrderStatusChanged(BaseModel):
    event_id: str = Field(min_length=1, max_length=64)
    event_type: Literal["order.status_changed"] = "order.status_changed"
    order_id: int
    status: str = Field(min_length=1, max_length=16)
    occurred_at: datetime
