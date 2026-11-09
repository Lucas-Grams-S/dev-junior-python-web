from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import settings


def make_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, pool_pre_ping=True)


engine = make_engine(settings.database_url)
# expire_on_commit=False: depois do commit os atributos continuam legíveis (em async, recarregar "por baixo" não é possível)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependência: uma sessão por requisição, fechada ao final (yield = setup/teardown)."""
    async with SessionLocal() as session:
        yield session
