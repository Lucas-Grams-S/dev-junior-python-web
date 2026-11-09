"""Retentativas: o que o httpx faz sozinho, o que você precisa escrever e o perigo de repetir POST."""
import random
import threading
import time
from http.server import ThreadingHTTPServer

import httpx

import servidor_externo as ext
from servidor_externo import ESTADO, H, Servidor, iniciar

srv, BASE = iniciar()

print("--- 1) httpx.HTTPTransport(retries=N) só repete falhas de CONEXÃO")
# reserva uma porta, mas só sobe o servidor 0,6 s depois
livre = Servidor(("127.0.0.1", 0), H); porta = livre.server_port; livre.server_close()
def subir_tarde():
    time.sleep(0.6)
    s = Servidor(("127.0.0.1", porta), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
threading.Thread(target=subir_tarde, daemon=True).start()
t = time.perf_counter()
with httpx.Client(transport=httpx.HTTPTransport(retries=3)) as c:
    r = c.get(f"http://127.0.0.1:{porta}/ok")
print(f"servidor subiu 0,6 s depois; com retries=3 → {r.status_code} em {time.perf_counter() - t:.2f} s")
with httpx.Client(transport=httpx.HTTPTransport(retries=3)) as c:
    r = c.get(f"{BASE}/instavel?falhas=2&k=t1")
print("mas um 503 NÃO é repetido pelo transporte → status", r.status_code)


# ---------------------------------------------------------------------------------------------
IDEMPOTENTES = {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}
TRANSITORIOS = {429, 500, 502, 503, 504}


def com_retry(client, metodo, url, *, tentativas=4, base=0.2, teto=5.0, dormir=time.sleep, aleatorio=random.random, **kw):
    """Repete erros transitórios com backoff exponencial + jitter. Respeita Retry-After. Só repete métodos seguros
    (ou POST com Idempotency-Key)."""
    pode_repetir = metodo in IDEMPOTENTES or "Idempotency-Key" in kw.get("headers", {})
    esperas = []
    for n in range(tentativas):
        try:
            r = client.request(metodo, url, **kw)
            if r.status_code not in TRANSITORIOS:
                return r, esperas
            ultima = r
            espera = float(r.headers["Retry-After"]) if "Retry-After" in r.headers else min(teto, base * 2 ** n) * aleatorio()
        except (httpx.ConnectError, httpx.TimeoutException) as e:       # falha de rede/timeout
            ultima = e
            espera = min(teto, base * 2 ** n) * aleatorio()             # "full jitter": evita todos tentando juntos
        if not pode_repetir or n == tentativas - 1:
            break
        esperas.append(round(espera, 2))
        dormir(espera)
    if isinstance(ultima, Exception):
        raise ultima
    return ultima, esperas


print("\n--- 2) com_retry: backoff exponencial com jitter, Retry-After e só métodos repetíveis")
random.seed(7)
with httpx.Client(base_url=BASE, timeout=2) as c:
    r, esperas = com_retry(c, "GET", "/instavel?falhas=2&k=g", dormir=lambda s: None)
    print(f"GET instável (2 falhas, depois ok) → {r.status_code} após esperas {esperas} (valores simulados, sem dormir)")
    r, esperas = com_retry(c, "GET", "/limite?k=r", dormir=lambda s: None)
    print(f"GET com 429 + Retry-After: 1       → {r.status_code} após esperas {esperas} (obedeceu o servidor)")
    r, esperas = com_retry(c, "GET", "/instavel?falhas=99&k=x", dormir=lambda s: None)
    print(f"GET que nunca melhora              → {r.status_code} após esperas {esperas} (desistiu após 4 tentativas)")
    r, esperas = com_retry(c, "GET", "/nao-existe", dormir=lambda s: None)
    print(f"GET 404                            → {r.status_code} esperas {esperas} (erro do cliente não é repetido)")

print("\n--- 3) repetir um POST SEM idempotência duplica o efeito")
ESTADO.update(criados=0, chaves={}, perde_resposta=True)
with httpx.Client(base_url=BASE, timeout=2) as c:
    r, esperas = com_retry(c, "POST", "/pedidos", json={"sku": "A"}, dormir=lambda s: None)
    print(f"POST sem chave: o código não repete → status {r.status_code}, criados no servidor: {ESTADO['criados']} (mas o cliente nem sabe se criou)")
    ESTADO.update(criados=0, chaves={}, perde_resposta=True)
    for tentativa in range(2):                                          # um cliente 'ingênuo' que repete na mão
        r = c.post("/pedidos", json={"sku": "A"})
        if r.status_code < 500:
            break
    print(f"POST repetido na mão, sem chave   → status final {r.status_code}, criados no servidor: {ESTADO['criados']}  ← DUPLICADO")
    ESTADO.update(criados=0, chaves={}, perde_resposta=True)
    r, esperas = com_retry(c, "POST", "/pedidos", json={"sku": "A"}, headers={"Idempotency-Key": "compra-123"}, dormir=lambda s: None)
    print(f"POST com Idempotency-Key           → status {r.status_code} {r.json()}, criados no servidor: {ESTADO['criados']}  ← UM só")
