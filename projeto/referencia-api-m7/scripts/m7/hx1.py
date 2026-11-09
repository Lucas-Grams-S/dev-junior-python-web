"""httpx síncrono: Client, timeouts e erros."""
import time

import httpx

from servidor_externo import ESTADO, iniciar

srv, BASE = iniciar()


def cron(fn):
    t = time.perf_counter()
    r = fn()
    return r, time.perf_counter() - t


print("--- 1) Client reaproveita a conexão (keep-alive)")
ESTADO["conexoes"] = 0
for _ in range(10):
    httpx.get(f"{BASE}/ok")                                   # função de módulo: abre e fecha uma conexão a cada chamada
print("10 × httpx.get(...)         → conexões TCP abertas no servidor:", ESTADO["conexoes"])
ESTADO["conexoes"] = 0
with httpx.Client(base_url=BASE) as c:
    for _ in range(10):
        c.get("/ok")
print("10 × client.get(...)        → conexões TCP abertas no servidor:", ESTADO["conexoes"])

print("\n--- 2) timeouts: connect / read / write / pool")
padrao = httpx.Client().timeout
print("timeout padrão do httpx:", padrao)
for nome, tempo in (("read=0,5 s numa resposta de 2 s", httpx.Timeout(5, read=0.5)),):
    try:
        httpx.get(f"{BASE}/lento?ms=2000", timeout=tempo)
    except httpx.ReadTimeout as e:
        print(f"{nome} → {type(e).__name__}")
try:
    httpx.get("http://127.0.0.1:1/", timeout=1)               # porta fechada
except httpx.ConnectError as e:
    print("porta fechada → ConnectError:", e)
try:
    httpx.get(f"{BASE}/trava", timeout=httpx.Timeout(10, read=0.3))
except httpx.TimeoutException as e:
    print("servidor que 'trava' → ", type(e).__name__, "(é subclasse de TimeoutException)")

print("\n--- 3) status de erro NÃO levanta exceção sozinho")
r = httpx.get(f"{BASE}/instavel?falhas=9&k=a")
print("status:", r.status_code, "| is_success:", r.is_success, "| is_server_error:", r.is_server_error)
try:
    r.raise_for_status()
except httpx.HTTPStatusError as e:
    print("raise_for_status() →", type(e).__name__, "| resposta:", e.response.status_code)
r = httpx.get(f"{BASE}/nao-existe")
print("404:", r.status_code, r.json())

print("\n--- 4) a hierarquia de exceções (as que você vai tratar)")
for cls in (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.HTTPStatusError):
    print(f"  {cls.__name__:<18} ← " + " ← ".join(c.__name__ for c in cls.__mro__[1:-2]))
srv.shutdown()
