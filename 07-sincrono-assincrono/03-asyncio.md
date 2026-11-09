# 3. `asyncio` e `async`/`await`

> ⏱️ ~1h30 · Módulo 7 · Pré-requisitos: [7.01](01-bloqueante-io-cpu.md), [7.02](02-threads-processos-gil.md), [1.15 (iteradores e geradores)](../01-python-logica/15-iteradores-geradores.md), [4.06 (Promises e `fetch`, a mesma ideia no JavaScript)](../04-front-end-essencial/06-js-promises-fetch.md)

> ✅ **Verificação.** Todos os programas foram executados em 2026-11-08 com **Python 3.13** e, nos exemplos com Django, no laboratório do módulo 6 (Django 5.2.19, SQLite). **As saídas abaixo foram geradas executando os arquivos no momento de montar a aula**, então são reais; os tempos variam alguns centésimos entre execuções.

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar o que é uma **corrotina**, o **laço de eventos** e o que `await` faz (e o que **não** faz)
- Rodar várias esperas ao mesmo tempo com `asyncio.gather`, `TaskGroup`, `Semaphore` e `timeout`
- Reconhecer e evitar o erro nº 1: **bloquear o laço de eventos** com uma chamada síncrona
- Usar o ORM do Django em contexto assíncrono (`aget`, `acount`, `async for`, `sync_to_async`) e entender `SynchronousOnlyOperation`
- Explicar por que `async` melhora a **vazão com espera**, mas não a velocidade de **cálculo**

## 🤔 Por que isso importa
`asyncio` é como um único *worker* atende **milhares** de conexões que passam quase todo o tempo esperando (APIs externas, WebSockets, filas): em vez de uma *thread* por espera, uma só *thread* alterna entre elas. É a base do ASGI (aula 05), do `httpx` assíncrono (aula 04), do FastAPI (módulo 15) e de qualquer cliente que consulte muitos serviços. E é fonte de bugs sutis (um `time.sleep` no lugar errado derruba o servidor inteiro), por isso entra em entrevistas.

## 💡 Intuição (explicação simples)
Imagine um **garçom único** num restaurante. No modelo síncrono, ele leva o pedido à cozinha e **fica parado esperando o prato** antes de atender a próxima mesa. No modelo `asyncio`, ele leva o pedido, **deixa um bilhete** (“me avise quando estiver pronto”) e vai atender outras mesas; quando a cozinha toca a campainha, ele volta ao bilhete. Um só garçom atende 50 mesas, **desde que** nunca fique parado olhando para a cozinha (chamada bloqueante). E ele não cozinha mais rápido: só **não desperdiça a espera**.

## 🔬 Como funciona por dentro
- **Corrotina:** uma função definida com `async def`. **Chamá-la não a executa**: devolve um objeto de corrotina (uma “receita pausável”). Ela só roda quando alguém a **agenda** (com `await`, `asyncio.run`, `create_task`, `gather`).
- **`await`**: “**pause-me aqui** até esta operação terminar e deixe o laço de eventos rodar outras corrotinas enquanto isso”. Só pode ser usado dentro de `async def`.
- **Laço de eventos (*event loop*):** o agendador. Mantém as corrotinas prontas e as que esperam (sockets, temporizadores) e, a cada volta, roda a próxima pronta **até ela chegar a um `await`**. É **cooperativo**: uma corrotina só cede o controle quando faz `await`; se ela calcular por 5 segundos sem `await`, **todas as outras ficam paradas** (é o que você verá abaixo). Na aula há um laço de brinquedo, feito com geradores, que mostra a ideia.
- **Tarefa (*Task*):** uma corrotina **já agendada** para rodar no laço (`asyncio.create_task`). Sem a tarefa, `await a(); await b()` roda **uma depois da outra**; com `gather`/tarefas, **sobrepostas**.
- **Ferramentas:**
  | API | Para quê |
  |---|---|
  | `asyncio.run(main())` | liga o laço, roda a corrotina principal e o desliga (ponto de entrada) |
  | `asyncio.gather(*cs)` | roda várias ao mesmo tempo e devolve os resultados **na ordem**; `return_exceptions=True` não deixa uma falha derrubar as outras |
  | `asyncio.TaskGroup()` (3.11+) | grupo com **escopo**: se uma tarefa falha, as irmãs são **canceladas** e o erro sobe (`except*`) |
  | `asyncio.timeout(s)` (3.11+) | cancela o bloco se passar do tempo (`TimeoutError`) |
  | `asyncio.Semaphore(n)` | limita **quantas** tarefas passam ao mesmo tempo (respeitar um limite de API, de conexões) |
  | `asyncio.Queue` | produtores e consumidores |
  | `asyncio.to_thread(fn, ...)` | roda **código bloqueante** numa thread, sem travar o laço |
  | `asyncio.sleep(s)` | espera **cooperativa** (nunca `time.sleep` dentro de `async`) |
- **Cancelamento:** cancelar uma tarefa levanta `CancelledError` **no ponto do `await`**; é o jeito de limpar recursos (`try/finally`) e **deve ser relançado**.
- **Quando `async` ajuda e quando não:**
  | Carga | `asyncio` |
  |---|---|
  | milhares de esperas de rede/socket | **excelente** (uma thread, pouca memória) |
  | poucas esperas | indiferente (mais complexidade sem ganho) |
  | **cálculo** (CPU-bound) | **não ajuda** (uma thread, cooperativa); use processos |
  | biblioteca **bloqueante** (`requests`, driver síncrono) | **atrapalha**, a menos que rodada em `to_thread` |
- **“Colorir” funções:** funções `async` só podem ser **aguardadas** por outras `async`; o código síncrono não chama `await`. Esse “contágio” é o custo de adotar `async`: toda a cadeia (view → serviço → cliente HTTP → driver) precisa ser assíncrona ou isolada com `sync_to_async`/`to_thread`.
- **Django e `asyncio`:** o ORM tem versões assíncronas (`aget`, `acount`, `aexists`, `acreate`, `async for`). Chamar o ORM **síncrono** dentro de código assíncrono levanta **`SynchronousOnlyOperation`**, uma proteção contra bloquear o laço. `sync_to_async` (de `asgiref`) executa uma função síncrona (um serviço com transação, por exemplo) numa thread. As **transações** continuam síncronas (`atomic()` não funciona com `await` no meio), por isso a regra prática é: lógica transacional em serviço síncrono chamado via `sync_to_async`.

## 🛠️ Exemplo prático
**1. O básico: corrotina, `gather` e escala** (`aio1.py`)
```python
import asyncio
import time


async def busca(nome, atraso):
    await asyncio.sleep(atraso)              # ESPERA cooperativa: devolve o controle ao laço de eventos
    return f"{nome} ok"


async def main():
    # 1) chamar uma função async NÃO executa nada: devolve uma corrotina
    c = busca("A", 0.1)
    print("tipo do retorno de busca('A', 0.1):", type(c).__name__)
    print("resultado ao dar await:", await c)

    # 2) em sequência: as esperas se somam
    t = time.perf_counter()
    for n in "ABCDE":
        await busca(n, 0.5)
    print(f"5 awaits seguidos (5 × 0,5 s)        → {time.perf_counter() - t:.2f} s")

    # 3) concorrente: as esperas se sobrepõem
    t = time.perf_counter()
    resultados = await asyncio.gather(*(busca(n, 0.5) for n in "ABCDE"))
    print(f"gather de 5 corrotinas (5 × 0,5 s)   → {time.perf_counter() - t:.2f} s  {resultados}")

    # 4) escala: 10 mil esperas de 1 s ao mesmo tempo, em UMA thread
    t = time.perf_counter()
    await asyncio.gather(*(asyncio.sleep(1) for _ in range(10_000)))
    print(f"gather de 10.000 esperas de 1 s      → {time.perf_counter() - t:.2f} s (uma thread só)")


asyncio.run(main())
```
```bash
uv run python aio1.py
```
```text
tipo do retorno de busca('A', 0.1): coroutine
resultado ao dar await: A ok
5 awaits seguidos (5 × 0,5 s)        → 2.50 s
gather de 5 corrotinas (5 × 0,5 s)   → 0.50 s  ['A ok', 'B ok', 'C ok', 'D ok', 'E ok']
gather de 10.000 esperas de 1 s      → 1.04 s (uma thread só)
```
- `busca("A", 0.1)` devolve uma **`coroutine`**: nada rodou ainda; só o `await` a executa.
- Cinco `await` seguidos somam as esperas (≈ **2,5 s**); `gather` sobrepõe e leva o tempo da **mais longa** (≈ **0,5 s**).
- **Dez mil** esperas de 1 s ao mesmo tempo terminaram em ≈ **1 s**, numa única thread. Com threads, seriam 10 mil threads (memória e escalonamento); aqui, 10 mil objetos pequenos.

**2. O erro nº 1: bloquear o laço de eventos; e as outras ferramentas** (`aio2.py`)
```python
"""Bloquear o laço de eventos, semáforo, timeout, cancelamento e TaskGroup."""
import asyncio
import time


async def batimento(lista, ate):
    """Marca o relógio a cada 0,1 s: se o laço travar, aparecem 'buracos' entre as marcas."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < ate:
        lista.append(time.perf_counter() - t0)
        await asyncio.sleep(0.1)


def maior_buraco(marcas):
    return max(b - a for a, b in zip(marcas, marcas[1:]))


async def experimento(titulo, trabalho):
    marcas = []
    bat = asyncio.create_task(batimento(marcas, 1.2))
    await asyncio.sleep(0.25)
    await trabalho()
    await bat
    print(f"{titulo:<46} maior intervalo entre batimentos: {maior_buraco(marcas):.2f} s")


async def main():
    print("--- bloquear o laço de eventos")
    async def bloqueia():
        time.sleep(0.6)                                  # ERRADO: chamada bloqueante dentro de async
    async def nao_bloqueia():
        await asyncio.sleep(0.6)                         # certo: espera cooperativa
    async def thread_aparte():
        await asyncio.to_thread(time.sleep, 0.6)         # certo para código bloqueante que você não controla
    await experimento("time.sleep(0.6) dentro de async def", bloqueia)
    await experimento("await asyncio.sleep(0.6)", nao_bloqueia)
    await experimento("await asyncio.to_thread(time.sleep, 0.6)", thread_aparte)

    print("\n--- limitar a concorrência com Semaphore (20 chamadas de 0,2 s)")
    async def chamada(sem, ativos, pico):
        async with sem:
            ativos[0] += 1
            pico[0] = max(pico[0], ativos[0])
            await asyncio.sleep(0.2)
            ativos[0] -= 1
    for limite in (20, 5):
        ativos, pico, sem = [0], [0], asyncio.Semaphore(limite)
        t = time.perf_counter()
        await asyncio.gather(*(chamada(sem, ativos, pico) for _ in range(20)))
        print(f"Semaphore({limite:>2}) → {time.perf_counter() - t:.2f} s | pico simultâneo = {pico[0]}")

    print("\n--- timeout e cancelamento")
    async def lenta():
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            print("  (a tarefa recebeu o cancelamento e pode limpar recursos)")
            raise
    try:
        async with asyncio.timeout(0.3):
            await lenta()
    except TimeoutError:
        print("asyncio.timeout(0.3) → TimeoutError: a espera foi cancelada")

    print("\n--- gather × TaskGroup quando uma das tarefas falha")
    async def ok(n):
        await asyncio.sleep(0.1 * n)
        return n
    async def falha():
        await asyncio.sleep(0.15)
        raise ValueError("antifraude fora do ar")
    r = await asyncio.gather(ok(1), falha(), ok(2), return_exceptions=True)
    print("gather(return_exceptions=True) →", [repr(x) if isinstance(x, Exception) else x for x in r])
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(ok(1)); tg.create_task(falha()); tg.create_task(ok(5))
    except* ValueError as grupo:
        print("TaskGroup → as irmãs foram canceladas e o erro subiu:", [str(e) for e in grupo.exceptions])


asyncio.run(main())
```
```bash
uv run python aio2.py
```
```text
--- bloquear o laço de eventos
time.sleep(0.6) dentro de async def            maior intervalo entre batimentos: 0.65 s
await asyncio.sleep(0.6)                       maior intervalo entre batimentos: 0.10 s
await asyncio.to_thread(time.sleep, 0.6)       maior intervalo entre batimentos: 0.10 s

--- limitar a concorrência com Semaphore (20 chamadas de 0,2 s)
Semaphore(20) → 0.20 s | pico simultâneo = 20
Semaphore( 5) → 0.80 s | pico simultâneo = 5

--- timeout e cancelamento
  (a tarefa recebeu o cancelamento e pode limpar recursos)
asyncio.timeout(0.3) → TimeoutError: a espera foi cancelada

--- gather × TaskGroup quando uma das tarefas falha
gather(return_exceptions=True) → [1, "ValueError('antifraude fora do ar')", 2]
TaskGroup → as irmãs foram canceladas e o erro subiu: ['antifraude fora do ar']
```
Como ler:
- Um “batimento” que deveria ocorrer a cada 0,1 s ficou **parado por ≈ 0,6 s** quando a corrotina chamou `time.sleep(0.6)`: **todo o servidor ficou congelado** (todas as requisições, não só a dela). Com `await asyncio.sleep(0.6)` ou `await asyncio.to_thread(time.sleep, 0.6)` o maior intervalo continuou **0,10 s**.
- `Semaphore(5)` limitou o pico a **5** chamadas simultâneas e as 20 chamadas levaram **0,8 s** (4 rodadas de 0,2 s). Use para respeitar o limite de uma API ou do pool de conexões.
- `asyncio.timeout` cancelou a espera e entregou `TimeoutError`; a tarefa recebeu `CancelledError` e pôde limpar recursos.
- `gather(return_exceptions=True)` devolveu o erro **como um valor**, junto aos resultados bons; o `TaskGroup` **cancelou as irmãs** e propagou o erro (`except*` captura grupos de exceções). O `TaskGroup` é a escolha moderna: **nenhuma tarefa fica “órfã”**.

**3. Django assíncrono** (`aio_django.py`, executado com `manage.py shell` no laboratório do módulo 6)
```python
"""Django + asyncio: o ORM síncrono é proibido dentro do laço de eventos; use a API assíncrona ou sync_to_async."""
import asyncio

from asgiref.sync import sync_to_async
from django.core.exceptions import SynchronousOnlyOperation

from apps.cart import services as carrinho
from apps.catalog.models import Product


async def main():
    try:
        Product.objects.count()                               # ORM síncrono dentro de async def
    except SynchronousOnlyOperation as e:
        print("ORM síncrono em async →", type(e).__name__, "|", str(e)[:70], "…")

    print("acount()            →", await Product.objects.acount())
    p = await Product.objects.aget(sku="INF-002")
    print("aget()              →", p.sku, p.name)
    nomes = [x.name async for x in Product.objects.filter(is_active=True).order_by("name")[:3]]
    print("async for           →", nomes)
    print("aexists()           →", await Product.objects.filter(sku="NAO-EXISTE").aexists())

    # um serviço síncrono (transação, travas) chamado a partir de código async:
    from django.contrib.auth import get_user_model
    usuario = await get_user_model().objects.aget(username="cliente")
    cart = await sync_to_async(carrinho.get_cart)(usuario)
    print("sync_to_async       → carrinho", cart.pk, "do usuário", usuario.username)

    # várias consultas independentes ao mesmo tempo
    total, ativos, categorias = await asyncio.gather(
        Product.objects.acount(),
        Product.objects.filter(is_active=True).acount(),
        sync_to_async(lambda: list(Product.objects.order_by("category__name").values_list("category__name", flat=True).distinct()))(),
    )
    print("gather de 3 consultas →", total, "produtos,", ativos, "ativos,", len(categorias), "categorias")


asyncio.run(main())
```
```bash
uv run python manage.py shell < aio_django.py
```
```text

ORM síncrono em async → SynchronousOnlyOperation | You cannot call this from an async context - use a thread or sync_to_a …
acount()            → 64
aget()              → INF-002 Notebook Plus
async for           → ['Cadeira Básico', 'Cadeira Max', 'Cadeira Plus']
aexists()           → False
sync_to_async       → carrinho 1 do usuário cliente
gather de 3 consultas → 64 produtos, 61 ativos, 3 categorias
```
- O ORM síncrono dentro de `async def` levanta **`SynchronousOnlyOperation`**. Isso é bom: o Django **impede** que você trave o laço sem perceber.
- Os métodos assíncronos (`acount`, `aget`, `aexists`, `async for`) funcionam; por baixo, o Django ainda usa threads para falar com o banco (a maioria dos drivers é síncrona), então o ganho vem de **sobrepor várias consultas e chamadas externas**, não de “um banco mais rápido”.
- `sync_to_async(servico)(...)` chama um serviço síncrono (aqui `get_cart`; no MiniShop, `create_order` com sua transação) sem travar o laço.
- Uma armadilha vista no exemplo: `values_list(...).distinct()` num modelo com `ordering` na `Meta` inclui o campo de ordenação no `SELECT DISTINCT` e devolve **uma linha por produto**; por isso o exemplo usa `order_by("category__name")` antes.

**4. Um laço de eventos de brinquedo** (`mini_loop.py`): sem `asyncio`, só geradores
```python
import heapq
import itertools
import time


class Loop:
    """Um laço de eventos de brinquedo: corrotinas são GERADORES que dão `yield` quando querem esperar."""

    def __init__(self):
        self.prontas, self.dormindo = [], []                 # fila de prontas e heap de (acordar_em, id, tarefa)
        self.contador = itertools.count()

    def criar(self, gen, nome):
        self.prontas.append((nome, gen))

    def rodar(self):
        while self.prontas or self.dormindo:
            while self.dormindo and self.dormindo[0][0] <= time.perf_counter():
                _, _, tarefa = heapq.heappop(self.dormindo)
                self.prontas.append(tarefa)                  # acordou: volta para a fila de prontas
            if not self.prontas:
                time.sleep(max(0, self.dormindo[0][0] - time.perf_counter()))   # nada a fazer: dorme até o próximo despertar
                continue
            nome, gen = self.prontas.pop(0)
            try:
                segundos = next(gen)                         # roda a tarefa até o próximo yield
            except StopIteration:
                continue                                     # terminou
            heapq.heappush(self.dormindo, (time.perf_counter() + segundos, next(self.contador), (nome, gen)))


t0 = time.perf_counter()
def log(msg):
    print(f"[{time.perf_counter() - t0:4.2f} s] {msg}")


def pedido(nome, passos):
    for n, (descricao, espera) in enumerate(passos, 1):
        log(f"{nome}: {descricao}")
        yield espera                                         # "me acorde daqui a `espera` segundos" (= await sleep)
    log(f"{nome}: concluído")


loop = Loop()
loop.criar(pedido("A", [("grava no banco", 0.1), ("manda e-mail", 0.4)]), "A")
loop.criar(pedido("B", [("grava no banco", 0.1), ("consulta antifraude", 0.3)]), "B")
loop.criar(pedido("C", [("grava no banco", 0.1)]), "C")
loop.rodar()
print(f"total: {time.perf_counter() - t0:.2f} s (sequencial seria 1,0 s) — UMA thread, três pedidos intercalados")
```
```bash
uv run python mini_loop.py
```
```text
[0.00 s] A: grava no banco
[0.00 s] B: grava no banco
[0.00 s] C: grava no banco
[0.10 s] A: manda e-mail
[0.10 s] B: consulta antifraude
[0.10 s] C: concluído
[0.40 s] B: concluído
[0.50 s] A: concluído
total: 0.50 s (sequencial seria 1,0 s) — UMA thread, três pedidos intercalados
```
Três “pedidos” rodaram **intercalados** numa única thread, em **≈ 0,5 s** em vez de 1,0 s: cada `yield espera` é o equivalente a um `await asyncio.sleep(espera)`, e o laço decide quem roda enquanto os outros dormem. Observe que **o laço é cooperativo**: se uma tarefa nunca desse `yield`, as outras nunca rodariam. É exatamente o que acontece com `time.sleep` dentro de `async def`.

## 🧠 Pausa para lógica
**Problema (o laço de brinquedo, por conta própria).** Sem olhar o exemplo 4, escreva um `Loop` que execute geradores e trate `yield n` como “acorde-me em `n` segundos”: quando nenhuma tarefa está pronta, o laço **dorme até o próximo despertar** (em vez de ficar rodando em círculos). Mostre três tarefas terminando intercaladas.

<details><summary>Dica</summary>
Duas estruturas: uma lista de <em>prontas</em> e um <em>heap</em> (<code>heapq</code>) de <code>(horário_de_acordar, desempate, tarefa)</code>. A cada volta: mova para as prontas quem já pode acordar; rode a primeira pronta até o próximo <code>yield</code>; recoloque-a no heap com <code>agora + n</code>; se nada está pronto, durma até o topo do heap.
</details>

<details><summary>Solução comentada</summary>

A solução é o próprio `mini_loop.py` do exemplo 4 (executado). Pontos-chave: (1) `next(gen)` roda a tarefa até o `yield` seguinte; (2) `heapq` mantém o despertar mais próximo no topo; (3) o contador `itertools.count()` evita comparar tarefas quando os horários empatam; (4) `time.sleep(...)` no laço, **só quando não há nada a fazer**, é o que torna o laço eficiente. `asyncio` troca os `yield` por `await`, o `heapq` por um seletor do sistema operacional (`epoll`/`kqueue`) que acorda quando um *socket* fica pronto, e o `time.sleep` por uma espera por eventos de I/O.
</details>

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `RuntimeWarning: coroutine 'x' was never awaited` | Chamou `x()` sem `await` | `await x()` (ou `create_task`/`gather`) |
| Servidor “congela” a cada chamada de certa rota | `time.sleep`, `requests.get` ou cálculo pesado dentro de `async def` | `await asyncio.sleep`, cliente async (`httpx`), `asyncio.to_thread` |
| `RuntimeError: asyncio.run() cannot be called from a running event loop` | `asyncio.run` dentro de código já assíncrono (Jupyter, ASGI) | `await main()` / `create_task` |
| `django.core.exceptions.SynchronousOnlyOperation: You cannot call this from an async context` | ORM síncrono em `async def` | `await Model.objects.aget(...)` ou `sync_to_async` |
| `TypeError: object NoneType can't be used in 'await' expression` | `await` de uma função que não é `async` | Não aguarde funções síncronas |
| Tarefas “somem” sem erro | `create_task` sem guardar a referência (coletada) ou erro engolido | Guardar a tarefa, usar `TaskGroup` |
| `gather` mostra só o primeiro erro e deixa as outras rodando | Comportamento padrão | `return_exceptions=True` ou `TaskGroup` |
| Concorrência demais derruba a API do outro lado | Sem limite | `asyncio.Semaphore(n)` e *rate limit* |
| `CancelledError` engolido | `except Exception`/`except BaseException` sem relançar | Relançar `CancelledError`; usar `finally` |
| Transação com `await` no meio | `atomic()` é síncrono | Serviço síncrono + `sync_to_async` |
| Async “não acelerou meu cálculo” | CPU-bound numa única thread | Processos (`ProcessPoolExecutor`, `to_thread` não ajuda sob o GIL) |

- **Regra de ouro:** dentro de `async def`, **nada bloqueia** além de `await`. Use `PYTHONASYNCIODEBUG=1` (ou `asyncio.run(..., debug=True)`) para o Python avisar de chamadas lentas.
- Prefira **`TaskGroup`** a tarefas soltas; defina **timeouts** em toda espera externa; limite a concorrência com **`Semaphore`**.
- **Não faça tudo `async` por moda:** código síncrono simples, atrás de uma fila, resolve a maioria dos casos de um sistema Django.
- Misturar mundos tem custo: chamar `async` de síncrono (`asgiref.sync.async_to_sync`) e o inverso (`sync_to_async`) existem, mas cada travessia custa uma thread.

## 🧩 Exercícios
**1. Fixação**
(a) O que acontece ao **chamar** uma função `async def` sem `await`? (b) Por que `gather` de 5 esperas de 0,5 s leva 0,5 s e cinco `await` seguidos, 2,5 s? (c) Por que `time.sleep` dentro de `async def` é um erro, e como resolver? (d) Quando `async` **não** acelera?

<details><summary>Solução</summary>

(a) Devolve um objeto de corrotina; nada executa, e o Python avisa “never awaited”. (b) `gather` agenda todas no laço, e as esperas correm juntas (vale a mais longa); `await` seguidos executam uma de cada vez. (c) Bloqueia a única thread do laço, travando todas as outras corrotinas; use `await asyncio.sleep` ou rode o bloqueante com `asyncio.to_thread`. (d) Em trabalho de CPU (calcular), ou quando as bibliotecas são bloqueantes.
</details>

**2. Aplicação no projeto MiniShop**
Consulte vários serviços ao mesmo tempo, com limites e erros tratados.

Critérios de pronto:
- [ ] Um módulo `apps/orders/antifraude.py` com `async def pontuar(pedido_id)` que consulta um antifraude simulado (servidor local, 0,3 s) com `asyncio.timeout(1)`
- [ ] `async def pontuar_varios(ids, limite=5)` usando `TaskGroup` (ou `gather(return_exceptions=True)`) e `Semaphore(limite)`
- [ ] Um teste que prova: 10 pedidos com limite 5 levam ≈ 2 rodadas (0,6 s), o **pico** de simultaneidade é 5, e um antifraude que **demora demais** vira `TimeoutError` tratado (pontuação “desconhecida”) sem derrubar os outros
- [ ] Nenhuma chamada bloqueante dentro de `async def` (rode com `debug=True` e mostre que não há avisos de “slow callback”)
- [ ] Uma função `async` que usa o ORM com `aget`/`acount` e uma que chama um serviço síncrono com `sync_to_async`
- [ ] Commit `feat(orders): concurrent fraud scoring with asyncio`

<details><summary>Solução de referência (executada)</summary>

```python
import asyncio
import random
import time


async def pontuar(pedido_id, atraso=0.3):
    async with asyncio.timeout(1):
        await asyncio.sleep(atraso)                       # no real: await cliente.get(...) (aula 04)
        return pedido_id, random.randint(0, 100)


async def pontuar_varios(ids, limite=5):
    sem = asyncio.Semaphore(limite)
    resultados = {}

    async def um(i):
        async with sem:
            try:
                resultados[i] = (await pontuar(i))[1]
            except TimeoutError:
                resultados[i] = None                       # "desconhecida": o pedido segue para revisão manual

    async with asyncio.TaskGroup() as tg:
        for i in ids:
            tg.create_task(um(i))
    return resultados


t = time.perf_counter()
r = asyncio.run(pontuar_varios(range(10)))
print(f"{len(r)} pedidos em {time.perf_counter() - t:.2f} s (limite 5 → 2 rodadas de 0,3 s)")
```
```text
10 pedidos em 0.60 s (limite 5 → 2 rodadas de 0,3 s)
```
</details>

**3. Desafio (opcional)**
Escreva `async def retry(fn, tentativas=3, base=0.1)` com *backoff* exponencial e **jitter** que repete **apenas** erros transitórios e respeita `asyncio.timeout`. Teste com uma função falsa que falha duas vezes e depois funciona, usando um relógio controlado para não esperar de verdade.

## 🎤 Na entrevista
- **O que é `asyncio` e como funciona?** Concorrência **cooperativa** numa única thread: um laço de eventos executa corrotinas e as alterna nos pontos de `await`, enquanto o sistema operacional avisa quando I/O está pronto; ótimo para muitas esperas de rede, inútil para cálculo.
- **Qual a diferença entre `await` e `asyncio.gather`?** `await` executa e espera uma operação de cada vez (em sequência, quando seguidos); `gather` agenda várias ao mesmo tempo e espera todas, sobrepondo as esperas.
- **O que acontece se eu chamar `time.sleep` ou `requests.get` dentro de `async def`?** Bloqueia o laço inteiro e congela todas as outras requisições/tarefas; usa-se `await asyncio.sleep`, um cliente assíncrono (`httpx`) ou `asyncio.to_thread`.
- **Quando usar threads, processos ou `asyncio`?** `asyncio` para muitas esperas de rede com bibliotecas assíncronas; threads para esperar com código bloqueante; processos para cálculo; e filas para o que pode ser adiado.
- **Como o Django lida com `async`?** Views assíncronas, ORM com métodos `a...`, e `SynchronousOnlyOperation` ao usar o ORM síncrono; serviços transacionais ficam síncronos e são chamados com `sync_to_async`.

## 📚 Para ir além
- 📄 Documentação oficial: [`asyncio`](https://docs.python.org/pt-br/3/library/asyncio.html). Visão geral em português.
- 📄 Documentação oficial: [Corrotinas e tarefas](https://docs.python.org/3/library/asyncio-task.html). `gather`, `TaskGroup`, `timeout`, `to_thread`.
- 📄 Documentação oficial: [Sincronização no `asyncio`](https://docs.python.org/3/library/asyncio-sync.html). `Semaphore`, `Lock`, `Event`.
- 📄 Documentação oficial: [Desenvolvendo com `asyncio` (modo debug)](https://docs.python.org/3/library/asyncio-dev.html). Como achar chamadas bloqueantes.
- 📄 Documentação oficial: [Visão conceitual do `asyncio`](https://docs.python.org/3/howto/a-conceptual-overview-of-asyncio.html). Corrotinas e laço de eventos sem jargão (em inglês).
- 📄 Documentação oficial: [Suporte assíncrono do Django](https://docs.djangoproject.com/en/5.2/topics/async/). Views async, ORM assíncrono e `sync_to_async`.
- 🏋️ Prática extra: rode `aio2.py` com `PYTHONASYNCIODEBUG=1`. No laboratório, o modo debug emitiu `Executing <Task ... coro=<main() ...> took 0.600 seconds`, apontando a chamada que travou o laço.

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Sei que chamar uma corrotina não a executa
- [ ] Vi `gather` sobrepor esperas e 10.000 esperas numa só thread
- [ ] Reproduzi o laço travado por `time.sleep` e o corrigi
- [ ] Usei `Semaphore`, `timeout` e `TaskGroup`
- [ ] Usei o ORM assíncrono e `sync_to_async` e entendi `SynchronousOnlyOperation`
