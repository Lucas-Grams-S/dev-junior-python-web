import os
from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from app import seed as seed_mod
from app.config import settings
from app.db import get_session
from app.main import app
from app.models import Base

TOKEN = "token-de-teste"


@pytest.fixture
async def engine():
    # Padrão: SQLite em memória; StaticPool = UMA conexão compartilhada (senão cada conexão veria um banco vazio diferente).
    # CATALOG_TEST_DATABASE_URL=postgresql+asyncpg://... roda a MESMA suíte no PostgreSQL (tabelas recriadas a cada teste).
    url = os.environ.get("CATALOG_TEST_DATABASE_URL")
    if url:
        eng = create_async_engine(url, poolclass=NullPool)
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    else:
        eng = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine, monkeypatch):
    fabrica = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(seed_mod, "SessionLocal", fabrica)
    return fabrica


@pytest.fixture
async def seeded(session_factory):
    await seed_mod.seed()
    return session_factory


@pytest.fixture
async def client(seeded, monkeypatch) -> AsyncIterator[httpx.AsyncClient]:
    async def _session() -> AsyncIterator[AsyncSession]:
        async with seeded() as s:
            yield s

    app.dependency_overrides[get_session] = _session  # troca a dependência: a rota nem sabe
    monkeypatch.setattr(settings, "api_token", TOKEN)
    transport = httpx.ASGITransport(app=app)  # chama o app direto, sem rede nem servidor
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth():
    return {"Authorization": f"Bearer {TOKEN}"}
