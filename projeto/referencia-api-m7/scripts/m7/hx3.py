"""httpx assíncrono, limites de conexão e testes sem rede (MockTransport)."""
import asyncio
import time

import httpx

from servidor_externo import iniciar

srv, BASE = iniciar()


def cron(titulo, t0):
    print(f"{titulo:<62} {time.perf_counter() - t0:5.2f} s")


async def main():
    urls = [f"{BASE}/lento?ms=300&k={i}" for i in range(20)]

    t = time.perf_counter()
    with httpx.Client() as c:                                       # síncrono: uma depois da outra
        for u in urls:
            c.get(u)
    cron("20 GET de 0,3 s com httpx.Client (sequencial)", t)

    t = time.perf_counter()
    async with httpx.AsyncClient() as c:                            # assíncrono: todas juntas
        rs = await asyncio.gather(*(c.get(u) for u in urls))
    cron(f"20 GET de 0,3 s com AsyncClient + gather ({sum(r.is_success for r in rs)} ok)", t)

    t = time.perf_counter()
    limites = httpx.Limits(max_connections=5)                        # no máximo 5 conexões ao mesmo tempo
    async with httpx.AsyncClient(limits=limites, timeout=httpx.Timeout(10, pool=10)) as c:
        await asyncio.gather(*(c.get(u) for u in urls))
    cron("o mesmo, com Limits(max_connections=5)  → 4 rodadas de 0,3 s", t)

    t = time.perf_counter()
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=1), timeout=httpx.Timeout(10, pool=0.2)) as c:
        rs = await asyncio.gather(*(c.get(f"{BASE}/lento?ms=300") for _ in range(3)), return_exceptions=True)
    print("max_connections=1 e pool=0,2 s → PoolTimeout em quem espera uma vaga:", [type(r).__name__ for r in rs])

    print("\n--- falhas parciais: uma chamada falha e as outras seguem")
    async with httpx.AsyncClient(timeout=0.5) as c:
        alvos = [f"{BASE}/ok", f"{BASE}/lento?ms=2000", f"{BASE}/instavel?falhas=9&k=z", f"{BASE}/ok"]
        rs = await asyncio.gather(*(c.get(u) for u in alvos), return_exceptions=True)
    for u, r in zip(alvos, rs):
        print(f"  {u.replace(BASE, ''):<26} → {type(r).__name__ if isinstance(r, Exception) else r.status_code}")


asyncio.run(main())

print("\n--- MockTransport: testar o código que chama a API SEM rede")
def antifraude_mock(request: httpx.Request) -> httpx.Response:
    pedido = int(request.url.params["pedido"])
    if pedido == 13:
        return httpx.Response(503)
    return httpx.Response(200, json={"pedido": pedido, "risco": 10 * pedido})

def consultar(client, pedido):
    r = client.get("https://antifraude.exemplo/score", params={"pedido": pedido})
    r.raise_for_status()
    return r.json()["risco"]

cliente_de_teste = httpx.Client(transport=httpx.MockTransport(antifraude_mock))
print("pedido 3  →", consultar(cliente_de_teste, 3))
try:
    consultar(cliente_de_teste, 13)
except httpx.HTTPStatusError as e:
    print("pedido 13 →", type(e).__name__, e.response.status_code, "(nenhuma conexão de rede foi aberta)")
srv.shutdown()
