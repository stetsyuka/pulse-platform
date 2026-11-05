from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.http import close_http_client
from routers import health, orders


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_http_client()


app = FastAPI(title="Pulse Platform API", lifespan=lifespan)
app.include_router(health.router)
app.include_router(orders.router)
