"""Três jeitos de "esperar 0,5 s" num servidor ASGI. Subir: uv run uvicorn scripts.async_demo:app --port 8820"""

import asyncio
import time

from fastapi import FastAPI

app = FastAPI()


@app.get("/async-correto")
async def async_correto() -> dict[str, str]:
    await asyncio.sleep(0.5)  # CEDE o laço de eventos: outras requisições andam enquanto espera
    return {"modo": "async def + await"}


@app.get("/sync-def")
def sync_def() -> dict[str, str]:
    time.sleep(0.5)  # `def` comum: o FastAPI roda numa THREAD do pool (40 por padrão); o laço fica livre
    return {"modo": "def (threadpool)"}


@app.get("/async-bloqueando")
async def async_bloqueando() -> dict[str, str]:
    time.sleep(0.5)  # noqa: ASYNC251  # ERRO CLÁSSICO: chamada bloqueante dentro de async def PARALISA o laço inteiro
    return {"modo": "async def + time.sleep (bloqueia tudo)"}


@app.get("/ping")
async def ping() -> dict[str, str]:
    return {"ok": "sim"}
