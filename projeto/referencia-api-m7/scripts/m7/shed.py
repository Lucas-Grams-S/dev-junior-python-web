"""Middleware ASGI de 'load shedding': se há requisições demais em andamento, recusa as excedentes com 503 + Retry-After."""
import asyncio
import threading
import time

import httpx
import uvicorn


def limitar(app, maximo):
    em_andamento = 0

    async def novo(scope, receive, send):
        nonlocal em_andamento
        if scope["type"] != "http":
            return await app(scope, receive, send)
        if em_andamento >= maximo:                                   # sem vaga: falhar RÁPIDO é melhor que enfileirar sem fim
            corpo = b'{"detail":"servidor ocupado","code":"overloaded"}'
            await send({"type": "http.response.start", "status": 503,
                        "headers": [(b"content-type", b"application/json"), (b"retry-after", b"1"),
                                    (b"content-length", str(len(corpo)).encode())]})
            return await send({"type": "http.response.body", "body": corpo})
        em_andamento += 1
        try:
            await app(scope, receive, send)
        finally:
            em_andamento -= 1                                        # sempre libera a vaga, mesmo com erro
    return novo


async def lenta(scope, receive, send):
    if scope["type"] != "http":
        return
    await asyncio.sleep(0.5)
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-length", b"2")]})
    await send({"type": "http.response.body", "body": b"ok"})


srv = uvicorn.Server(uvicorn.Config(limitar(lenta, 4), host="127.0.0.1", port=8152, log_level="error"))
threading.Thread(target=srv.run, daemon=True).start()
while not srv.started:
    time.sleep(0.05)


async def disparar():
    async with httpx.AsyncClient() as c:
        return await asyncio.gather(*(c.get("http://127.0.0.1:8152/") for _ in range(10)))


t = time.perf_counter()
rs = asyncio.run(disparar())
codigos = sorted(r.status_code for r in rs)
print(f"10 requisições simultâneas, limite de 4 em andamento → {codigos.count(200)} × 200 e {codigos.count(503)} × 503 em {time.perf_counter() - t:.2f} s")
recusada = next(r for r in rs if r.status_code == 503)
print("exemplo de recusa:", recusada.status_code, recusada.json(), "| Retry-After:", recusada.headers["retry-after"])
srv.should_exit = True
