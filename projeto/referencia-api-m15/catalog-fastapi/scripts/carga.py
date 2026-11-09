"""Carga simples: N requisições GET com C em voo. Uso: python scripts/carga.py URL N C  (imprime req/s e percentis em ms)."""

import asyncio
import statistics
import sys
import time

import httpx


async def main(url: str, n: int, c: int) -> None:
    sem = asyncio.Semaphore(c)
    lat: list[float] = []
    falhas = 0

    async def uma(cli: httpx.AsyncClient) -> None:
        nonlocal falhas
        async with sem:
            t0 = time.perf_counter()
            r = await cli.get(url)
            lat.append((time.perf_counter() - t0) * 1000)
            falhas += r.status_code != 200

    async with httpx.AsyncClient(timeout=60, limits=httpx.Limits(max_connections=c)) as cli:
        await asyncio.gather(*(uma(cli) for _ in range(30)))  # aquecimento
        lat.clear()
        t0 = time.perf_counter()
        await asyncio.gather(*(uma(cli) for _ in range(n)))
        dt = time.perf_counter() - t0
    q = statistics.quantiles(lat, n=100)
    print(f"{n / dt:7.0f} req/s  p50={q[49]:6.1f} ms  p95={q[94]:6.1f} ms  falhas={falhas}")


asyncio.run(main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3])))
