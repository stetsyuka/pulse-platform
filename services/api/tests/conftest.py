import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from collections.abc import AsyncIterator  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from db.base import Base  # noqa: E402
from db.session import get_session  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture
async def session_maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def session(session_maker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_maker() as s:
        yield s


@pytest.fixture
async def client(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[httpx.AsyncClient]:
    async def _override() -> AsyncIterator[AsyncSession]:
        async with session_maker() as s:
            yield s

    app.dependency_overrides[get_session] = _override
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
