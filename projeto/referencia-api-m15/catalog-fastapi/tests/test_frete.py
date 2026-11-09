import asyncio
import time
from decimal import Decimal

import httpx

from app.frete import consultar_frete, consultar_varios


def cliente(handler) -> httpx.AsyncClient:
    # MockTransport: o "servidor" é uma função Python; nenhuma rede, nenhum servidor, nenhuma porta
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://frete.test")


async def test_sucesso():
    async def h(request: httpx.Request) -> httpx.Response:
        assert request.url.params["cep"] == "01001000"
        return httpx.Response(200, json={"valor": "19.90"})

    async with cliente(h) as c:
        assert await consultar_frete(c, "01001000") == Decimal("19.90")


async def test_erro_500_vira_none():
    async with cliente(lambda r: httpx.Response(500)) as c:
        assert await consultar_frete(c, "01001000") is None


async def test_timeout_vira_none():
    def h(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("lento demais", request=request)

    async with cliente(h) as c:
        assert await consultar_frete(c, "01001000") is None


async def test_json_sem_campo_vira_none():
    async with cliente(lambda r: httpx.Response(200, json={"outro": 1})) as c:
        assert await consultar_frete(c, "01001000") is None


async def test_varios_em_paralelo():
    async def h(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.3)  # cada consulta "demora" 0,3 s
        return httpx.Response(200, json={"valor": "10"})

    async with cliente(h) as c:
        t0 = time.perf_counter()
        r = await consultar_varios(c, ["1", "2", "3", "4", "5"])
        dt = time.perf_counter() - t0
    assert set(r.values()) == {Decimal(10)}
    assert dt < 0.6  # 5 x 0,3 s = 1,5 s em série; juntas, ~0,3 s
