# 1. Bloqueante × não bloqueante; I/O-bound × CPU-bound

> ⏱️ ~1h30 · Módulo 7 · Pré-requisitos: [1.15 (iteradores e geradores)](../01-python-logica/15-iteradores-geradores.md), [2.01](../02-como-a-web-funciona/01-cliente-servidor-dns-tcp.md), [6.09 (throttling)](../06-apis-rest/09-paginacao-throttling.md)

> ✅ **Verificação.** Os programas desta aula foram executados em 2026-11-08 com **Python 3.13** (biblioteca padrão apenas). Os tempos são reais **desta máquina** e variam de computador para computador; o que importa é a **proporção** entre tempo de parede e de CPU.

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar o que é uma chamada **bloqueante** e uma **não bloqueante**, e **concorrência × paralelismo**
- Diferenciar um programa **I/O-bound** (espera) de um **CPU-bound** (calcula) **medindo**, com `perf_counter` e `process_time`
- Reconhecer onde o MiniShop **espera** (e-mail, antifraude, banco) e por que isso limita quantos pedidos por segundo cabem
- Calcular a **vazão** de um servidor com *workers* síncronos a partir da latência
- Escolher o ponto de partida certo: threads/`asyncio` para esperar, processos para calcular, fila para adiar

## 🤔 Por que isso importa
“Por que meu servidor não aguenta 50 usuários se a CPU está em 3%?” é a pergunta clássica do júnior que descobre que **esperar também custa**: enquanto um *worker* aguarda o SMTP ou uma API externa, ele fica **ocupado e inútil**. Entender a diferença entre esperar e calcular é a base de tudo neste módulo (threads, `asyncio`, filas, webhooks) e de uma pergunta frequente de entrevista: “quando usar `async`? e quando processos?”.

## 💡 Intuição (explicação simples)
Pense numa **cozinha com um cozinheiro**. Quando ele **pica cebola** (CPU), está trabalhando: só outro cozinheiro (outro núcleo) aceleraria. Quando ele **espera a água ferver** (I/O), está parado: se ficar olhando a panela (bloqueante), perde tempo; se aproveitar a espera para picar o tomate (não bloqueante), faz mais com o mesmo cozinheiro. O pedido do cliente que exige “ferver, esperar o entregador de gelo e ligar para o fornecedor” demora por **espera**, não por trabalho, e é isso que se otimiza com concorrência, sem comprar mais fogões.

## 🔬 Como funciona por dentro
- **Chamada bloqueante:** a função só retorna quando a operação termina; a *thread* que a chamou **fica parada** (o sistema operacional a coloca para dormir e dá a CPU a outra). `time.sleep()`, `socket.recv()`, `requests.get()`, `cursor.execute()` bloqueiam.
- **Chamada não bloqueante:** retorna **na hora**, dizendo “ainda não está pronto” ou devolvendo uma promessa; o programa decide o que fazer enquanto isso (`asyncio`, *sockets* com `select`). Alguém precisa **voltar a perguntar** (laço de eventos, aula 03).
- **Concorrência × paralelismo:**
  | Conceito | Definição | Exemplo |
  |---|---|---|
  | **Concorrência** | **lidar com** várias coisas ao mesmo tempo (intercalando) | 1 atendente, 5 clientes em espera por telefone |
  | **Paralelismo** | **executar** várias coisas **ao mesmo instante** | 4 atendentes atendendo 4 clientes |
  Concorrência resolve **espera**; paralelismo resolve **cálculo**.
- **I/O-bound** (limitado por entrada/saída): o tempo é dominado por **esperar** disco, rede ou banco. Sinal: **tempo de parede ≫ tempo de CPU**. Ajuda: concorrência (threads, `asyncio`).
- **CPU-bound** (limitado por processamento): o tempo é dominado por **calcular** (hash, imagem, regex, compressão, JSON enorme). Sinal: **CPU ≈ parede**. Ajuda: **paralelismo** (vários processos, aula 02) ou um algoritmo melhor.
- **Medir, não adivinhar.** Dois relógios do Python:
  | Relógio | O que mede |
  |---|---|
  | `time.perf_counter()` | tempo de **parede** (o que o cliente percebe) |
  | `time.process_time()` | tempo de **CPU** do processo (só quando ele de fato calcula) |
  A razão `cpu / parede` perto de **0** = esperando; perto de **1** = calculando.
- **Ordens de grandeza** (aproximadas, ajudam a intuir): acessar a memória ≈ **100 ns**; um SSD ≈ **100 µs**; um banco na mesma rede ≈ **1 ms**; uma API em outro datacenter ≈ **50–300 ms**; um SMTP lento ≈ **centenas de ms a segundos**. A espera por rede é **milhares a milhões de vezes** maior que uma operação em memória.
- **Vazão de um worker síncrono** = `1 / latência`. Com `N` workers: `N / latência`. Se cada pedido leva 1,4 s esperando o e-mail e o antifraude, **um** worker atende **0,7 pedido/s**, mesmo com a CPU quase parada. Aumentar workers ajuda, mas cada worker custa memória (e o banco tem limite de conexões).
- **As três saídas** para reduzir espera, que veremos no módulo: (1) **concorrência** dentro do processo (threads/`asyncio`, aulas 02 e 03), (2) **adiar** o que não precisa ser feito agora (fila e *worker*, aulas 06 e 07: o e-mail pode sair depois da resposta), (3) **inverter** a chamada (webhook: em vez de ficar consultando o gateway de pagamento, ele avisa quando terminar, aula 09).
- **O que é “tempo de espera” no MiniShop hoje:** gravar o pedido (rápido), **enviar o e-mail de confirmação**, **consultar o antifraude** e, no futuro, **chamar o gateway de pagamento**. Todas são espera de rede.

## 🛠️ Exemplo prático
**1. I/O-bound × CPU-bound, medidos** (`io_cpu.py`; uma “API externa” lenta roda numa *thread* do próprio script)
```python
"""Bloqueante × não bloqueante; I/O-bound × CPU-bound: medindo o tempo de parede e o tempo de CPU."""
import hashlib
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen


class Lento(BaseHTTPRequestHandler):                 # uma "API externa" que demora 0,3 s para responder
    def do_GET(self):
        time.sleep(0.3)
        self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), Lento)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_port}/"


def medir(titulo, fn):
    p0, c0 = time.perf_counter(), time.process_time()
    fn()
    parede, cpu = time.perf_counter() - p0, time.process_time() - c0
    print(f"{titulo:<48} parede={parede:5.2f}s  cpu={cpu:5.2f}s  cpu/parede={cpu / parede:4.0%}")
    return parede, cpu


print("--- I/O-bound: o programa ESPERA")
medir("4 × time.sleep(0.5)", lambda: [time.sleep(0.5) for _ in range(4)])
medir("5 chamadas HTTP seguidas à API lenta (0,3 s)", lambda: [urlopen(URL).read() for _ in range(5)])

print("\n--- CPU-bound: o programa TRABALHA")
def hash_pesado():
    for _ in range(4):
        hashlib.pbkdf2_hmac("sha256", b"senha", b"sal", 400_000)
medir("4 × PBKDF2 com 400 mil iterações", hash_pesado)
medir("soma de 10 milhões de inteiros (laço Python)", lambda: sum(i * i for i in range(10_000_000)))

print("\n--- o pedido do MiniShop, feito de forma síncrona (a cada passo o servidor ESPERA)")
def pedido_sincrono():
    time.sleep(0.05)      # grava o pedido no banco
    time.sleep(0.8)       # envia o e-mail de confirmação (SMTP)
    time.sleep(0.5)       # avisa o antifraude (HTTP)
    time.sleep(0.05)      # monta a resposta
t, cpu = medir("POST /orders/ com e-mail e antifraude no meio", pedido_sincrono)
print(f"→ o cliente espera {t:.1f} s; o servidor gastou só {cpu * 1000:.0f} ms de CPU: o resto foi ESPERA")

print("\n--- quantos pedidos por segundo cabem em um worker síncrono?")
for latencia in (0.05, 0.3, 1.4):
    print(f"latência {latencia:>4} s → {1 / latencia:5.1f} req/s por worker | com 4 workers: {4 / latencia:5.1f} req/s")
srv.shutdown()
```
```bash
python3 io_cpu.py
```
```text
--- I/O-bound: o programa ESPERA
4 × time.sleep(0.5)                              parede= 2.00s  cpu= 0.00s  cpu/parede=  0%
5 chamadas HTTP seguidas à API lenta (0,3 s)     parede= 1.51s  cpu= 0.01s  cpu/parede=  0%

--- CPU-bound: o programa TRABALHA
4 × PBKDF2 com 400 mil iterações                 parede= 0.18s  cpu= 0.18s  cpu/parede=100%
soma de 10 milhões de inteiros (laço Python)     parede= 0.36s  cpu= 0.36s  cpu/parede=100%

--- o pedido do MiniShop, feito de forma síncrona (a cada passo o servidor ESPERA)
POST /orders/ com e-mail e antifraude no meio    parede= 1.40s  cpu= 0.00s  cpu/parede=  0%
→ o cliente espera 1.4 s; o servidor gastou só 1 ms de CPU: o resto foi ESPERA

--- quantos pedidos por segundo cabem em um worker síncrono?
latência 0.05 s →  20.0 req/s por worker | com 4 workers:  80.0 req/s
latência  0.3 s →   3.3 req/s por worker | com 4 workers:  13.3 req/s
latência  1.4 s →   0.7 req/s por worker | com 4 workers:   2.9 req/s
```
Leitura:
- **Esperar:** quatro `sleep(0.5)` e cinco chamadas HTTP de 0,3 s levaram exatamente a **soma** das esperas (2,0 s e 1,5 s) com **0% de CPU**. O programa estava parado, e as chamadas **seguidas** não aproveitam a espera uma da outra.
- **Calcular:** os hashes e o laço usaram **100% de CPU**: tempo de parede = tempo de CPU.
- **O pedido síncrono:** 1,4 s para o cliente e **1 ms de CPU**. A CPU do servidor quase não trabalhou; ele esperou o SMTP e o antifraude. É a razão de existirem filas (aula 06).
- **Vazão:** com 1,4 s de latência, **um** worker serve só 0,7 pedido/s; com 4 workers, 2,9 pedidos/s. Se o e-mail e o antifraude saíssem do caminho (latência 0,1 s), cada worker serviria **10 pedidos/s**: **14 vezes mais** sem comprar servidor.
- Os valores de CPU variam com a máquina (o PBKDF2 aqui foi rápido); a conclusão **não** varia.

**2. Classificar funções automaticamente** (`classificar.py`)
```python
import hashlib
import json
import re
import tempfile
import time


def classificar(fn, limite=0.5):
    """Mede o tempo de parede e de CPU e classifica a função."""
    p0, c0 = time.perf_counter(), time.process_time()
    fn()
    parede, cpu = time.perf_counter() - p0, time.process_time() - c0
    razao = cpu / parede if parede else 0
    return ("CPU-bound" if razao >= limite else "I/O-bound"), round(razao, 2), round(parede, 2)


def le_arquivo_grande():
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"x" * 50_000_000); f.flush()
        open(f.name, "rb").read()


casos = {
    "time.sleep(0.3)": lambda: time.sleep(0.3),
    "sha256 de 30 MB": lambda: hashlib.sha256(b"x" * 30_000_000).hexdigest(),
    "json.dumps de 200 mil itens": lambda: json.dumps([{"id": i, "nome": f"p{i}"} for i in range(200_000)]),
    "regex em texto de 5 MB": lambda: re.findall(r"\d+", "abc 123 " * 600_000),
    "ler arquivo de 50 MB (no cache do SO)": le_arquivo_grande,
    "esperar por resposta (select/sleep curto ×20)": lambda: [time.sleep(0.02) for _ in range(20)],
}
for nome, fn in casos.items():
    tipo, razao, parede = classificar(fn)
    print(f"{nome:<46} → {tipo:<9} (cpu/parede = {razao:4.2f}, parede = {parede:4.2f} s)")
```
```text
time.sleep(0.3)                                → I/O-bound (cpu/parede = 0.00, parede = 0.30 s)
sha256 de 30 MB                                → CPU-bound (cpu/parede = 1.00, parede = 0.03 s)
json.dumps de 200 mil itens                    → CPU-bound (cpu/parede = 1.00, parede = 0.07 s)
regex em texto de 5 MB                         → CPU-bound (cpu/parede = 1.00, parede = 0.07 s)
ler arquivo de 50 MB (no cache do SO)          → CPU-bound (cpu/parede = 1.00, parede = 0.05 s)
esperar por resposta (select/sleep curto ×20)  → I/O-bound (cpu/parede = 0.00, parede = 0.40 s)
```
(Os tempos de parede variam um pouco entre execuções; a classificação, não.) Uma surpresa instrutiva: **ler um arquivo que já está no cache do sistema** foi classificado como CPU-bound, porque o SO só copiou memória. Com um arquivo **frio** em disco lento, ou pela rede, o mesmo código seria I/O-bound. **“I/O-bound” depende do que está por baixo**, por isso medimos no ambiente real.

## 🧠 Pausa para lógica
**Problema (vazão e custo).** Um endpoint gasta 20 ms de CPU e 280 ms esperando uma API externa. Com `W` workers síncronos, qual a vazão máxima (req/s) em `W = 1, 4, 16`? Qual a **utilização de CPU** de cada worker? Se a espera caísse para 30 ms (cache/fila), quantos workers seriam necessários para a mesma vazão que 16 workers tinham antes?

<details><summary>Dica</summary>
Vazão = <code>W / (cpu + espera)</code>. Utilização de CPU de um worker = <code>cpu / (cpu + espera)</code>. Para igualar a vazão, resolva <code>W' / (cpu + espera') = W / (cpu + espera)</code>.
</details>

<details><summary>Solução comentada</summary>

```python
cpu, espera = 0.020, 0.280
latencia = cpu + espera
for w in (1, 4, 16):
    print(f"W={w:>2} → {w / latencia:5.1f} req/s | CPU por worker: {cpu / latencia:.0%}")

meta = 16 / latencia                           # a vazão que 16 workers davam
nova_latencia = cpu + 0.030
w_novo = meta * nova_latencia
print(f"\nmeta = {meta:.1f} req/s | nova latência = {nova_latencia * 1000:.0f} ms → workers necessários = {w_novo:.1f} ≈ {round(w_novo + 0.499)}")
```
```text
W= 1 →   3.3 req/s | CPU por worker: 7%
W= 4 →  13.3 req/s | CPU por worker: 7%
W=16 →  53.3 req/s | CPU por worker: 7%

meta = 53.3 req/s | nova latência = 50 ms → workers necessários = 2.7 ≈ 3
```
(Executado em 2026-11-08.) Cada worker usa só **7% de CPU**: 93% do tempo dele é espera. Reduzir a espera de 280 ms para 30 ms trocou **16 workers por 3**, com a mesma vazão, e é exatamente o ganho de tirar o trabalho lento do caminho do pedido.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / erro | Causa | Solução |
|---|---|---|
| “Adicionei workers e quase nada mudou” | O gargalo é CPU do banco/outro serviço, ou o limite de conexões | Medir onde o tempo vai (perfil, `EXPLAIN`, APM) |
| “CPU em 5% mas o servidor está lento” | Workers parados esperando I/O | Reduzir/concorrer a espera (async, fila, cache) |
| Usar threads para acelerar cálculo e não melhorar | CPU-bound sob o **GIL** (aula 02) | Processos ou algoritmo melhor |
| Usar `time.time()` para medir intervalos | Relógio de parede pode ser ajustado | `time.perf_counter()` |
| Chamar API externa dentro de `transaction.atomic()` | Segura a transação (e travas) durante a espera | Chamar **depois** do commit (`transaction.on_commit`, aula 06) |
| Chamada externa **sem timeout** | Uma API travada trava o worker para sempre | Sempre definir *timeout* (aula 04) |
| Medir uma vez e concluir | Variação de cache, rede e máquina | Várias execuções; olhar a proporção, não só o valor |
| “Async é mais rápido” | Confusão entre esperar e calcular | Async melhora **vazão com espera**, não a velocidade de cálculo (aula 03) |

- **Meça antes de otimizar** (parede × CPU) e **esconda a espera**, não a CPU: o ganho está em não deixar o worker parado.
- **Tire do caminho crítico** o que o cliente não precisa esperar (e-mail, relatório, webhook para terceiros).
- Toda chamada de rede tem **timeout**, e a de escrita relevante tem **idempotência** (módulo 6).
- Mais workers não são grátis: memória, conexões do banco e *throttling* de terceiros também limitam.

## 🧩 Exercícios
**1. Fixação**
(a) Qual a diferença entre concorrência e paralelismo? (b) Como saber, medindo, se uma função é I/O-bound? (c) Por que 4 workers síncronos com latência de 1,4 s só dão ~2,9 req/s? (d) Dê dois exemplos de I/O-bound e dois de CPU-bound no MiniShop.

<details><summary>Solução</summary>

(a) Concorrência é lidar com várias tarefas intercalando (resolve espera); paralelismo é executá-las ao mesmo instante (resolve cálculo). (b) `process_time()/perf_counter()` próximo de 0: o tempo de parede é espera. (c) Cada worker atende `1/1,4 ≈ 0,71` req/s; `4 × 0,71 ≈ 2,9`. (d) I/O-bound: enviar e-mail, consultar o antifraude, consultas ao banco; CPU-bound: gerar PDF/relatório grande, redimensionar imagens, calcular hash de senha (PBKDF2).
</details>

**2. Aplicação no projeto MiniShop**
Diagnostique onde o MiniShop espera.

Critérios de pronto (em `docs/espera.md`):
- [ ] Lista dos pontos de espera do fluxo de pedido (banco, e-mail, antifraude simulado, gateway de pagamento futuro) com a latência estimada de cada um
- [ ] Um *script* que mede (com `perf_counter` e `process_time`) um pedido **síncrono simulado** e mostra a razão CPU/parede
- [ ] A **vazão** por worker e com 4 workers, antes e depois de retirar o e-mail e o antifraude do caminho do pedido
- [ ] Classificação de 5 funções do projeto como I/O-bound ou CPU-bound, com a medição
- [ ] Uma frase por ponto de espera dizendo **a estratégia** (concorrência, fila, webhook, cache) e em qual aula entra
- [ ] Commit `docs: diagnose waiting points in the order flow`

<details><summary>Solução de referência (trecho do `docs/espera.md`)</summary>

| Passo do pedido | Tipo | Latência | Estratégia | Aula |
|---|---|---|---|---|
| gravar pedido (transação) | I/O (banco) | ~50 ms | manter síncrono (precisa ser consistente) | — |
| e-mail de confirmação | I/O (SMTP) | ~800 ms | fila + worker, depois do commit | 7.06 |
| antifraude | I/O (HTTP) | ~500 ms | chamadas concorrentes com timeout, ou fila | 7.03/7.04 |
| gateway de pagamento | I/O (HTTP) + espera humana | segundos a minutos | webhook | 7.09 |
| hash da senha no login | CPU | ~100 ms | manter; limitar tentativas | — |
</details>

**3. Desafio (opcional)**
Escreva um decorador `@medido` que registre, a cada chamada, o tempo de parede, o de CPU e a razão, e imprima um aviso quando a razão ficar abaixo de 10% e a parede passar de 200 ms (“esta função espera demais”). Aplique-o nas funções do exercício 2.

## 🎤 Na entrevista
- **Qual a diferença entre I/O-bound e CPU-bound?** I/O-bound passa a maior parte do tempo esperando disco, rede ou banco (tempo de parede ≫ CPU) e se beneficia de concorrência; CPU-bound passa o tempo calculando (CPU ≈ parede) e se beneficia de paralelismo (vários processos/núcleos) ou de algoritmo melhor.
- **O que significa uma chamada bloqueante?** A *thread* que a chama fica parada até a operação terminar; enquanto isso ela não faz outra coisa. A alternativa é não bloquear (async) ou delegar a outra *thread*/processo/fila.
- **Meu servidor está com CPU baixa e lento, por quê?** Provavelmente os workers estão esperando I/O (banco, APIs externas). A solução é reduzir/concorrer a espera, adiar trabalho para filas, usar cache e ajustar *timeouts*, e não necessariamente mais CPU.
- **Concorrência e paralelismo são a mesma coisa?** Não: concorrência é estrutura (lidar com várias tarefas), paralelismo é execução simultânea; dá para ter concorrência sem paralelismo (um núcleo, `asyncio`).

## 📚 Para ir além
- 📄 Documentação oficial: [Módulo `time` (Python)](https://docs.python.org/pt-br/3/library/time.html). `perf_counter`, `process_time`, `sleep`.
- 📄 Documentação oficial: [Glossário do Python](https://docs.python.org/3/glossary.html). Termos como *GIL*, *coroutine*, *event loop* (em inglês).
- 📑 Artigo/tutorial: [roadmap.sh — Backend](https://roadmap.sh/backend). Onde concorrência, filas e mensageria aparecem na trilha de backend.
- 🏋️ Prática extra: ative `django.db.backends` e `time` numa view lenta do MiniShop e descubra qual passo domina o tempo.

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Medi a diferença entre tempo de parede e de CPU
- [ ] Sei classificar uma função como I/O-bound ou CPU-bound e justificar
- [ ] Calculei a vazão de workers síncronos a partir da latência
- [ ] Identifiquei os pontos de espera do pedido do MiniShop
- [ ] Sei as três saídas: concorrência, fila e webhook
