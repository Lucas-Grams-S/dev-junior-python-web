"""Mede quanto tempo 20 requisições SIMULTÂNEAS (cada uma espera 0,5 s) levam em cada combinação servidor × view."""
import asyncio
import os
import signal
import subprocess
import sys
import time

import httpx

PORTA = 8140
N = 20
LAB = os.environ["LAB"]

CONFIGS = [
    ("gunicorn WSGI, 1 worker sync",         ["gunicorn", "config.wsgi", "-w", "1"],                       "/demo/sync/"),
    ("gunicorn WSGI, 4 workers sync",        ["gunicorn", "config.wsgi", "-w", "4"],                       "/demo/sync/"),
    ("gunicorn WSGI, 1 worker, 20 threads",  ["gunicorn", "config.wsgi", "-w", "1", "--threads", "20"],    "/demo/sync/"),
    ("uvicorn ASGI, view SÍNCRONA",          ["uvicorn", "config.asgi:application"],                       "/demo/sync/"),
    ("uvicorn ASGI, view ASSÍNCRONA",        ["uvicorn", "config.asgi:application"],                       "/demo/async/"),
    ("gunicorn WSGI, view ASSÍNCRONA",       ["gunicorn", "config.wsgi", "-w", "1"],                       "/demo/async/"),
]


async def disparar(caminho):
    async with httpx.AsyncClient(timeout=120, limits=httpx.Limits(max_connections=100)) as c:
        t = time.perf_counter()
        rs = await asyncio.gather(*(c.get(f"http://127.0.0.1:{PORTA}{caminho}") for _ in range(N)))
        return time.perf_counter() - t, sum(r.status_code == 200 for r in rs)


def esperar_no_ar():
    for _ in range(100):
        try:
            if httpx.get(f"http://127.0.0.1:{PORTA}/api/v1/categories/", timeout=1).status_code == 200:
                return True
        except httpx.HTTPError:
            time.sleep(0.2)
    return False


print(f"{N} requisições simultâneas; cada view espera 0,5 s")
print(f"{'servidor / view':<42} {'tempo total':>11}   {'vazão':>9}")
for nome, cmd, caminho in CONFIGS:
    prog = [os.path.join(LAB, ".venv/bin", cmd[0]), *cmd[1:], "--bind" if cmd[0] == "gunicorn" else "--port",
            f"127.0.0.1:{PORTA}" if cmd[0] == "gunicorn" else str(PORTA)]
    if cmd[0] == "uvicorn":
        prog += ["--host", "127.0.0.1", "--log-level", "warning"]
    else:
        prog += ["--log-level", "warning"]
    srv = subprocess.Popen(prog, cwd=LAB, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        if not esperar_no_ar():
            print(f"{nome:<42} (servidor não subiu)")
            continue
        asyncio.run(disparar(caminho))                      # aquecimento (importa módulos, abre conexões)
        total, ok = asyncio.run(disparar(caminho))
        print(f"{nome:<42} {total:9.2f} s   {N / total:6.1f} req/s" + ("" if ok == N else f"   (só {ok} responderam 200)"))
    finally:
        os.killpg(srv.pid, signal.SIGTERM)
        srv.wait(timeout=20)
        time.sleep(0.5)
