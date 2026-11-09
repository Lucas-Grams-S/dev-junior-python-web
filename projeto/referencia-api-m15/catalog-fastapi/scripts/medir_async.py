"""Dispara N requisições concorrentes a cada rota e mede o tempo total. Uso: python scripts/medir_async.py http://localhost:8820 20"""

import asyncio
import sys
import time

import httpx


async def main(base: str, n: int) -> None:
    async with httpx.AsyncClient(base_url=base, timeout=60, limits=httpx.Limits(max_connections=200)) as c:
        for rota in ("/async-correto", "/sync-def", "/async-bloqueando"):
            t0 = time.perf_counter()
            rs = await asyncio.gather(*(c.get(rota) for _ in range(n)))
            dt = time.perf_counter() - t0
            print(f"{rota:20} {n} requisições concorrentes: {dt:6.2f} s  (todas 200: {all(r.status_code == 200 for r in rs)})")
        t0 = time.perf_counter()
        await c.get("/ping")
        print(f"/ping sozinho: {(time.perf_counter() - t0) * 1000:7.1f} ms")
        # o /ping responde rápido SE o laço estiver livre: dispara junto com 5 bloqueadoras
        bloqueadoras = [asyncio.create_task(c.get("/async-bloqueando")) for _ in range(5)]
        await asyncio.sleep(0.1)
        t0 = time.perf_counter()
        await c.get("/ping")
        print(f"/ping durante 5 bloqueadoras: {(time.perf_counter() - t0) * 1000:7.0f} ms")
        await asyncio.gather(*bloqueadoras)


asyncio.run(main(sys.argv[1], int(sys.argv[2])))
