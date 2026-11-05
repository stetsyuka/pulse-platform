"""Smoke-тест: піднімає застосунок у процесі й перевіряє /health і базовий маршрут."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import httpx  # noqa: E402

from db.base import Base  # noqa: E402
from db.session import engine  # noqa: E402
from main import app  # noqa: E402


async def main() -> int:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://smoke") as client:
        health = await client.get("/health")
        orders = await client.get("/orders")
    ok = (
        health.status_code == 200
        and health.json() == {"status": "ok"}
        and orders.status_code == 200
    )
    status = "OK" if ok else "FAIL"
    print(f"smoke: /health={health.status_code} /orders={orders.status_code} -> {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
