"""Cliente HTTP assíncrono para um serviço externo de frete (aula 15.04): timeout, falha controlada e cliente INJETADO."""

import asyncio
import logging
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


async def consultar_frete(client: httpx.AsyncClient, cep: str) -> Decimal | None:
    """Devolve o valor do frete, ou None se o serviço falhar (o catálogo continua sem frete: falha aberta, como na aula 14.03)."""
    try:
        r = await client.get("/frete", params={"cep": cep}, timeout=httpx.Timeout(2.0, connect=1.0))
        r.raise_for_status()
        return Decimal(str(r.json()["valor"]))
    except (httpx.HTTPError, KeyError, ValueError):  # timeout, conexão, status 4xx/5xx, JSON sem o campo
        logger.warning("frete_indisponivel cep=%s", cep, exc_info=True)
        return None


async def consultar_varios(client: httpx.AsyncClient, ceps: list[str]) -> dict[str, Decimal | None]:
    """As consultas independentes andam JUNTAS (tempo total ~ o da mais lenta, não a soma)."""
    valores = await asyncio.gather(*(consultar_frete(client, c) for c in ceps))
    return dict(zip(ceps, valores, strict=True))
