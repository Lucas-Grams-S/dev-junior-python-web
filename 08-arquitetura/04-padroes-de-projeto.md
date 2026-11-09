# 4. Strategy, Factory, Repository e Adapter

> ⏱️ ~1h30 · Módulo 8 · Pré-requisitos: [8.02](02-services-repositories.md), [8.03](03-solid-dry-kiss-yagni.md), [7.04 (httpx, retentativas)](../07-sincrono-assincrono/04-httpx-timeouts-retries.md), [7.09 (webhooks)](../07-sincrono-assincrono/09-webhooks.md)

> ✅ **Verificação.** Código executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19, httpx 0.28.1): um **provedor de pagamento “Acme Pay” de mentira** (servidor HTTP próprio, com API, estados e assinatura diferentes) conversa com a API real, servida pelo Gunicorn. **As saídas são reais.** A suíte do laboratório chegou a **124 testes passando** (7 novos) e os **3 contratos de arquitetura** continuaram cumpridos. Nenhum gateway real foi usado.

## 🎯 Objetivos
Ao final desta aula você consegue:
- Reconhecer o **problema** que cada padrão resolve (e **não** usar padrão sem problema): **Strategy**, **Factory**, **Repository** e **Adapter**
- Escrever um **Adapter** para um serviço externo, traduzindo o **vocabulário do provedor** para o **do MiniShop** (estados, valores em centavos, assinatura de webhook)
- Escolher a implementação em tempo de execução com uma **fábrica** guiada por configuração
- Testar adaptadores **sem rede** (`MockTransport`) e garantir que todos falam a **mesma língua** (teste de contrato)
- Preferir **funções e dicionários** a hierarquias de classes quando bastam (o jeito Python)

## 🤔 Por que isso importa
Hoje o MiniShop fala com um “gateway” simulado. No dia em que a empresa fechar contrato com um provedor real (e, daqui a dois anos, **trocar** por outro mais barato), cada um terá **outra** API, **outros nomes de estado**, **outra assinatura** de webhook. Se o provedor estiver espalhado pelo código (`if provider == "acme"` por toda parte), trocar vira um projeto de semanas. Com um **Adapter**, é **uma classe nova e uma variável de ambiente**. Padrões de projeto aparecem em toda entrevista (“dê um exemplo de Adapter/Strategy”), e o exemplo bom é um que você **executou**.

## 💡 Intuição (explicação simples)
Em viagem, a tomada do hotel é de outro formato. Você não reforma o carregador: usa um **adaptador de tomada** (*Adapter*), que traduz um formato no outro. Para escolher **como** ir ao aeroporto (táxi, metrô, ônibus), você troca o “jeito de fazer a mesma coisa” conforme a situação (*Strategy*). Quem decide **qual** adaptador ou jeito usar, olhando o país ou o orçamento, é uma **recepção** (*Factory*). E o **guarda-volumes** (*Repository*) guarda e devolve a mala sem você saber em que prateleira ela fica.

## 🔬 Como funciona por dentro
| Padrão | Problema que resolve | Ideia | No MiniShop |
|---|---|---|---|
| **Strategy** | várias **formas de fazer a mesma coisa**, escolhidas em tempo de execução | cada variante atrás da **mesma interface**; o contexto só chama | formas de pagamento/desconto (aula 03), cálculo de frete por região |
| **Factory** | **quem cria** o objeto e **qual classe** instanciar | uma função/classe decide e entrega o objeto pronto | `obter_gateway()` (pelo `settings`) |
| **Repository** | acesso a dados **atrás de uma interface** substituível | “coleção” com métodos de negócio; adaptadores (ORM/memória) | `PedidoRepository` (aula 02) |
| **Adapter** | o sistema externo fala **outra língua** e você quer a **sua** | uma classe que **traduz** chamadas e dados entre dois vocabulários | `GatewayFake` e `GatewayAcme` |
- **Quando usar cada um (e quando não):**
  | Padrão | Use quando | Não use quando |
  |---|---|---|
  | Strategy | já há **3+ variantes** (ou a 3ª está chegando) | só existe uma regra (KISS/YAGNI, aula 03) |
  | Factory | a escolha da implementação depende de **config/ambiente** | sempre a mesma classe |
  | Repository | regras ricas e testes sem banco (aula 02) | CRUD simples |
  | Adapter | integra **terceiros** ou legado com modelo diferente | o seu próprio código já fala a sua língua |
- **Em Python, muitas vezes basta uma função.** *Strategy* costuma ser **uma função** ou um **dicionário de funções** (aula 03). Classes valem quando a variante tem **estado** (credenciais, `client` HTTP), como os adaptadores de gateway.
- **O Adapter, em detalhe (hexagonal / “portas e adaptadores”):** o **núcleo** (regras do MiniShop) define a **porta** (`PaymentGateway`, um `Protocol`) no **seu** vocabulário (`Cobranca`, `EventoPagamento` com tipos `paid|failed|refunded|ignored` e valor em `Decimal`). Cada **adaptador** conhece **um** provedor e faz três traduções:
  1. **Requisição:** valor `Decimal` → **centavos inteiros**, nomes de campo, cabeçalhos, **chave de idempotência**;
  2. **Resposta/estados:** `CAPTURED` → `paid`, `DECLINED` → `failed`, o que não interessa → `ignored`;
  3. **Webhook:** a **assinatura** do provedor (HMAC de um jeito, com ou sem timestamp), o formato do corpo e o **evento normalizado**.
  O núcleo **não importa** `httpx` nem sabe o que é “Acme”: a regra de dependência da aula 01 continua valendo.
- **Falhas fazem parte do contrato:** o adaptador traduz erros do provedor para **exceções suas** (`GatewayIndisponivel`), repete **só o transitório** e usa a **chave de idempotência** (aula 7.04), de modo que repetir **não cobra duas vezes**.
- **Teste de contrato entre adaptadores** (aula 03): os dois adaptadores, alimentados com eventos **equivalentes** no seu próprio dialeto, devem devolver o **mesmo** `EventoPagamento` normalizado.
- **Armadilhas:** “adaptador” que vaza o vocabulário do provedor para dentro do núcleo (o objeto de resposta cru da Acme circulando pelo sistema); fábrica com `if` para cada provedor espalhada em vários lugares (use **uma**); hierarquias profundas de estratégias quando um dicionário bastava.

## 🛠️ Exemplo prático
**1. A porta e os dois adaptadores** (`apps/payments/gateway.py`)
```python
"""PORTA (interface) para gateways de pagamento + ADAPTADORES por provedor + FÁBRICA que escolhe o adaptador pela configuração.

O resto do sistema só conhece `Cobranca` e `EventoPagamento` (o vocabulário DO MINISHOP); cada adaptador traduz de/para o vocabulário do provedor."""
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol

import httpx
from django.conf import settings

from .security import AssinaturaInvalida, verificar


@dataclass(frozen=True)
class Cobranca:
    ref: str                    # identificador da cobrança no provedor
    status: str = "pending"


@dataclass(frozen=True)
class EventoPagamento:
    id: str                     # id ÚNICO do evento (idempotência)
    tipo: str                   # vocabulário do MiniShop: "paid" | "failed" | "refunded" | "ignored"
    payment_ref: str
    valor: Decimal | None = None
    bruto: dict = field(default_factory=dict)


class GatewayIndisponivel(Exception):
    """O provedor não respondeu / respondeu com erro (transitório)."""


class PaymentGateway(Protocol):
    def criar_cobranca(self, order_id: int, valor: Decimal) -> Cobranca: ...
    def interpretar_webhook(self, cabecalhos, corpo: bytes) -> EventoPagamento: ...


# ----------------------------------------------------------------------------------------------- adaptador 1: o "fake" local
class GatewayFake:
    """Usado em desenvolvimento e nos testes: gera a referência localmente e fala o 'dialeto' da aula 7.09."""

    TIPOS = {"payment.succeeded": "paid", "payment.failed": "failed", "payment.refunded": "refunded"}

    def criar_cobranca(self, order_id, valor):
        return Cobranca(ref="pay_" + uuid.uuid4().hex[:16])

    def interpretar_webhook(self, cabecalhos, corpo):
        verificar(settings.WEBHOOK_SECRET, corpo, cabecalhos.get("X-Signature"))           # levanta AssinaturaInvalida
        bruto = json.loads(corpo)
        dados = bruto.get("data", {})
        valor = Decimal(str(dados["amount"])) if "amount" in dados else None
        return EventoPagamento(bruto["id"], self.TIPOS.get(bruto["type"], "ignored"), dados.get("payment_ref", ""), valor, bruto)


# ----------------------------------------------------------------------------------------------- adaptador 2: um provedor HTTP "Acme Pay"
class GatewayAcme:
    """Fala com o 'Acme Pay': outro formato de requisição (centavos), outros nomes de estado e OUTRA assinatura de webhook."""

    EVENTOS = {"charge.captured": "paid", "charge.declined": "failed", "charge.refunded": "refunded"}
    TOLERANCIA = 300

    def __init__(self, base_url, segredo_webhook, client=None):
        self.client = client or httpx.Client(base_url=base_url, timeout=httpx.Timeout(5, read=3))
        self.segredo = segredo_webhook

    def criar_cobranca(self, order_id, valor):
        corpo = {"amount_cents": int(valor * 100), "currency": "BRL", "reference": f"order-{order_id}"}
        chave = f"order-{order_id}"                                                         # idempotência: repetir NÃO cobra duas vezes
        for tentativa in range(3):
            try:
                r = self.client.post("/v1/charges", json=corpo, headers={"Idempotency-Key": chave})
            except (httpx.ConnectError, httpx.TimeoutException):
                r = None
            if r is not None and r.status_code in (200, 201):
                return Cobranca(ref=r.json()["charge_id"], status="pending")
            if r is not None and r.status_code < 500:
                raise GatewayIndisponivel(f"Acme recusou a cobrança: HTTP {r.status_code}")        # erro do pedido: não adianta repetir
            time.sleep(0.05 * 2 ** tentativa)
        raise GatewayIndisponivel("Acme indisponível após 3 tentativas")

    def interpretar_webhook(self, cabecalhos, corpo):
        recebida = cabecalhos.get("X-Acme-Signature", "")
        esperada = "sha256=" + hmac.new(self.segredo.encode(), corpo, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(esperada, recebida):
            raise AssinaturaInvalida("assinatura da Acme não confere")
        bruto = json.loads(corpo)
        if abs(time.time() - bruto["created"]) > self.TOLERANCIA:
            raise AssinaturaInvalida("evento antigo demais (replay?)")
        cobranca = bruto["charge"]
        return EventoPagamento(bruto["id"], self.EVENTOS.get(bruto["event"], "ignored"), cobranca["id"],
                               Decimal(cobranca["amount_cents"]) / 100, bruto)               # centavos → Decimal


# ----------------------------------------------------------------------------------------------- fábrica
def obter_gateway() -> PaymentGateway:
    """Escolhe o adaptador pela configuração (PAYMENT_GATEWAY): trocar de provedor é UMA variável de ambiente."""
    nome = getattr(settings, "PAYMENT_GATEWAY", "fake")
    if nome == "fake":
        return GatewayFake()
    if nome == "acme":
        return GatewayAcme(settings.ACME_BASE_URL, settings.ACME_WEBHOOK_SECRET)
    raise ValueError(f"PAYMENT_GATEWAY desconhecido: {nome!r}")
```
Leia a diferença entre os dois adaptadores: o **Fake** gera a referência localmente e entende o “dialeto” da aula 7.09 (`payment.succeeded`, valor como texto, assinatura com timestamp). O **Acme** manda `amount_cents` (inteiro), usa `Idempotency-Key`, repete `503` com a mesma chave, traduz `charge.captured` para `paid` e verifica uma assinatura **sem timestamp no cabeçalho** (o `created` vai no corpo). O núcleo só vê `Cobranca` e `EventoPagamento`.

**2. O núcleo ficou independente do provedor** (trechos)
```python
# apps/payments/api.py: o webhook não sabe quem é o provedor
evento = obter_gateway().interpretar_webhook(request.headers, corpo)     # verifica a assinatura e TRADUZ o dialeto
resultado, detalhe = processar_evento(evento)                            # a regra de negócio, igual para todos

# o início do pagamento
cobranca = obter_gateway().criar_cobranca(order.pk, order.total)         # o provedor é um DETALHE atrás da porta
p = services.criar_pagamento(order, cobranca.ref)
```
```python
# config/settings.py: trocar de provedor = trocar UMA variável
PAYMENT_GATEWAY = os.environ.get("PAYMENT_GATEWAY", "fake")               # "fake" | "acme"
ACME_BASE_URL = os.environ.get("ACME_BASE_URL", "http://127.0.0.1:8150")
ACME_WEBHOOK_SECRET = os.environ.get("ACME_WEBHOOK_SECRET", "acme_whsec_lab_apenas_para_estudo")
```
O `processar_evento` agora recebe um `EventoPagamento` (e não um dicionário cru): a idempotência, a ordem dos estados e a validação do valor **não mudaram**, e os testes de webhook da aula 7.09 **passaram sem alteração** (usam o adaptador *fake*).

**3. Trocando de provedor, de verdade** (`acme_demo.py`: o servidor “Acme Pay” roda num processo, a API do MiniShop no Gunicorn com `PAYMENT_GATEWAY=acme`)
```bash
LAB=$PWD PYTHONPATH=. uv run python acme_demo.py
```
```text
PAYMENT_GATEWAY=fake  → obter_gateway() devolve GatewayFake
PAYMENT_GATEWAY=acme  → obter_gateway() devolve GatewayAcme

pedido #1 total 114.60; POST /pay/ → ch_e522f166a4aa (pending)
  o MiniShop pediu a cobrança em centavos (11460); a Acme recebeu 2 requisição(ões): a 1ª deu 503 e o adaptador REPETIU com a mesma Idempotency-Key
  cobranças criadas na Acme: 1 (uma só, apesar da repetição)

webhooks no dialeto da Acme (evento 'charge.captured', valor em centavos, outra assinatura):
  1) charge.captured válido                                  → 200 processed
      estado: pedido=paid, pagamento=paid
  2) o MESMO corpo de novo (duplicata)                       → 200 duplicate
  3) assinatura inválida                                     → 401 invalid_signature
  4) assinado com o segredo do MiniShop (outro dialeto!)     → 401 invalid_signature
  5) evento antigo (replay, 10 min)                          → 401 invalid_signature
  6) charge.authorized (a Acme tem, nós não usamos)          → 200 ignored
  7) charge.declined depois do captured (fora de ordem)      → 200 ignored

auditoria (WebhookEvent):
  paid      processed  pagamento paid
  ignored   ignored    tipo sem efeito: ignored
  failed    ignored    fora de ordem: já está paid, chegou failed
```
- **Fábrica:** com `PAYMENT_GATEWAY=fake` ou `acme`, `obter_gateway()` devolve outro adaptador; **nenhuma outra linha** muda.
- **Cobrança:** o MiniShop pediu **11460 centavos** (e não `114.60`); a Acme recebeu **2 requisições** (a 1ª deu `503`), o adaptador **repetiu com a mesma `Idempotency-Key`** e a Acme criou **uma só** cobrança: nada cobrado em dobro.
- **Webhooks no dialeto da Acme:** `charge.captured` → o pedido virou `paid`; a **duplicata** foi reconhecida; **assinatura inválida**, assinatura com o **segredo do MiniShop** (outro dialeto) e **evento antigo** (*replay*) foram `401`; `charge.authorized` (estado que a Acme tem e nós não usamos) foi **ignorado**; e o `charge.declined` **fora de ordem** não desfez o pagamento. A tabela de auditoria mostra que a **regra de negócio é a mesma** da aula 7.09, só que alimentada por outro provedor.

**4. Os testes do Adapter, sem rede** (`tests/test_gateway.py`)
```python
def test_cobranca_repete_503_com_a_mesma_chave_e_converte_para_centavos():
    vistas = []
    def h(req):
        vistas.append((req.headers["Idempotency-Key"], json.loads(req.content)["amount_cents"]))
        return httpx.Response(503) if len(vistas) == 1 else httpx.Response(201, json={"charge_id": "ch_9"})
    assert acme(h).criar_cobranca(7, Decimal("114.60")).ref == "ch_9"
    assert vistas == [("order-7", 11460), ("order-7", 11460)]


def test_ambos_os_adaptadores_falam_o_mesmo_vocabulario(settings):
    ...
    assert ev_fake.tipo == ev_acme.tipo == "paid" and ev_fake.valor == ev_acme.valor == Decimal("10")
```
```bash
uv run pytest -q
uv run lint-imports
```
```text
124 passed
Contracts: 3 kept, 0 broken.
```
Os 7 testes novos cobrem: repetição do `503` com a **mesma chave** e conversão para **centavos**; `4xx` **não** repetido e `5xx` esgotando as tentativas; tradução do webhook da Acme para o vocabulário do MiniShop; rejeição de **assinatura errada** e de **replay**; o **teste de contrato** (dois dialetos, mesmo evento normalizado) e a **fábrica** (escolha pelo `settings` e erro para nome desconhecido). Nenhum abriu uma conexão de rede: o `MockTransport` do `httpx` fez o papel da Acme.

**5. Strategy e Factory em Python, sem cerimônia**
Revise o `ocp.py` da aula 03: as formas de pagamento eram **estratégias** (funções num dicionário) escolhidas por **nome**, isto é, uma **fábrica** muito simples. Para um provedor com **estado** (um `client` HTTP, um segredo), a variante vira **classe** (o adaptador). A regra prática: **comece com função; promova a classe quando houver estado**.

## 🧠 Pausa para lógica
**Problema (tradutor de estados).** Escreva um `adaptar(evento_acme)` que receba o dicionário do webhook da Acme (`{"event": "charge.captured", "charge": {"id": ..., "amount_cents": 11460}}`) e devolva `("paid", "ch_1", Decimal("114.60"))`, tratando **estado desconhecido** como `"ignored"` **sem** levantar exceção, e **centavos inteiros** sem usar `float`. Prove com uma tabela de casos.

<details><summary>Dica</summary>
Um dicionário <code>EVENTOS = {"charge.captured": "paid", ...}</code> com <code>.get(evento, "ignored")</code>. Para o valor, <code>Decimal(cents) / 100</code> (inteiro dividido por 100 em <code>Decimal</code>), nunca <code>cents / 100</code> com <code>float</code>.
</details>

<details><summary>Solução comentada</summary>

É o trecho `interpretar_webhook` do `GatewayAcme` (exemplo 1): `self.EVENTOS.get(bruto["event"], "ignored")` e `Decimal(cobranca["amount_cents"]) / 100`. Dois detalhes importantes: (1) um estado **desconhecido** não pode derrubar o webhook (o provedor passa a acrescentar eventos novos sem avisar); responda `200` e registre; (2) `float(11460) / 100` daria `114.6` mas valores como `0.07` e somas **acumulam erro**: dinheiro é `Decimal` (aula 5.16).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| `if provedor == "acme"` espalhado pelo código | Sem Adapter/fábrica | Adaptador por provedor + **uma** fábrica |
| O objeto de resposta cru do provedor circula pelo sistema | Adaptador “vazando” | Converter na borda para o tipo do **seu** domínio |
| Cobrança duplicada depois de um retry | Sem `Idempotency-Key` | Chave estável por pedido; repetir só o transitório |
| Webhook derrubado por evento novo do provedor | `KeyError`/`ValueError` em estado desconhecido | `.get(..., "ignored")` e `200` |
| Valor em centavos tratado como reais (ou o contrário) | Falta de conversão explícita na borda | `Decimal(cents) / 100` e `int(valor * 100)` **só** no adaptador, com teste |
| Fábrica com `ValueError: PAYMENT_GATEWAY desconhecido` em produção | Variável de ambiente errada | Falhar **cedo** na inicialização (verificação no `AppConfig.ready()`/`check`) |
| Teste do adaptador depende da rede | Sem `MockTransport`/*fake* do servidor | Injetar o `client` no adaptador (construtor) |
| Hierarquia `BaseGateway` → `HttpGateway` → `AcmeGateway` | Herança desnecessária | Composição + `Protocol` |
| Padrão “porque o livro mandou” | Resume-driven design | Só quando o problema existe (YAGNI) |

- **Nomeie pelo papel** (`PaymentGateway`, `PedidoRepository`), não pelo padrão (`GatewayAdapterFactoryImpl`).
- **O adaptador é o único lugar que conhece o provedor**: documentação, mapeamento de estados e peculiaridades ficam ali.
- **Teste de contrato** para todo conjunto de adaptadores da mesma porta.
- **Segredos** do provedor em variáveis de ambiente (aula 5.14), nunca no repositório.
- **Registre** o provedor escolhido numa decisão de arquitetura (ADR, aula 05).

## 🧩 Exercícios
**1. Fixação**
(a) Qual problema cada um resolve: Strategy, Factory, Repository, Adapter? (b) Por que o adaptador converte para o vocabulário do MiniShop em vez de devolver a resposta do provedor? (c) Por que a chave de idempotência importa no adaptador? (d) Quando uma função basta em vez de uma classe?

<details><summary>Solução</summary>

(a) Strategy: variantes intercambiáveis do mesmo comportamento; Factory: escolher/criar a implementação; Repository: acesso a dados atrás de uma interface; Adapter: traduzir uma interface externa para a que o sistema espera. (b) Para que o núcleo não dependa do provedor (trocar de provedor não toca o núcleo). (c) Retentativas de cobrança sem chave podem cobrar o cliente duas vezes. (d) Quando a variante não tem estado nem precisa de várias operações: uma função (ou um dicionário de funções) já cumpre a interface.
</details>

**2. Aplicação no projeto MiniShop**
Entregue o **Adapter para o gateway de pagamento** (parte da entrega do módulo).

Critérios de pronto:
- [ ] `PaymentGateway` (`Protocol`) com `criar_cobranca` e `interpretar_webhook`, e os tipos normalizados `Cobranca` e `EventoPagamento`
- [ ] Adaptadores `GatewayFake` e um segundo (`GatewayAcme` ou outro provedor simulado seu) com dialetos **diferentes** (assinatura, valor, estados)
- [ ] `obter_gateway()` guiado por `PAYMENT_GATEWAY`, falhando com mensagem clara para nome desconhecido
- [ ] `processar_evento` recebendo o evento **normalizado**; os testes de webhook antigos passam **sem alteração**
- [ ] Testes do adaptador **sem rede** (`MockTransport`): retentativa com a mesma chave, `4xx` sem repetir, assinatura/replay, tradução de estados e valores
- [ ] Teste de **contrato** entre os adaptadores e teste da fábrica
- [ ] `lint-imports` com os contratos cumpridos (o núcleo não importa `httpx` nem o provedor)
- [ ] `docs/adr/0001-gateway-de-pagamento.md`: contexto, decisão (Adapter + fábrica), alternativas (chamar o provedor direto) e consequências
- [ ] Commit `feat(payments): payment gateway port with Fake and Acme adapters`

<details><summary>Solução de referência (ADR)</summary>

```markdown
# ADR 0001: Gateway de pagamento atrás de uma porta (Adapter)
Status: aceito · Data: 2026-11-08
Contexto: o provedor ainda não está definido e pode mudar; cada um tem API, estados e assinatura diferentes.
Decisão: `PaymentGateway` (Protocol) no vocabulário do MiniShop; um adaptador por provedor; `obter_gateway()` escolhe por `PAYMENT_GATEWAY`.
Alternativas: chamar a API do provedor direto das views/serviços (rápido, mas acopla tudo e dificulta trocar/testar).
Consequências: +1 classe por provedor e testes de contrato; trocar de provedor = novo adaptador + variável de ambiente; o núcleo não conhece `httpx`.
```
</details>

**3. Desafio (opcional)**
Acrescente **um terceiro provedor** (“Beta Pay”) cuja API **só aceita `GET` com os parâmetros na URL** e cuja assinatura usa **HMAC-SHA512** com o timestamp no cabeçalho. Escreva o adaptador, os testes e mostre que **nenhuma linha** do núcleo (`services`, `api`) precisou mudar.

## 🎤 Na entrevista
- **Dê um exemplo de Adapter.** O adaptador de gateway de pagamento: define uma interface do MiniShop (`criar_cobranca`, `interpretar_webhook`) e, para cada provedor, uma classe que traduz requisições, estados, valores e assinaturas, para o núcleo não depender de nenhum provedor.
- **Qual a diferença entre Strategy e Factory?** Strategy encapsula **variantes de um comportamento** intercambiáveis; Factory decide **qual** objeto criar. Costumam andar juntos: a fábrica escolhe a estratégia.
- **Repository ou ORM direto?** Repository quando há regras ricas, necessidade de testes sem banco ou troca de persistência; ORM direto em CRUD simples.
- **Como você troca de provedor de pagamento sem reescrever o sistema?** Com uma porta e adaptadores: escreve-se um novo adaptador, ajusta-se a configuração da fábrica e roda-se o teste de contrato.
- **Padrões de projeto sempre valem a pena?** Não: cada padrão custa abstração; só se justifica quando o problema (variantes, acoplamento a terceiros, testes lentos) existe.

## 📚 Para ir além
- 📄 Catálogo: [Refactoring Guru — Adapter](https://refactoring.guru/design-patterns/adapter). Estrutura e exemplos.
- 📄 Catálogo: [Refactoring Guru — Strategy](https://refactoring.guru/design-patterns/strategy). Variantes intercambiáveis.
- 📄 Catálogo: [Refactoring Guru — Factory Method](https://refactoring.guru/design-patterns/factory-method). Quem cria o objeto.
- 📄 Artigo: [Alistair Cockburn — Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/). Portas e adaptadores (em inglês).
- 📘 Livro gratuito: [Cosmic Python — Dependency Injection](https://www.cosmicpython.com/book/chapter_13_dependency_injection.html). Compondo adaptadores (em inglês).
- 📄 Documentação oficial: [`functools`](https://docs.python.org/3/library/functools.html). `partial`, `singledispatch`: estratégias sem classes.
- 🏋️ Prática extra: rode o `acme_demo.py` com `PAYMENT_GATEWAY=fake` e veja o que falha (e por quê).

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Sei dizer o problema que cada padrão resolve e quando **não** usá-lo
- [ ] Escrevi um Adapter que traduz requisição, estados, valores e assinatura
- [ ] Troquei de provedor mudando uma variável de ambiente
- [ ] Testei o adaptador sem rede e com um teste de contrato
- [ ] O núcleo continua sem importar `httpx` nem o provedor (contratos verdes)
