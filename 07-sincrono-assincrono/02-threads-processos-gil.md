# 2. Threads, processos e o GIL

> ⏱️ ~1h30 · Módulo 7 · Pré-requisitos: [7.01](01-bloqueante-io-cpu.md), [1.16 (decorators e context managers)](../01-python-logica/16-decorators-context-managers.md), [5.17 (transações e travas)](../05-django/17-pedidos-estoque-transacao.md)

> ✅ **Verificação.** Todos os programas foram executados em 2026-11-08, numa máquina de **12 núcleos**, com **Python 3.13.18** (com GIL) e **Python 3.13.18 free-threaded** (`python3.13t`, sem GIL). Os tempos são reais desta máquina; o que importa é a **proporção** entre as linhas. Os exemplos com Django usam o laboratório do módulo 6.

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar o que é uma *thread*, um processo e o **GIL**, e o que ele permite e impede
- Escolher entre **threads** (esperar), **processos** (calcular) e sequencial, **medindo** em vez de supor
- Usar `ThreadPoolExecutor` e `ProcessPoolExecutor` e explicar o custo de criar processos e mover dados (*pickle*)
- Reconhecer e corrigir uma **condição de corrida** com `Lock`, sem depender da “sorte” do GIL
- Saber que, no Django, **cada thread tem sua própria conexão** com o banco e precisa fechá-la

## 🤔 Por que isso importa
Quase todo servidor Python usa threads ou processos sem que você perceba: o Gunicorn *sync* usa processos; o `runserver` usa threads; o Celery (aula 06) usa processos. Entender o GIL evita dois erros caros: **esperar que threads acelerem cálculo** (não aceleram em Python comum) e **usar processos para tarefas minúsculas** (ficam centenas de vezes mais lentas). Em entrevista: “o que é o GIL e quando ele atrapalha?” é pergunta garantida.

## 💡 Intuição (explicação simples)
Numa **cozinha com uma única bancada de corte**, vários cozinheiros (*threads*) dividem a mesma bancada: só **um corta por vez** (o GIL é a regra “uma faca na bancada”). Para **esperar** (ferver a água, forno), não precisam da bancada, então os outros cortam enquanto um espera: ótimo para I/O. Para **cortar** (CPU), a bancada única vira gargalo: mais cozinheiros não aceleram. A saída é **mais cozinhas** (processos), cada uma com sua bancada, ao custo de montar cada cozinha (memória e tempo) e de **levar os ingredientes** de uma para outra (serialização). A novidade é a **bancada sem trava** (Python *free-threaded*): vários cortam ao mesmo tempo, mas agora os cozinheiros precisam combinar quem mexe em quê (travas), senão há bagunça.

## 🔬 Como funciona por dentro
- **Processo**: programa em execução com **memória própria** (isolada). Se um quebra, os outros seguem. Criar custa mais (segundos de memória e milissegundos de tempo) e **trocar dados** exige serializar (*pickle*).
- **Thread**: linha de execução **dentro** de um processo, **compartilhando a memória**. Barata de criar e de trocar dados, mas **perigosa** (corridas, travas).
- **GIL (*Global Interpreter Lock*)** no CPython padrão: uma trava global garantindo que **só uma thread executa bytecode Python por vez**. Consequências:
  | Carga | Threads com GIL | Processos |
  |---|---|---|
  | **I/O-bound** (esperar rede/disco/banco) | **ganham**: o GIL é **liberado** durante a espera | ganham, com mais custo |
  | **CPU-bound** em Python puro | **não ganham** (só um calcula por vez) | **ganham** (um GIL por processo) |
  Bibliotecas em C/Rust (NumPy, hashlib, compressão) podem **liberar o GIL** enquanto calculam, então threads ajudam nelas.
- **Python *free-threaded*.** O Python 3.13 trouxe uma compilação **experimental sem GIL** (PEP 703), e o 3.14 a tornou **oficialmente suportada, mas opcional** (PEP 779). Nela, threads de CPU escalam, ao custo de um programa de uma thread um pouco mais lento e de **bibliotecas** que ainda precisam ser compatíveis. O curso usa o Python **com GIL**; a medição abaixo mostra a diferença.
- **Concurrent.futures**: a interface comum.
  | | `ThreadPoolExecutor` | `ProcessPoolExecutor` |
  |---|---|---|
  | Para | esperar (I/O) | calcular (CPU) |
  | Dados | compartilhados (cuidado!) | copiados (pickle) |
  | Custo de criar | baixo | alto |
  | Uso | `ex.map(fn, itens)` / `ex.submit(fn, x)` → `Future` | idem, `fn` e argumentos precisam ser *picklable* |
- **Condição de corrida (*race condition*)**: o resultado depende da **ordem** em que as threads se intercalam. `x += 1` são **três passos** (ler, somar, escrever); duas threads podem ler o mesmo valor e uma sobrescreve o trabalho da outra (*lost update*, como no estoque da aula 5.17). A defesa em memória é uma **trava** (`threading.Lock`); no banco, `F()`, `select_for_update()` e transações.
- **“Funciona com o GIL” não é garantia.** Algumas operações parecem seguras no CPython padrão por **acaso de implementação**; no *free-threaded* o bug aparece (veja abaixo). Escreva código **correto**, não code “que costuma funcionar”.
- **Método de início de processos:** no Linux, o 3.13 usa `fork` (copia o processo; rápido, mas problemático com threads e bibliotecas); o **3.14 passou a usar `forkserver`**; no macOS/Windows é `spawn`. Em `spawn`/`forkserver` o código do módulo é reimportado, por isso o `if __name__ == "__main__":` é **obrigatório** em scripts que criam processos.
- **No Django:** `django.db.connections` é **por thread**. Cada thread que você cria abre sua conexão na primeira consulta e deve fechá-la (`connections.close_all()`), senão há conexões vazadas. Threads também **não compartilham transações**: o que uma thread grava dentro de `atomic()` só aparece para as outras após o *commit*.
- **Quando usar o quê (resumo):** esperar pouco/uma vez → sequencial; várias esperas independentes → threads (ou `asyncio`, aula 03); cálculo pesado → processos (ou, no futuro, free-threaded); trabalho que pode esperar → fila + worker (aula 06).

## 🛠️ Exemplo prático
**1. Threads × processos, esperando e calculando** (`gil.py`)
```python
"""Threads × processos, para trabalho de ESPERA e de CÁLCULO. Rode no Python normal e no free-threaded."""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

N = 4                                    # número de tarefas (e de workers)


def espera(_):                           # I/O-bound simulado
    time.sleep(0.5)


def calcula(_):                          # CPU-bound: laço Python puro
    s = 0
    for i in range(6_000_000):
        s += i * i
    return s


def cronometrar(titulo, fn):
    t = time.perf_counter()
    fn()
    print(f"  {titulo:<34} {time.perf_counter() - t:5.2f} s")


def sequencial(f):
    return lambda: [f(i) for i in range(N)]


def com_threads(f):
    def run():
        with ThreadPoolExecutor(N) as ex:
            list(ex.map(f, range(N)))
    return run


def com_processos(f):
    def run():
        with ProcessPoolExecutor(N) as ex:
            list(ex.map(f, range(N)))
    return run


if __name__ == "__main__":
    gil = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(f"Python {sys.version.split()[0]} | GIL ligado: {gil} | núcleos: {os.cpu_count()}")
    print("ESPERA (4 × sleep 0,5 s)")
    cronometrar("sequencial", sequencial(espera))
    cronometrar("4 threads", com_threads(espera))
    cronometrar("4 processos", com_processos(espera))
    print("CÁLCULO (4 × laço de 6 milhões)")
    cronometrar("sequencial", sequencial(calcula))
    cronometrar("4 threads", com_threads(calcula))
    cronometrar("4 processos", com_processos(calcula))
```
```bash
uv run --python 3.13 python gil.py       # CPython com GIL
uv python install 3.13t && python3.13t gil.py     # free-threaded (sem GIL)
```
```text
Python 3.13.18 | GIL ligado: True | núcleos: 12
ESPERA (4 × sleep 0,5 s)
  sequencial                          2.00 s
  4 threads                           0.50 s
  4 processos                         0.52 s
CÁLCULO (4 × laço de 6 milhões)
  sequencial                          0.71 s
  4 threads                           0.75 s
  4 processos                         0.26 s

Python 3.13.18 | GIL ligado: False | núcleos: 12
ESPERA (4 × sleep 0,5 s)
  sequencial                          2.00 s
  4 threads                           0.50 s
  4 processos                         0.52 s
CÁLCULO (4 × laço de 6 milhões)
  sequencial                          0.85 s
  4 threads                           0.23 s
  4 processos                         0.26 s
```
A tabela inteira da seção anterior, **medida**:
- **Esperar:** 2,0 s → **0,5 s** com 4 threads (e também com processos): as esperas acontecem **ao mesmo tempo**.
- **Calcular com GIL:** 4 threads levaram **0,75 s**, **pior** que o sequencial (0,71 s): só uma calcula por vez, e ainda se paga a troca entre threads. **Processos: 0,26 s** (≈ 2,7× mais rápido; o ganho não é 4× porque criar os processos e juntar os resultados também custa).
- **Calcular sem GIL (free-threaded):** as mesmas 4 threads caem para **0,23 s**, tão bom quanto os processos e **sem copiar dados**. Repare, porém, que o **sequencial ficou mais lento** (0,85 s contra 0,71 s): o preço da compilação sem GIL para código de uma thread só.
- A espera por `sleep` independe do GIL, que é **liberado** durante a espera.

**2. Condição de corrida** (`race.py`: 8 threads, cada uma soma 1 por 20 mil vezes → esperado 160.000)
```python
"""Condição de corrida: o 'saldo' do estoque atualizado por várias threads, sem e com Lock."""
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

THREADS, VEZES = 8, 20_000


def sem_trava():
    estoque = {"valor": 0}

    def baixa():
        for _ in range(VEZES):
            estoque["valor"] += 1                 # LER, SOMAR, ESCREVER: três passos, não um

    with ThreadPoolExecutor(THREADS) as ex:
        for _ in range(THREADS):
            ex.submit(baixa)
    return estoque["valor"]


def com_trava():
    estoque = {"valor": 0}
    trava = threading.Lock()

    def baixa():
        for _ in range(VEZES):
            with trava:                           # só uma thread por vez na seção crítica
                estoque["valor"] += 1

    with ThreadPoolExecutor(THREADS) as ex:
        for _ in range(THREADS):
            ex.submit(baixa)
    return estoque["valor"]


def passo_a_passo_sem_trava():
    """A mesma corrida, mas com uma pausa entre ler e escrever, para o problema aparecer sempre."""
    estoque = {"valor": 0}

    def baixa():
        for _ in range(200):
            atual = estoque["valor"]              # 1) ler
            time.sleep(0)                         # 2) outra thread pode entrar aqui
            estoque["valor"] = atual + 1          # 3) escrever (sobrescreve o que outra thread fez)

    with ThreadPoolExecutor(THREADS) as ex:
        for _ in range(THREADS):
            ex.submit(baixa)
    return estoque["valor"]


gil = getattr(sys, "_is_gil_enabled", lambda: True)()
esperado = THREADS * VEZES
print(f"Python {sys.version.split()[0]} | GIL ligado: {gil}")
print(f"esperado: {esperado}")
print(f"sem trava (+= simples)     : {sem_trava()}")
print(f"com Lock                   : {com_trava()}")
print(f"ler → pausar → escrever    : {passo_a_passo_sem_trava()}  (esperado {THREADS * 200})")
```
```text
Python 3.13.18 | GIL ligado: True
esperado: 160000
sem trava (+= simples)     : 160000
com Lock                   : 160000
ler → pausar → escrever    : 210  (esperado 1600)

Python 3.13.18 | GIL ligado: False
esperado: 160000
sem trava (+= simples)     : 34830
com Lock                   : 160000
ler → pausar → escrever    : 225  (esperado 1600)
```
Esta é a lição mais importante da aula:
- **Com o GIL**, o `+=` “sem trava” **deu o resultado certo** (160.000). Foi **sorte da implementação**: o CPython só troca de thread em pontos específicos, e este padrão raramente é interrompido no meio. **Não é uma garantia.**
- **Sem o GIL**, o mesmo código perdeu **mais de 75% das atualizações** (34.830 de 160.000).
- Com uma **pausa entre ler e escrever** (o que acontece de verdade quando há uma consulta ou chamada de rede no meio), a corrida aparece **sempre**, até com GIL: **210 de 1.600** (o resultado exato varia a cada execução).
- O `Lock` resolve nos dois casos. É o equivalente em memória do `select_for_update()` da aula 5.17: **ler, decidir e escrever precisam ser uma operação indivisível**.

**3. Processos têm custo** (`overhead.py`)
```python
"""Processos têm custo: criar, serializar (pickle) e devolver dados. Vale a pena só para trabalho GRANDE."""
import multiprocessing as mp
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor


def quadrado(x):
    return x * x


def pesado(n):
    s = 0
    for i in range(n):
        s += i * i
    return s


def cron(titulo, fn):
    t = time.perf_counter()
    r = fn()
    print(f"  {titulo:<52} {time.perf_counter() - t:6.3f} s")
    return r


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]} | método de início padrão: {mp.get_start_method()}")
    itens = list(range(20_000))

    print("tarefas MINÚSCULAS (20 mil × x*x)")
    cron("sequencial", lambda: [quadrado(x) for x in itens])
    with ProcessPoolExecutor(4) as ex:
        cron("4 processos, 1 tarefa por vez (chunksize=1)", lambda: list(ex.map(quadrado, itens)))
        cron("4 processos, lotes de 2.500 (chunksize=2500)", lambda: list(ex.map(quadrado, itens, chunksize=2500)))

    print("tarefas GRANDES (4 × laço de 3 milhões)")
    cron("sequencial", lambda: [pesado(3_000_000) for _ in range(4)])
    with ProcessPoolExecutor(4) as ex:
        cron("4 processos", lambda: list(ex.map(pesado, [3_000_000] * 4)))

    print("custo de MOVER dados entre processos (pickle)")
    grande = list(range(3_000_000))
    t = time.perf_counter(); blob = pickle.dumps(grande); t1 = time.perf_counter() - t
    t = time.perf_counter(); pickle.loads(blob); t2 = time.perf_counter() - t
    print(f"  lista de 3 milhões de inteiros: {len(blob) / 1e6:.0f} MB, serializar {t1:.3f} s + desserializar {t2:.3f} s")
```
```text
Python 3.13.18 | método de início padrão: fork
tarefas MINÚSCULAS (20 mil × x*x)
  sequencial                                            0.001 s
  4 processos, 1 tarefa por vez (chunksize=1)           0.869 s
  4 processos, lotes de 2.500 (chunksize=2500)          0.004 s
tarefas GRANDES (4 × laço de 3 milhões)
  sequencial                                            0.370 s
  4 processos                                           0.115 s
custo de MOVER dados entre processos (pickle)
  lista de 3 milhões de inteiros: 15 MB, serializar 0.029 s + desserializar 0.075 s
```
- Com tarefas **minúsculas**, mandar uma a uma para 4 processos foi **~900× mais lento** que o laço comum (0,869 s contra 0,001 s): cada tarefa paga serialização e comunicação. **Agrupar em lotes** (`chunksize`) cai para 0,004 s, mas ainda não vence o sequencial: **não paralelize o que é barato**.
- Com tarefas **grandes**, 4 processos ganharam **3,2×** (0,37 s → 0,115 s).
- Mover 15 MB entre processos custa ~0,1 s só de *pickle*. Dados enormes entre processos são um problema de projeto (use memória compartilhada, arquivos ou deixe cada processo ler a sua parte).
- O método de início padrão no Linux é `fork` no Python 3.13; o Python 3.14 mostrou `forkserver` neste mesmo computador. Em ambos, mantenha o `if __name__ == "__main__":`.

**4. Threads no Django: uma conexão por thread** (executado no laboratório do módulo 6)
```python
"""No Django, cada thread tem a SUA conexão com o banco (connections é thread-local)."""
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from django.db import connection, connections
from apps.catalog.models import Product


def consulta(i):
    n = Product.objects.count()                            # abre uma conexão NESTA thread, na primeira consulta
    return threading.current_thread().name, id(connection.connection), n


principal = (threading.current_thread().name, id(connection.connection), Product.objects.count())
print(f"thread principal: {principal[0]} | conexão {principal[1]} | produtos: {principal[2]}")
with ThreadPoolExecutor(4, thread_name_prefix="w") as ex:
    resultados = list(ex.map(consulta, range(12)))         # 12 tarefas em 4 threads
por_thread = defaultdict(set)
for nome, conn, _ in resultados:
    por_thread[nome].add(conn)
for nome in sorted(por_thread):
    print(f"  {nome}: {len(por_thread[nome])} conexão(ões) → {sorted(por_thread[nome])}")
todas = {c for s in por_thread.values() for c in s}
print(f"conexões distintas entre os workers: {len(todas)} | a da principal é uma delas? {principal[1] in todas}")
connections.close_all()
```
```bash
uv run python manage.py shell < django_threads.py
```
```text
thread principal: MainThread | conexão 20333824 | produtos: 65
  w_0: 1 conexão(ões) → [138775656938320]
  w_1: 1 conexão(ões) → [138775655481888]
  w_2: 1 conexão(ões) → [138775656934480]
  w_3: 1 conexão(ões) → [138775655487888]
conexões distintas entre os workers: 4 | a da principal é uma delas? False
```
Cada uma das 4 threads abriu **a sua** conexão (mantida enquanto a thread vive) e nenhuma é a da *thread* principal. Em produção com PostgreSQL, isso significa: **mais threads = mais conexões abertas**, e o PostgreSQL tem um limite (`max_connections`, padrão 100). Threads criadas por você devem chamar `connections.close_all()` ao terminar (o exemplo faz isso no fim; num servidor, o Django fecha as conexões das *threads de requisição* sozinho).

## 🧠 Pausa para lógica
**Problema (um pool de threads à mão).** Implemente `MiniPool(n)`: `n` threads que consomem tarefas de uma `queue.Queue`; `map(fn, itens)` devolve os resultados **na ordem de entrada**; o encerramento usa uma “pílula de veneno” (`None`) por worker; e o pool registra o **pico de tarefas simultâneas**, que não pode passar de `n`.

<details><summary>Dica</summary>
Cada worker faz <code>while True: item = tarefas.get(); if item is None: return</code>. Coloque <code>(indice, fn, arg)</code> na fila e os resultados <code>(indice, valor)</code> numa segunda fila; reordene por índice. Proteja o contador de ativos com um <code>Lock</code>.
</details>

<details><summary>Solução comentada</summary>

```python
import queue
import threading
import time


class MiniPool:
    """Pool de threads feito à mão: uma fila de tarefas, N workers e uma 'pílula de veneno' para encerrar."""

    def __init__(self, n):
        self.tarefas, self.resultados = queue.Queue(), queue.Queue()
        self.ativos, self.pico = 0, 0
        self.trava = threading.Lock()
        self.workers = [threading.Thread(target=self._loop, daemon=True) for _ in range(n)]
        for w in self.workers:
            w.start()

    def _loop(self):
        while True:
            item = self.tarefas.get()
            if item is None:                               # pílula de veneno: encerra este worker
                return
            indice, fn, arg = item
            with self.trava:
                self.ativos += 1
                self.pico = max(self.pico, self.ativos)
            try:
                self.resultados.put((indice, fn(arg)))
            finally:
                with self.trava:
                    self.ativos -= 1

    def map(self, fn, itens):
        itens = list(itens)
        for i, x in enumerate(itens):
            self.tarefas.put((i, fn, x))
        saida = [None] * len(itens)
        for _ in itens:
            i, r = self.resultados.get()
            saida[i] = r                                   # devolve na ORDEM de entrada
        for _ in self.workers:
            self.tarefas.put(None)
        for w in self.workers:
            w.join()
        return saida


def lenta(x):
    time.sleep(0.2)
    return x * x


t = time.perf_counter()
pool = MiniPool(4)
print("resultados:", pool.map(lenta, range(12)))
print(f"12 tarefas de 0,2 s com 4 workers: {time.perf_counter() - t:.2f} s (sequencial seria 2,4 s) | pico de tarefas simultâneas: {pool.pico}")
```
```text
resultados: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121]
12 tarefas de 0,2 s com 4 workers: 0.60 s (sequencial seria 2,4 s) | pico de tarefas simultâneas: 4
```
(Executado em 2026-11-08.) Este é o esqueleto do que o `ThreadPoolExecutor` faz e do que o Celery (aula 06) faz com **processos** e uma fila **externa** (Redis): fila + workers + um jeito de encerrar.
</details>

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| Threads para calcular e “nada melhorou” | CPU-bound sob o GIL | `ProcessPoolExecutor` (ou algoritmo/biblioteca em C) |
| Processos para tarefas pequenas e ficou **mais lento** | Custo de criar/serializar | Lotes (`chunksize`), ou nem paralelizar |
| `RuntimeError: An attempt has been made to start a new process before the current process has finished its bootstrapping phase` | Faltou `if __name__ == "__main__":` com `spawn`/`forkserver` | Proteger o ponto de entrada |
| `AttributeError: Can't pickle local object` / `PicklingError` | Função local, `lambda` ou objeto não *picklable* enviado a processo | Funções de módulo e argumentos simples |
| Resultado diferente a cada execução | Condição de corrida | `Lock`, filas, ou evitar estado compartilhado |
| `django.db.utils.OperationalError: too many connections` / `FATAL: sorry, too many clients already` | Threads demais, cada uma com conexão | Limitar o pool, fechar conexões, *pool* de conexões/PgBouncer |
| `SynchronousOnlyOperation` | ORM usado em contexto assíncrono (aula 03) | `sync_to_async`/`asyncio.to_thread` |
| Deadlock (tudo para) | Duas travas pedidas em ordens diferentes | Mesma ordem de travas; `timeout` no `acquire` |
| `KeyboardInterrupt` não encerra o programa | Threads não *daemon* esperando | `daemon=True` ou sinal de parada |
| Misturar `fork` com threads | Estado de travas copiado em estado ruim | `spawn`/`forkserver` ou criar processos antes das threads |

- **Comece pelo mais simples:** sequencial; só adicione concorrência com uma **medição** que mostre o ganho.
- **Evite estado compartilhado mutável** entre threads; prefira filas (`queue.Queue`), mensagens e resultados devolvidos.
- **Não use o ORM livremente em threads suas**: conexões, transações e *thread-safety* exigem cuidado; para trabalho no banco em segundo plano, use **fila + worker** (aula 06).
- Para esperar muita coisa ao mesmo tempo (milhares de chamadas de rede), `asyncio` (aula 03) escala melhor que threads.
- Nunca confie em “no CPython isso é atômico” para correção: use travas, estruturas seguras ou o banco.

## 🧩 Exercícios
**1. Fixação**
(a) O que o GIL impede e o que ele **não** impede? (b) Por que 4 threads de cálculo foram mais lentas que o sequencial no Python com GIL? (c) Por que o código sem trava “funcionou” com o GIL e falhou sem ele? (d) Por que `ProcessPoolExecutor` com uma tarefa minúscula por vez foi tão lento?

<details><summary>Solução</summary>

(a) Impede **duas threads de executarem bytecode Python ao mesmo tempo**; não impede esperas simultâneas (o GIL é liberado em I/O), nem processos paralelos. (b) Só uma calcula por vez e ainda há o custo da troca de contexto. (c) Foi sorte: o CPython só troca de thread em pontos específicos e esse padrão raramente é interrompido; sem o GIL, as threads rodam de fato juntas e a corrida aparece. (d) Cada tarefa paga serialização e comunicação entre processos, muito maior que o trabalho; lotes (`chunksize`) reduzem o custo.
</details>

**2. Aplicação no projeto MiniShop**
Aplique concorrência onde faz sentido e prove com números.

Critérios de pronto:
- [ ] Um *script* `scripts/antifraude_concorrente.py` que consulta um antifraude **simulado** (servidor local com 0,3 s de latência) para 8 pedidos: sequencial × `ThreadPoolExecutor(8)`, com os tempos medidos
- [ ] Um teste mostrando que o tempo concorrente é menor que 40% do sequencial (com folga para variação)
- [ ] Um contador de “pedidos processados” compartilhado entre as threads, **com `Lock`**, e um teste que prova o total correto
- [ ] Um cálculo CPU-bound (ex.: hashes) comparando sequencial, threads e processos, e uma nota em `docs/concorrencia.md` explicando o resultado com o GIL
- [ ] Nenhuma chamada ao ORM em threads suas sem fechar a conexão (use `connections.close_all()` no `finally`)
- [ ] Commit `perf: concurrent fraud checks with a thread pool`

<details><summary>Solução de referência (esqueleto; executado: `sequencial 2.41 s | 8 threads 0.30 s | processados=8`)</summary>

```python
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen


class Antifraude(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.3)
        self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), Antifraude)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_port}/"

processados, trava = 0, threading.Lock()


def checar(pedido_id):
    global processados
    urlopen(URL, timeout=2).read()
    with trava:
        processados += 1
    return pedido_id


t = time.perf_counter(); [checar(i) for i in range(8)]; seq = time.perf_counter() - t
processados = 0
t = time.perf_counter()
with ThreadPoolExecutor(8) as ex:
    list(ex.map(checar, range(8)))
conc = time.perf_counter() - t
print(f"sequencial {seq:.2f} s | 8 threads {conc:.2f} s | processados={processados}")
assert conc < seq * 0.4 and processados == 8
```
</details>

**3. Desafio (opcional)**
Escreva um decorador `@sincronizado` (usa um `Lock` interno) e uma versão *thread-safe* do contador de estoque. Rode o teste de corrida (8 threads × 20 mil) no Python normal e no *free-threaded* e registre os resultados. Depois substitua o `Lock` por uma operação atômica no banco (`F()` com SQLite/PostgreSQL) e compare.

## 🎤 Na entrevista
- **O que é o GIL e quando ele atrapalha?** Uma trava global do CPython que permite só uma *thread* executar bytecode Python por vez. Não atrapalha carga I/O-bound (o GIL é liberado nas esperas), mas impede que threads acelerem cálculo em Python puro; para isso usam-se processos, bibliotecas em C ou, a partir do 3.13/3.14, a compilação *free-threaded*.
- **Threads ou processos?** Threads para esperar (I/O), por serem leves e compartilharem memória; processos para calcular (paralelismo real), pagando custo de criação, memória e serialização. Para trabalho que pode esperar, uma fila com workers.
- **O que é uma condição de corrida e como evitá-la?** Resultado dependente da intercalação de threads (ler-modificar-escrever não atômico). Evita-se com travas, filas, evitar estado compartilhado ou, no banco, operações atômicas (`F()`), transações e `select_for_update()`.
- **Como o Django lida com threads e conexões?** Cada thread tem sua própria conexão com o banco; threads criadas manualmente devem fechá-la; e há limite de conexões no banco, então threads demais esgotam o servidor.

## 📚 Para ir além
- 📄 Documentação oficial: [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html). `ThreadPoolExecutor`, `ProcessPoolExecutor`, `Future`.
- 📄 Documentação oficial: [`threading`](https://docs.python.org/3/library/threading.html). `Thread`, `Lock`, `Event`, `Semaphore`.
- 📄 Documentação oficial: [`multiprocessing`](https://docs.python.org/3/library/multiprocessing.html). Métodos de início (`fork`, `spawn`, `forkserver`) e memória compartilhada.
- 📄 Documentação oficial: [Python *free-threading* (HOWTO)](https://docs.python.org/3/howto/free-threading-python.html). Como usar e o que muda.
- 📄 Especificação: [PEP 703 — tornando o GIL opcional](https://peps.python.org/pep-0703/). A proposta original.
- 📄 Especificação: [PEP 779 — critérios para o suporte oficial do *free-threaded*](https://peps.python.org/pep-0779/). O suporte no Python 3.14.
- 📑 Artigo/tutorial: [Wiki do Python — GlobalInterpreterLock](https://wiki.python.org/moin/GlobalInterpreterLock). Explicação curta do GIL.
- 🏋️ Prática extra: rode `gil.py` com `python3.13t -X gil=1` (religa o GIL no *free-threaded*) e compare com a execução normal. No laboratório, com o GIL religado, as 4 threads de cálculo voltaram a **0,82 s** (igual ao sequencial) enquanto os 4 processos ficaram em 0,25 s.

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Medi threads e processos para esperar e para calcular
- [ ] Vi a condição de corrida aparecer (sempre com pausa; sem GIL, mesmo sem pausa) e a corrigi com `Lock`
- [ ] Entendi o custo de processos (criar, pickle) e o papel do `chunksize`
- [ ] Sei que cada thread do Django tem sua conexão com o banco
- [ ] Sei dizer o que é o *free-threaded* e que o curso usa o Python com GIL
