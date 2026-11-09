from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .db import engine
from .routers import categories, products


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # startup: nada a criar (o esquema vem do Alembic); shutdown: fecha o pool de conexões
    yield
    await engine.dispose()


app = FastAPI(
    title="MiniShop — catálogo (FastAPI)",
    version="0.1.0",
    description="Reimplementação de leitura/criação do catálogo, para comparar com Django/DRF (módulo 15).",
    lifespan=lifespan,
)
app.include_router(products.router)
app.include_router(categories.router)


@app.get("/health/", tags=["ops"], include_in_schema=False)
async def health() -> dict[str, str]:
    """Liveness: o processo responde. (Readiness com banco: /health/ready/.)"""
    return {"status": "ok"}


@app.get("/health/ready/", tags=["ops"], include_in_schema=False)
async def ready() -> dict[str, str]:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ready"}
