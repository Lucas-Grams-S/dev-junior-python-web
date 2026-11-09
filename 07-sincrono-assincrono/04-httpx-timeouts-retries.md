# 4. `httpx`, timeouts e retentativas

> ⏱️ ~1h30 · Módulo 7 · Pré-requisitos: [7.01](01-bloqueante-io-cpu.md), [7.03](03-asyncio.md), [6.01](../06-apis-rest/01-principios-rest.md) (idempotência), [6.09](../06-apis-rest/09-paginacao-throttling.md) (`429` e `Retry-After`)

> ✅ **Verificação.** Código executado em 2026-11-08 com **Python 3.13** e **httpx 0.28.1** contra uma “API externa” de mentira, feita só com a biblioteca padrão (lenta, instável, com limite de taxa e que trava). **As saídas foram geradas executando os arquivos ao montar a aula.** Os tempos variam alguns centésimos entre execuções; os números de tentativas e de efeitos colaterais não.

## 🎯 Objetivos
Ao final desta aula você consegue:
- Chamar APIs externas com `httpx` (síncrono e assíncrono), reaproveitando conexões com `Client`/`AsyncClient`
- Definir os **quatro timeouts** (conexão, leitura, escrita, *pool*) e tratar a hierarquia de exceções
- Escrever uma **retentativa segura**: erros transitórios, *backoff* exponencial com *jitter*, `Retry-After`, e **só** em operações repetíveis
- Mostrar, com o servidor contando os efeitos, por que repetir um `POST` **sem idempotência** duplica pedidos
- Explicar o **disjuntor** (*circuit breaker*) e testar código HTTP **sem rede** com `MockTransport`

## 🤔 Por que isso importa
O MiniShop depende de serviços que não controla: antifraude, gateway de pagamento, correios, e-mail. Todos **falham**, **demoram** e **limitam** chamadas. Um júnior que escreve `requests.get(url)` sem *timeout* cria um servidor que **trava para sempre** quando o outro lado trava; um que repete um `POST` às cegas **cobra o cliente duas vezes**. Entender timeouts, retentativas e idempotência é o que separa integração de produção de integração de demonstração.

## 💡 Intuição (explicação simples)
Ligar para uma empresa: se **ninguém atende** (conexão), você desiste depois de alguns toques (*connect timeout*); se atendem e **ficam em silêncio** (leitura), você desliga depois de um tempo (*read timeout*). Se a linha está **ocupada** (503), tenta de novo **mais tarde, esperando cada vez mais** (*backoff*) e **sem todo mundo ligar no mesmo segundo** (*jitter*); se a atendente diz “ligue daqui a 1 minuto” (`Retry-After`), você **obedece**. Mas atenção ao **pedido por telefone**: se a ligação caiu depois de você fazer o pedido, ligar de novo pode gerar **dois pedidos**, a menos que você dê um **número de protocolo** (a chave de idempotência) e a empresa reconheça “esse pedido eu já anotei”. E se a empresa está claramente fora do ar, **pare de ligar por um tempo** (disjuntor).

## 🔬 Como funciona por dentro
- **`httpx`**: cliente HTTP moderno do Python, com a **mesma API** em modo síncrono (`httpx.Client`) e assíncrono (`httpx.AsyncClient`), HTTP/1.1 e (opcional) HTTP/2, `timeout` por padrão (5 s), e transportes plugáveis (inclusive de teste). Substitui o `requests` quando se quer `async` e *timeouts* seguros por padrão.
- **`Client` × funções de módulo:** `httpx.get(...)` abre e fecha uma conexão **a cada chamada**; o **`Client`** mantém um *pool* de conexões (**keep-alive**) e reaproveita TCP/TLS. Em produção, **sempre** um `Client` compartilhado (e fechado no fim), nunca um por requisição.
- **Os quatro timeouts** (`httpx.Timeout(5, read=0.5)`):
  | Timeout | Limita | Exceção |
  |---|---|---|
  | `connect` | abrir a conexão TCP/TLS | `ConnectTimeout` |
  | `read` | **esperar** o próximo pedaço da resposta | `ReadTimeout` |
  | `write` | enviar o corpo | `WriteTimeout` |
  | `pool` | esperar uma conexão livre do *pool* | `PoolTimeout` |
  Importante: `read` mede a espera **entre bytes**, não o tempo total; para um limite do **total**, use `asyncio.timeout` (aula 03) ou o orçamento do pedido todo.
- **Exceções:** `HTTPError` → `RequestError` → `TransportError` → (`TimeoutException`, `NetworkError`/`ConnectError`…); e `HTTPStatusError` (levantada por `raise_for_status()`). **Um status 4xx/5xx não levanta nada sozinho**: você decide se é erro.
- **O que repetir (e o que não):**
  | Situação | Repetir? |
  |---|---|
  | falha de **conexão**, *timeout*, `502/503/504` | **sim** (transitório), com *backoff* |
  | `429` | **sim**, esperando o `Retry-After` |
  | `500` | talvez (pode ser *bug* permanente) |
  | `400/401/403/404/422` | **não** (o pedido está errado; repetir não conserta) |
  | método **não idempotente** (`POST`) | **só com chave de idempotência** (aula 6.13) |
- **Backoff exponencial com *jitter*:** esperar `base × 2^n` (0,2 s, 0,4 s, 0,8 s…) com um **teto**, multiplicado por um aleatório (*full jitter*) para que milhares de clientes **não retomem no mesmo instante** e derrubem o serviço que acabou de se recuperar (*thundering herd*). O servidor pode mandar a **hora certa** em `Retry-After`: obedeça-o.
- **`HTTPTransport(retries=N)`**: o `httpx` repete **apenas falhas de conexão** (`ConnectError`, `ConnectTimeout`), nunca respostas `5xx`/`429`. Retentativas de status são **responsabilidade sua** (ou de uma biblioteca como a `tenacity`).
- **Orçamento de tempo:** some os *timeouts* e as esperas. Três tentativas de 5 s com esperas de 1 s significam **17 s** de *worker* parado; num servidor web isso derruba a vazão (aula 01). Por isso chamadas lentas e repetíveis **saem da requisição** e vão para uma **fila** (aulas 06 e 07).
- **Disjuntor (*circuit breaker*):** depois de `N` falhas seguidas, **pare de chamar** o serviço por um tempo (“aberto”), falhando **rápido**; depois deixa passar **uma** chamada de teste (“meio-aberto”) e, se der certo, volta ao normal. Evita acumular chamadas lentas numa dependência morta e dá fôlego a ela.
- **Testar sem rede:** `httpx.MockTransport(funcao)` recebe a requisição e devolve uma resposta falsa; o seu código roda **inalterado**, rápido e **determinístico**. É a base dos testes das aulas 07 e 09.
- **Concorrência de chamadas:** `AsyncClient` + `gather` sobrepõe as esperas; `httpx.Limits(max_connections=N)` e `asyncio.Semaphore` evitam **sobrecarregar** o outro lado (e esgotar a sua máquina).

## 🛠️ Exemplo prático
**0. A “API externa” de mentira** (`servidor_externo.py`, só biblioteca padrão; usada em todos os exemplos)
```python
"""Uma 'API externa' de mentira, com os defeitos de uma real: lenta, instável, com limite de taxa e que trava."""
import json
import threading
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ESTADO = {"conexoes": 0, "pedidos": Counter(), "lock": threading.Lock(), "criados": 0, "chaves": {}, "perde_resposta": True}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"                         # keep-alive: a conexão pode ser reaproveitada

    def setup(self):
        super().setup()
        with ESTADO["lock"]:
            ESTADO["conexoes"] += 1                       # uma conexão TCP nova chegou

    def log_message(self, *a):
        pass

    def _responder(self, status, corpo, extra=None):
        dados = json.dumps(corpo).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        chave = q.get("k", "padrao")
        with ESTADO["lock"]:
            ESTADO["pedidos"][(url.path, chave)] += 1
            n = ESTADO["pedidos"][(url.path, chave)]
        if url.path == "/ok":
            return self._responder(200, {"ok": True})
        if url.path == "/lento":                          # demora `ms` milissegundos
            time.sleep(int(q.get("ms", 500)) / 1000)
            return self._responder(200, {"ok": True})
        if url.path == "/instavel":                       # falha com 503 nas primeiras `falhas` chamadas
            if n <= int(q.get("falhas", 2)):
                return self._responder(503, {"erro": "indisponível"})
            return self._responder(200, {"ok": True, "tentativa": n})
        if url.path == "/limite":                         # 429 com Retry-After na primeira chamada
            if n == 1:
                return self._responder(429, {"erro": "calma"}, {"Retry-After": "1"})
            return self._responder(200, {"ok": True, "tentativa": n})
        if url.path == "/trava":                          # aceita e nunca responde (até 10 s)
            time.sleep(10)
            return self._responder(200, {"ok": True})
        return self._responder(404, {"erro": "não existe"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(n)
        chave = self.headers.get("Idempotency-Key")
        with ESTADO["lock"]:
            if chave and chave in ESTADO["chaves"]:                        # repetição da mesma intenção: devolve o que já foi criado
                return self._responder(201, {"id": ESTADO["chaves"][chave], "replayed": True})
            ESTADO["criados"] += 1                                         # o EFEITO COLATERAL acontece aqui
            novo = ESTADO["criados"]
            if chave:
                ESTADO["chaves"][chave] = novo
            primeira = novo == 1 or (chave is None and novo == 1)
        if ESTADO["perde_resposta"] and ESTADO["criados"] == 1:
            return self._responder(503, {"erro": "indisponível"})          # criou, mas a RESPOSTA falhou (o pior caso)
        return self._responder(201, {"id": novo})


class Servidor(ThreadingHTTPServer):
    request_queue_size = 256                              # o padrão (5) faria conexões simultâneas esperarem ~1 s de retransmissão
    daemon_threads = True


def iniciar():
    srv = Servidor(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}"
```
Endpoints: `/ok` (rápido), `/lento?ms=` (demora), `/instavel?falhas=N` (devolve `503` nas N primeiras chamadas), `/limite` (`429` com `Retry-After: 1` na primeira), `/trava` (não responde) e `POST /pedidos` (cria, **mas na primeira vez perde a resposta**: o pior caso, “criei e não consegui avisar”). Observação: foi preciso aumentar `request_queue_size` (o padrão, 5, faz conexões simultâneas esperarem ~1 s de retransmissão e distorce a medição), um lembrete de que **o outro lado também tem limites**.

**1. `Client`, timeouts e erros** (`hx1.py`)
```python
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
```
```bash
uv add httpx && uv run python hx1.py
```
```text
--- 1) Client reaproveita a conexão (keep-alive)
10 × httpx.get(...)         → conexões TCP abertas no servidor: 10
10 × client.get(...)        → conexões TCP abertas no servidor: 1

--- 2) timeouts: connect / read / write / pool
timeout padrão do httpx: Timeout(timeout=5.0)
read=0,5 s numa resposta de 2 s → ReadTimeout
porta fechada → ConnectError: [Errno 111] Connection refused
servidor que 'trava' →  ReadTimeout (é subclasse de TimeoutException)

--- 3) status de erro NÃO levanta exceção sozinho
status: 503 | is_success: False | is_server_error: True
raise_for_status() → HTTPStatusError | resposta: 503
404: 404 {'erro': 'não existe'}

--- 4) a hierarquia de exceções (as que você vai tratar)
  ConnectTimeout     ← TimeoutException ← TransportError ← RequestError ← HTTPError ← Exception
  ReadTimeout        ← TimeoutException ← TransportError ← RequestError ← HTTPError ← Exception
  ConnectError       ← NetworkError ← TransportError ← RequestError ← HTTPError ← Exception
  HTTPStatusError    ← HTTPError ← Exception
```
- **Dez** chamadas com `httpx.get` abriram **dez conexões TCP**; dez com um `Client` abriram **uma**. Em HTTPS a diferença inclui o *handshake* TLS de cada conexão: é o custo que o `Client` economiza.
- O timeout padrão é de **5 s para tudo**; um `ReadTimeout` de 0,5 s cortou a resposta lenta e outro cortou o servidor que “trava”.
- **Porta fechada** dá `ConnectError` na hora (*Connection refused*); um servidor que não responde dá `ReadTimeout`: dois problemas diferentes, mesma regra: **sempre ter timeout**.
- Um `503` **não** levantou exceção: `r.status_code == 503` e `raise_for_status()` o converte em `HTTPStatusError`. Decida conscientemente.

**2. Retentativas: o que o httpx faz, o que é com você, e o perigo do `POST`** (`hx2.py`)
```python
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
```
```bash
uv run python hx2.py
```
```text
--- 1) httpx.HTTPTransport(retries=N) só repete falhas de CONEXÃO
servidor subiu 0,6 s depois; com retries=3 → 200 em 1.52 s
mas um 503 NÃO é repetido pelo transporte → status 503

--- 2) com_retry: backoff exponencial com jitter, Retry-After e só métodos repetíveis
GET instável (2 falhas, depois ok) → 200 após esperas [0.06, 0.06] (valores simulados, sem dormir)
GET com 429 + Retry-After: 1       → 200 após esperas [1.0] (obedeceu o servidor)
GET que nunca melhora              → 503 após esperas [0.13, 0.03, 0.43] (desistiu após 4 tentativas)
GET 404                            → 404 esperas [] (erro do cliente não é repetido)

--- 3) repetir um POST SEM idempotência duplica o efeito
POST sem chave: o código não repete → status 503, criados no servidor: 1 (mas o cliente nem sabe se criou)
POST repetido na mão, sem chave   → status final 201, criados no servidor: 2  ← DUPLICADO
POST com Idempotency-Key           → status 201 {'id': 1, 'replayed': True}, criados no servidor: 1  ← UM só
```
Como ler:
- **(1)** Com o servidor subindo 0,6 s depois, `retries=3` conseguiu **200** (o transporte repetiu a conexão recusada). Mas o `503` do `/instavel` **não** foi repetido: o transporte só cuida da conexão.
- **(2)** `com_retry` repetiu o `503` duas vezes com esperas pequenas e aleatórias (o *jitter*; aqui simuladas sem dormir de verdade e com semente fixa para o resultado ser reproduzível), **obedeceu o `Retry-After: 1`** do `429` (espera exata de 1,0 s, sem jitter), **desistiu** de um serviço que nunca melhora após 4 tentativas e **não repetiu** o `404`.
- **(3)** O caso que justifica a aula 6.13: o servidor **criou** o recurso, mas a resposta falhou. Sem chave, o cliente que repete cria **dois** (“criados no servidor: 2”); com `Idempotency-Key`, o servidor reconhece a **mesma intenção** e devolve o que já criou (`replayed: True`): **um só**. Observe também que `com_retry` **recusou repetir o `POST` sem chave** (só repete métodos seguros ou `POST` com a chave).

**3. `AsyncClient`, limites e `MockTransport`** (`hx3.py`)
```python
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
```
```bash
uv run python hx3.py
```
```text
20 GET de 0,3 s com httpx.Client (sequencial)                   6.82 s
20 GET de 0,3 s com AsyncClient + gather (20 ok)                0.34 s
o mesmo, com Limits(max_connections=5)  → 4 rodadas de 0,3 s    1.34 s
max_connections=1 e pool=0,2 s → PoolTimeout em quem espera uma vaga: ['Response', 'PoolTimeout', 'PoolTimeout']

--- falhas parciais: uma chamada falha e as outras seguem
  /ok                        → 200
  /lento?ms=2000             → ReadTimeout
  /instavel?falhas=9&k=z     → 503
  /ok                        → 200

--- MockTransport: testar o código que chama a API SEM rede
pedido 3  → 30
pedido 13 → HTTPStatusError 503 (nenhuma conexão de rede foi aberta)
```
- Vinte chamadas de ≈ 0,3 s levaram **≈ 7 s em sequência** e **≈ 0,35 s** com `AsyncClient` + `gather` (≈ 20× mais rápido): a mesma lição da aula 03, agora com HTTP de verdade. (O sequencial passa um pouco de 6 s por causa do custo de cada requisição no servidor de teste.)
- `Limits(max_connections=5)` transformou as 20 chamadas em **4 rodadas** (≈ 1,3 s): **proteção** contra sobrecarregar o serviço do outro lado. Com `max_connections=1` e `pool=0,2`, quem não conseguiu uma vaga levou **`PoolTimeout`**: o *timeout* de *pool* existe para você notar quando seu próprio limite virou gargalo.
- Com `return_exceptions=True`, uma chamada que falhou (timeout, 503) **não derrubou** as outras: cada resultado é uma resposta **ou** uma exceção.
- **`MockTransport`**: o código de consulta foi testado **sem abrir uma conexão de rede**, inclusive o caminho do erro `503`. É assim que se testa integração HTTP em CI.

**4. Disjuntor** (`breaker.py`, relógio controlado para não esperar de verdade)
```python
class DisjuntorAberto(Exception):
    pass


class Disjuntor:
    """Circuit breaker: depois de N falhas seguidas, para de chamar o serviço por um tempo (fail fast)."""

    def __init__(self, limite=3, recuperacao=10, relogio=None):
        self.limite, self.recuperacao, self.relogio = limite, recuperacao, relogio
        self.falhas, self.aberto_em, self.estado = 0, None, "fechado"

    def chamar(self, fn):
        if self.estado == "aberto":
            if self.relogio() - self.aberto_em < self.recuperacao:
                raise DisjuntorAberto("serviço fora do ar: nem tentei")          # não gasta tempo nem a conexão
            self.estado = "meio-aberto"                                           # deixa passar UMA chamada de teste
        try:
            r = fn()
        except Exception:
            self.falhas += 1
            if self.estado == "meio-aberto" or self.falhas >= self.limite:
                self.estado, self.aberto_em = "aberto", self.relogio()
            raise
        self.falhas, self.estado = 0, "fechado"
        return r


t = [0.0]
saudavel = [False]
chamadas_reais = [0]


def servico():
    chamadas_reais[0] += 1
    if not saudavel[0]:
        raise ConnectionError("503")
    return "ok"


d = Disjuntor(limite=3, recuperacao=10, relogio=lambda: t[0])
for i in range(1, 9):
    try:
        resp = d.chamar(servico)
    except DisjuntorAberto as e:
        resp = f"BLOQUEADA ({e})"
    except ConnectionError:
        resp = "falhou"
    print(f"t={t[0]:4.1f} chamada {i}: {resp:<44} estado={d.estado:<11} chamadas reais ao serviço={chamadas_reais[0]}")
    t[0] += 1
t[0] = 12; saudavel[0] = True
print("--- o serviço voltou e passaram 10 s")
for i in (9, 10):
    resp = d.chamar(servico)
    print(f"t={t[0]:4.1f} chamada {i}: {resp:<44} estado={d.estado:<11} chamadas reais ao serviço={chamadas_reais[0]}")
```
```bash
python3 breaker.py
```
```text
t= 0.0 chamada 1: falhou                                       estado=fechado     chamadas reais ao serviço=1
t= 1.0 chamada 2: falhou                                       estado=fechado     chamadas reais ao serviço=2
t= 2.0 chamada 3: falhou                                       estado=aberto      chamadas reais ao serviço=3
t= 3.0 chamada 4: BLOQUEADA (serviço fora do ar: nem tentei)   estado=aberto      chamadas reais ao serviço=3
t= 4.0 chamada 5: BLOQUEADA (serviço fora do ar: nem tentei)   estado=aberto      chamadas reais ao serviço=3
t= 5.0 chamada 6: BLOQUEADA (serviço fora do ar: nem tentei)   estado=aberto      chamadas reais ao serviço=3
t= 6.0 chamada 7: BLOQUEADA (serviço fora do ar: nem tentei)   estado=aberto      chamadas reais ao serviço=3
t= 7.0 chamada 8: BLOQUEADA (serviço fora do ar: nem tentei)   estado=aberto      chamadas reais ao serviço=3
--- o serviço voltou e passaram 10 s
t=12.0 chamada 9: ok                                           estado=fechado     chamadas reais ao serviço=4
t=12.0 chamada 10: ok                                           estado=fechado     chamadas reais ao serviço=5
```
Depois de **3 falhas seguidas** o disjuntor **abriu**: as chamadas 4 a 8 foram **bloqueadas sem tocar no serviço** (o contador de chamadas reais ficou parado em 3), poupando conexões, *threads* e timeouts. Quando passaram os 10 s e o serviço voltou, a chamada de teste (“meio-aberto”) deu certo e ele **fechou**. Em produção use uma biblioteca madura (`pybreaker`) ou o recurso do seu *gateway*; o importante é o conceito: **falhar rápido** protege o seu sistema e o do outro.

## 🧠 Pausa para lógica
**Problema (o disjuntor, por conta própria).** Sem olhar o exemplo, escreva `Disjuntor(limite, recuperacao, relogio)` com os estados **fechado → aberto → meio-aberto**, que conte falhas **seguidas** (um sucesso zera), recuse chamadas enquanto aberto, e permita **uma** chamada de teste após o tempo de recuperação, voltando a abrir se ela falhar.

<details><summary>Dica</summary>
Guarde <code>falhas</code>, <code>aberto_em</code> e <code>estado</code>. Em <code>chamar(fn)</code>: se <code>aberto</code> e ainda não passou <code>recuperacao</code>, levante <code>DisjuntorAberto</code>; se passou, vá para <code>meio-aberto</code> e execute. Na exceção: incremente <code>falhas</code> e abra se for o <code>limite</code> ou se estava <code>meio-aberto</code>. No sucesso: zere tudo.
</details>

<details><summary>Solução comentada</summary>

A solução é o `breaker.py` do exemplo 4 (executado). Três decisões de projeto: (1) o relógio é **injetado** (`relogio=lambda: t[0]`), o que permite testar em milissegundos o que levaria minutos; (2) apenas **uma** chamada passa no estado meio-aberto, para não despejar uma multidão sobre um serviço que acabou de voltar; (3) o estado vive **em memória por processo**: com vários *workers* cada um tem o seu disjuntor (aceitável); um estado compartilhado exigiria Redis.
</details>

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| Servidor trava para sempre numa chamada externa | Sem *timeout* (em `requests` o padrão é **nenhum**) | Sempre `timeout=` (no `httpx` o padrão é 5 s; ajuste) |
| `httpx.ReadTimeout` | O servidor demorou entre bytes | Subir o `read` se for legítimo; senão tratar e repetir/falhar |
| `httpx.ConnectError: [Errno 111] Connection refused` | Serviço fora do ar / porta errada | Repetir com *backoff*, disjuntor, alerta |
| `httpx.PoolTimeout` | Todas as conexões do *pool* ocupadas | Aumentar `max_connections`, reduzir a concorrência, achar a chamada lenta |
| `RuntimeError: Cannot send a request, as the client has been closed` | Usou o `Client` depois do `with` | Cliente com vida longa e fechado no desligamento |
| Muitas conexões TCP/TLS e latência alta | Funções de módulo (`httpx.get`) em laço | Um `Client` compartilhado |
| Cobrou/criou duas vezes depois de um retry | `POST` repetido sem idempotência | `Idempotency-Key` (aula 6.13) e só repetir com ela |
| “Efeito manada” ao voltar do ar | *Backoff* sem *jitter* | Multiplicar a espera por um aleatório |
| Retentativas infinitas | Sem limite de tentativas/tempo | `tentativas` e orçamento total (`asyncio.timeout`) |
| Repetir `400`/`404` | Tratar todo erro como transitório | Repetir só `429/5xx` e falhas de rede |
| Teste de integração lento e instável | Chamadas reais em CI | `MockTransport`, `respx` ou servidor local |
| Segredo no log da requisição | `print(r.request.headers)` | Nunca registrar `Authorization`/chaves |

- **Todo cliente externo:** `Client` compartilhado, *timeouts* explícitos, **limite de concorrência**, retentativa só para transitórios e repetíveis, disjuntor se a dependência for crítica, e **log** do que falhou (sem segredos).
- **Não retente dentro de uma requisição web** além de 1 ou 2 tentativas rápidas: o cliente do **seu** servidor está esperando. Para o resto, use **fila** (aula 06) e retentativas do *worker* (aula 07).
- Prefira `tenacity` (`@retry(stop=..., wait=wait_exponential_jitter(...))`) a escrever o laço à mão em produção; o laço da aula serve para entender o que ela faz.
- Combine: **idempotência + retentativa** é o par que torna uma integração confiável.

## 🧩 Exercícios
**1. Fixação**
(a) Quais são os quatro *timeouts* do `httpx` e o que cada um limita? (b) Por que um `Client` e não `httpx.get` em laço? (c) Por que `HTTPTransport(retries=3)` não resolve um `503`? (d) Por que o jitter existe?

<details><summary>Solução</summary>

(a) `connect` (abrir a conexão), `read` (esperar dados), `write` (enviar o corpo) e `pool` (esperar uma conexão livre do *pool*). (b) O `Client` reaproveita conexões (keep-alive, TLS), `httpx.get` abre uma nova por chamada. (c) O transporte só repete falhas de **conexão**; respostas `5xx`/`429` precisam de lógica de retentativa sua. (d) Para que muitos clientes não repitam no mesmo instante, derrubando de novo o serviço recém-recuperado.
</details>

**2. Aplicação no projeto MiniShop**
Construa o cliente do antifraude do MiniShop, robusto e testável.

Critérios de pronto:
- [ ] `apps/orders/antifraude_client.py` com um `httpx.Client` (e um `AsyncClient`) compartilhado, `Timeout(connect=1, read=2, write=2, pool=1)` e `base_url` vinda de configuração (aula 5.14)
- [ ] `consultar(pedido_id)` com retentativa **só** para `429/502/503/504` e falhas de rede, *backoff* exponencial com *jitter* e `Retry-After`, no máximo 3 tentativas
- [ ] Um disjuntor em volta da chamada (abre após 5 falhas seguidas; recuperação de 30 s) e um resultado **“desconhecido”** quando aberto (o pedido segue para revisão)
- [ ] Testes com `MockTransport`: sucesso, `503` seguido de sucesso, `429` com `Retry-After`, `404` sem repetir, esgotamento das tentativas, e disjuntor abrindo
- [ ] Testes **sem dormir de verdade** (relógio e `dormir` injetados)
- [ ] Log de cada retentativa (número, motivo, espera) **sem** dados sensíveis
- [ ] Commit `feat(orders): resilient fraud-check HTTP client`

<details><summary>Solução de referência (executada: os 4 testes passam)</summary>

```python
import random
import time

import httpx

TRANSITORIOS = {429, 502, 503, 504}


class AntifraudeClient:
    def __init__(self, client: httpx.Client, dormir=None, aleatorio=random.random, tentativas=3):
        self.http, self.aleatorio, self.tentativas = client, aleatorio, tentativas
        self.dormir = dormir or time.sleep

    def consultar(self, pedido_id):
        for n in range(self.tentativas):
            try:
                r = self.http.get("/score", params={"pedido": pedido_id})
            except (httpx.ConnectError, httpx.TimeoutException):
                r = None
            if r is not None and r.status_code not in TRANSITORIOS:
                r.raise_for_status()                                  # 4xx: erro de verdade, não repete
                return r.json()["risco"]
            if n == self.tentativas - 1:
                return None                                           # "desconhecido": segue para revisão manual
            espera = float(r.headers["Retry-After"]) if r is not None and "Retry-After" in r.headers else 0.2 * 2 ** n * self.aleatorio()
            self.dormir(espera)


def test_503_depois_ok():
    respostas = iter([httpx.Response(503), httpx.Response(200, json={"risco": 12})])
    cli = AntifraudeClient(httpx.Client(base_url="http://x", transport=httpx.MockTransport(lambda req: next(respostas))), dormir=lambda s: None)
    assert cli.consultar(1) == 12


def test_429_respeita_retry_after():
    esperas = []
    respostas = iter([httpx.Response(429, headers={"Retry-After": "2"}), httpx.Response(200, json={"risco": 5})])
    cli = AntifraudeClient(httpx.Client(base_url="http://x", transport=httpx.MockTransport(lambda r: next(respostas))), dormir=esperas.append)
    assert cli.consultar(1) == 5 and esperas == [2.0]


def test_esgota_e_devolve_desconhecido():
    cli = AntifraudeClient(httpx.Client(base_url="http://x", transport=httpx.MockTransport(lambda r: httpx.Response(503))), dormir=lambda s: None)
    assert cli.consultar(1) is None


def test_404_nao_repete():
    chamadas = []
    def h(r):
        chamadas.append(1); return httpx.Response(404)
    cli = AntifraudeClient(httpx.Client(base_url="http://x", transport=httpx.MockTransport(h)), dormir=lambda s: None)
    try:
        cli.consultar(1)
    except httpx.HTTPStatusError:
        pass
    assert len(chamadas) == 1


if __name__ == "__main__":
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            fn(); print("ok", nome)
```
```text
ok test_503_depois_ok
ok test_429_respeita_retry_after
ok test_esgota_e_devolve_desconhecido
ok test_404_nao_repete
```
</details>

**3. Desafio (opcional)**
Troque o laço escrito à mão pela biblioteca `tenacity` (`retry`, `stop_after_attempt`, `wait_exponential_jitter`, `retry_if_exception_type`) e compare o código e os testes. Depois acrescente um **orçamento total de tempo** (`stop_after_delay`) e mostre que nenhuma chamada ultrapassa 5 s no pior caso.

## 🎤 Na entrevista
- **Por que sempre definir *timeout* em chamadas externas?** Sem ele, um serviço lento ou travado prende o *worker* indefinidamente e derruba a vazão do seu servidor; *timeouts* (conexão e leitura) limitam o dano e permitem falhar rápido.
- **Como implementar retentativas de forma segura?** Repetir só erros transitórios (rede, `429`, `502/503/504`) e métodos idempotentes (ou `POST` com chave de idempotência), com limite de tentativas, *backoff* exponencial com *jitter*, respeitando `Retry-After`, e idealmente fora da requisição web, numa fila.
- **O que é um *circuit breaker*?** Um mecanismo que, depois de várias falhas seguidas, para de chamar o serviço por um período (falhando rápido), testa com uma chamada e só então volta ao normal; protege o seu sistema e dá folga ao serviço doente.
- **`httpx.Client` ou `httpx.get`?** `Client` (ou `AsyncClient`): reaproveita conexões e configurações, reduzindo latência e custo de TLS; funções de módulo só para *scripts* rápidos.
- **Como testar código que chama uma API externa?** Sem rede: `MockTransport`/`respx` para simular respostas e falhas, relógio e `sleep` injetados para os testes não esperarem.

## 📚 Para ir além
- 📄 Documentação: [HTTPX](https://www.python-httpx.org/). Visão geral e comparação com `requests`.
- 📄 Documentação: [HTTPX — Timeouts](https://www.python-httpx.org/advanced/timeouts/). Os quatro *timeouts* e as exceções.
- 📄 Documentação: [HTTPX — Clientes](https://www.python-httpx.org/advanced/clients/). `Client`, *pool* e reutilização de conexão.
- 📄 Documentação: [HTTPX — Transportes](https://www.python-httpx.org/advanced/transports/). `HTTPTransport(retries=)` e `MockTransport`.
- 📄 Documentação: [HTTPX — Async](https://www.python-httpx.org/async/). `AsyncClient` e `gather`.
- 📄 Documentação: [HTTPX — Limites de recursos](https://www.python-httpx.org/advanced/resource-limits/). `Limits(max_connections=...)`.
- 📄 Documentação: [Tenacity](https://tenacity.readthedocs.io/). Retentativas declarativas (`wait_exponential_jitter`).
- 📑 Artigo/tutorial: [AWS Builders' Library — Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/). A referência sobre o assunto (em inglês).
- 📑 Artigo/tutorial: [Martin Fowler — Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html). O padrão explicado (em inglês).
- 📄 Referência: [`Retry-After` (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Reference/Headers/Retry-After). Formato do cabeçalho.
- 🏋️ Prática extra: mude o `read` do exemplo 1 para 3 s e observe o que muda no `/lento?ms=2000` e no `/trava`.

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Usei `Client` compartilhado e vi a diferença de conexões
- [ ] Defini e provoquei `ConnectError`, `ReadTimeout` e `PoolTimeout`
- [ ] Escrevi retentativa com *backoff*, *jitter* e `Retry-After`, só para o que é repetível
- [ ] Vi o `POST` duplicar sem chave e não duplicar com `Idempotency-Key`
- [ ] Testei código HTTP sem rede (`MockTransport`) e entendi o disjuntor
