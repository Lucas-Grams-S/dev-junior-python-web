# 5. Monolito, monolito modular e microsserviços

> ⏱️ ~1h · Módulo 8 · Pré-requisitos: [8.01](01-responsabilidades-camadas.md), [8.04](04-padroes-de-projeto.md), [7.04](../07-sincrono-assincrono/04-httpx-timeouts-retries.md)

> ✅ **Verificação.** Medições e `lint-imports` executados em 2026-11-08 no laboratório (Python 3.13, loopback, sem rede real). **As saídas são reais.** Os números absolutos dependem da máquina; a **ordem de grandeza** é o que importa.

## 🎯 Objetivos
- Distinguir **monolito**, **monolito modular** e **microsserviços** pelo que cada um custa
- **Medir** a diferença entre uma chamada de função e uma chamada HTTP, e calcular a disponibilidade combinada
- Impor **fronteiras de módulo** com `import-linter` (apps em camadas, sem ciclos)
- Escrever um **ADR** curto justificando por que o MiniShop continua um monolito modular

## 🤔 Por que isso importa
“Vamos migrar para microsserviços” é uma das decisões mais caras e mais mal justificadas da área. Um dev júnior que entende **o que se compra e o que se paga** é valioso em qualquer discussão de arquitetura, e esse tema cai em entrevista com frequência.

## 💡 Intuição (explicação simples)
Um **monolito** é uma casa de um cômodo grande: tudo junto, fácil de mudar, mas bagunça se cresce sem divisórias. O **monolito modular** é a mesma casa com **paredes e portas bem definidas**: cada cômodo tem sua função, só se entra pela porta. **Microsserviços** são casas separadas na mesma rua: cada uma com sua conta de luz e sua chave, e você precisa **sair na rua** para visitar o vizinho (e a rua pode estar interditada).

## 🔬 Como funciona por dentro
| | Monolito | Monolito modular | Microsserviços |
|---|---|---|---|
| Deploy | 1 unidade | 1 unidade | N unidades independentes |
| Fronteiras | informais | **impostas por ferramenta** | impostas pela rede |
| Chamada entre partes | função | função (pela “porta” pública) | HTTP/mensageria |
| Transação entre partes | sim (banco único) | sim | **não** (consistência eventual, sagas) |
| Custo operacional | baixo | baixo | alto (observabilidade, deploy, versões) |
| Quando compensa | começo | maioria dos casos | times grandes e independentes, escala desigual |

- **A rede não é de graça.** A mesma consulta de estoque, como função ou como HTTP local, custa ordens de grandeza diferentes (medição abaixo) e **pode falhar** de formas novas: timeout, indisponibilidade, versão incompatível.
- **Disponibilidade se multiplica.** Se cada dependência síncrona tem 99,9%, `k` delas em série dão `0,999^k`.
- **Perde-se a transação.** No monolito, `with transaction.atomic()` cobre pedido + estoque. Entre serviços, é preciso compensar (saga), idempotência e outbox (aula 7.10).
- **Microsserviços resolvem problema de organização** (times independentes) e de **escala desigual**, não de código bagunçado: código bagunçado vira sistema distribuído bagunçado.
- **O caminho sensato:** monolito **modular** primeiro; extrair um serviço só quando houver motivo medido (escala, time, ciclo de deploy).

## 🛠️ Exemplo prático
**1. Quanto custa atravessar a fronteira?** (`chamada.py`: uma função vs um servidor HTTP local, com conexão reaproveitada)
```python
"""Custo de uma chamada: função no mesmo processo vs HTTP local (mesma máquina, sem rede real)."""
import statistics, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx

def estoque_disponivel(produto_id: int) -> int:
    return 42

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    wbufsize = 65536  # um único send por resposta (evita Nagle + ACK atrasado = +40 ms)
    def do_GET(self):
        corpo = b'{"disponivel": 42}'
        self.send_response(200); self.send_header("Content-Length", str(len(corpo))); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(corpo)
    def log_message(self, *a): pass

srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/estoque/1"

N = 2000
t = time.perf_counter()
for _ in range(N): estoque_disponivel(1)
fn = (time.perf_counter() - t) / N

with httpx.Client() as c:
    c.get(url)
    amostras = []
    for _ in range(N):
        t = time.perf_counter(); c.get(url); amostras.append(time.perf_counter() - t)
amostras.sort()
print(f"função no mesmo processo : {fn*1e6:10.2f} µs por chamada")
print(f"HTTP local (conexão viva) : mediana {statistics.median(amostras)*1e6:8.0f} µs · p99 {amostras[int(N*.99)]*1e6:8.0f} µs")
print(f"razão (mediana HTTP / função): ~{statistics.median(amostras)/fn:,.0f}x")

# disponibilidade composta: pedido chama k serviços em série, cada um com 99,9% de disponibilidade
for k in (1, 3, 5, 10):
    print(f"{k:>2} dependências a 99,9% → disponibilidade combinada {0.999**k*100:.2f}% (~{(1-0.999**k)*30*24*60:.0f} min fora do ar/mês)")
```
```text
função no mesmo processo :       0.03 µs por chamada
HTTP local (conexão viva) : mediana      279 µs · p99      682 µs
razão (mediana HTTP / função): ~10,235x
 1 dependências a 99,9% → disponibilidade combinada 99.90% (~43 min fora do ar/mês)
 3 dependências a 99,9% → disponibilidade combinada 99.70% (~129 min fora do ar/mês)
 5 dependências a 99,9% → disponibilidade combinada 99.50% (~216 min fora do ar/mês)
10 dependências a 99,9% → disponibilidade combinada 99.00% (~430 min fora do ar/mês)
```
> 🔎 **Correção no caminho.** Minha primeira execução mostrou ~41 000 µs por chamada HTTP. Era um artefato: o `http.server` do Python escrevia cabeçalho e corpo em envios separados, e o par *Nagle + ACK atrasado* do TCP injeta ~40 ms. Com um único envio por resposta (`wbufsize`), a mediana caiu para a faixa de centenas de µs. Moral: **meça, desconfie do número e investigue** antes de concluir.

Mesmo no melhor caso (loopback, conexão viva, sem TLS, sem serialização pesada) a chamada HTTP é **dezenas de milhares de vezes** mais lenta que a função, e numa rede real ainda entram DNS, TLS, filas e perda de pacotes. A tabela de disponibilidade mostra que **10 dependências a 99,9% já dão ~430 min fora do ar por mês**.

**2. Fronteiras impostas por ferramenta** (`.importlinter`)
```ini
[importlinter]
root_packages =
    apps
    config
include_external_packages = True

[importlinter:contract:camadas-dentro-de-cada-app]
name = Dentro de cada app: interface → serviços → dados (nunca no sentido contrário)
type = layers
layers =
    api
    services
    models
containers =
    apps.cart
    apps.orders
    apps.payments

[importlinter:contract:servicos-sem-framework-de-interface]
name = Serviços e modelos não dependem de DRF nem de Channels
type = forbidden
source_modules =
    apps.catalog.models
    apps.cart.models
    apps.cart.services
    apps.orders.models
    apps.orders.services
    apps.payments.models
    apps.payments.services
forbidden_modules =
    rest_framework
    channels
allow_indirect_imports = True

[importlinter:contract:apps-sem-ciclos]
name = Apps em camadas, sem dependência circular (quem está em cima pode usar quem está embaixo)
type = layers
layers =
    apps.realtime
    apps.payments
    apps.orders
    apps.cart
    apps.catalog
```
O terceiro contrato é o coração do monolito modular: os apps formam uma **hierarquia** e nenhum importa quem está acima. O mapa real de dependências entre apps:
```text
cart      → catalog
orders    → cart, catalog
payments  → orders
realtime  → orders, payments
```
```bash
uv run lint-imports
```
```text
-------------------------------------

Dentro de cada app: interface → serviços → dados (nunca no sentido contrário) KEPT
Serviços e modelos não dependem de DRF nem de Channels KEPT
Apps em camadas, sem dependência circular (quem está em cima pode usar quem está
embaixo) KEPT

Contracts: 3 kept, 0 broken.
```
Se alguém fizer `catalog` importar `orders`, o CI quebra. Foi exatamente o que a aula 01 resolveu ao mover o `pay` para `payments` e desacoplar o Channels por sinal.

**3. Candidato a serviço, se um dia for preciso:** `payments`. Já fala com o exterior por uma **porta** (aula 04), é chamado por uma única direção e se comunica com o resto por **eventos** (`pedido_pago`). Extraí-lo seria trocar o sinal por mensagem e a chamada de função por HTTP, e o desenho já permite isso. Hoje **não há motivo**: um time, uma escala, um deploy.

**4. ADR** (`docs/adr/0002-monolito-modular.md`)
```markdown
# ADR 0002: MiniShop continua um monolito modular
Status: aceito · Data: 2026-11-08
Contexto: 1 time, tráfego baixo, transações entre pedido/estoque/pagamento.
Decisão: manter um único deploy; impor fronteiras entre apps com import-linter.
Alternativas: microsserviços (rejeitado: perde a transação, multiplica operação e
falhas de rede, sem time ou escala que o justifique).
Consequências: deploy e debug simples; disciplina de fronteiras vira responsabilidade do CI;
payments é o primeiro candidato a extração (porta + eventos já existem).
Gatilhos para rever: times independentes, escala desigual medida, ciclo de deploy conflitante.
```

## 🧠 Pausa para lógica
**Problema.** Um pedido síncrono chama 4 serviços, cada um com 99,95% de disponibilidade. Qual a disponibilidade combinada e quantos minutos fora do ar por mês (30 dias)?

<details><summary>Dica</summary>Multiplique as disponibilidades: <code>0,9995^4</code>.</details>

<details><summary>Solução comentada</summary>

`0,9995^4 ≈ 0,9980` → **99,80%**. Indisponibilidade `≈ 0,20% × 43 200 min ≈ 86 min/mês`. Cada serviço sozinho tem só ~22 min. Moral: a cadeia síncrona é **pior que o pior elo**; por isso se usam filas, cache e degradação graciosa.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| “Microsserviços” que compartilham o mesmo banco | Monolito distribuído | Ou um monolito modular, ou dados por serviço |
| Deploy de 5 serviços sempre juntos | Acoplamento de versões | Voltar a um deploy único |
| Cadeia de chamadas síncronas | Disponibilidade multiplicada | Eventos, cache, timeouts, *circuit breaker* |
| Apps importando uns aos outros em ciclo | Sem fronteiras | Contrato `layers` no import-linter |
| Migrar “porque a Netflix faz” | Cargo cult | Decidir por gatilhos medidos, registrar em ADR |

- **Comece modular**, extraia por motivo medido.
- **Fronteiras por contrato de CI**, não por boa vontade.
- **Registre decisões** em ADRs curtos, com gatilhos para revisá-las.

## 🧩 Exercícios
**1. Fixação.** (a) O que se perde ao separar pedido e estoque em serviços? (b) Por que microsserviços não consertam código bagunçado? (c) O que o contrato `layers` entre apps garante?

<details><summary>Solução</summary>

(a) A transação atômica única (passa-se a ter consistência eventual, sagas, idempotência). (b) Porque o problema é de fronteiras e responsabilidades, que a rede só torna mais caro. (c) Que os apps formam uma hierarquia sem ciclos: dependências só vão para baixo.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `.importlinter` com o contrato de apps em camadas e `lint-imports` verde
- [ ] Script de medição função vs HTTP com a saída no README do módulo
- [ ] `docs/adr/0002-monolito-modular.md` com gatilhos de revisão
- [ ] Commit `docs(adr): keep MiniShop a modular monolith`

**3. Desafio (opcional).** Introduza de propósito um import de `catalog` para `orders`, rode `lint-imports`, leia o erro e reverta.

## 🎤 Na entrevista
- **Monolito ou microsserviços?** Começo por monolito modular; microsserviços quando há times independentes, escala desigual ou ciclos de deploy conflitantes, medidos, porque trocam transação por consistência eventual e somam custo operacional.
- **Qual o principal custo de microsserviços?** Complexidade distribuída: rede que falha, observabilidade, versões, transações e deploy.
- **Como impedir que um monolito vire bagunça?** Fronteiras impostas por ferramenta (import-linter), camadas e revisão de ADRs.
- **O que é um monolito distribuído?** Serviços separados que precisam ser implantados juntos ou compartilham banco: o pior dos dois mundos.

## 📚 Para ir além
- 📄 Artigo: [Martin Fowler — MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html). Por que começar pelo monolito (em inglês).
- 📄 Artigo: [Martin Fowler — Microservices](https://martinfowler.com/articles/microservices.html). Características e custos (em inglês).
- 📄 Documentação: [import-linter](https://import-linter.readthedocs.io/en/stable/). Contratos de arquitetura.
- 📄 Artigo: [Architecture Decision Records](https://adr.github.io/). Formato e modelos de ADR.

## ✅ Checklist da aula
- [ ] Sei comparar monolito, monolito modular e microsserviços pelo custo
- [ ] Medi função vs HTTP e calculei disponibilidade combinada
- [ ] Imponho fronteiras entre apps com import-linter
- [ ] Escrevi um ADR com gatilhos de revisão
