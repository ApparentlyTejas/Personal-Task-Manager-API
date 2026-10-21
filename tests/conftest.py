"""
Shared pytest fixtures for the API smoke tests.

Tests talk to a real PostgreSQL instance (the same engine the app uses in
production/Docker). Point DATABASE_URL at a disposable database before
running them, e.g. the `postgres` service container used in CI, or a local
`docker run -p 5544:5432 postgres:15-alpine ...` for manual runs.
"""
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from database import DATABASE_URL
from main import app
from models import Base


@pytest_asyncio.fixture(autouse=True)
async def _reset_database() -> AsyncGenerator[None, None]:
    """Drop and recreate all tables before every test for isolation."""
    engine = create_async_engine(DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """An httpx client wired directly to the FastAPI app (no network)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
