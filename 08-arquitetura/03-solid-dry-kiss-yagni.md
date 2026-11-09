# 3. SOLID, DRY, KISS e YAGNI em Python

> ⏱️ ~1h30 · Módulo 8 · Pré-requisitos: [8.01](01-responsabilidades-camadas.md), [8.02](02-services-repositories.md), [1.12 a 1.14 (classes, herança, métodos especiais)](../01-python-logica/12-poo-classes.md)

> ✅ **Verificação.** Todos os exemplos foram executados em 2026-11-08 (Python 3.13, Django 5.2.19) sobre o código real do MiniShop; ferramentas: `mypy` 2.4.1, `radon` 6.0.1 e `ruff` 0.17.4. **As saídas são reais.** O laboratório terminou a aula com **117 testes passando** (10 novos: o teste de contrato do repositório, que roda contra os **dois** adaptadores).

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar os cinco princípios **SOLID** com **exemplos em Python** (e onde eles já estão no MiniShop)
- Aplicar **Aberto/Fechado** trocando `if/elif` por estratégias registradas, e **Liskov** com um **teste de contrato**
- Usar `typing.Protocol` e o `mypy` para **segregar interfaces** e verificar a **inversão de dependência**
- Distinguir **DRY** (duplicação de *conhecimento*) de código parecido por acaso, e eliminar duplicações **reais**
- Aplicar **KISS** e **YAGNI** com **números** (linhas, complexidade, manutenibilidade) e reconhecer a abstração errada

## 🤔 Por que isso importa
“Conhece SOLID?” é a pergunta mais clássica de entrevista de desenvolvimento, e a pior resposta é recitar as siglas sem exemplo. A melhor é mostrar **onde o princípio resolveu um problema real**. Mas há o outro lado: aplicar padrões por reflexo gera **código mais difícil de ler que o problema original**. Esta aula entrega os dois lados: os princípios **e** a régua (KISS, YAGNI) para não exagerar.

## 💡 Intuição (explicação simples)
Pense numa **caixa de ferramentas bem organizada**. **S**: cada ferramenta serve a **uma** coisa (a chave de fenda não vira martelo). **O**: para um parafuso novo, você **acrescenta uma ponta** ao kit, sem serrar a chave de fenda. **L**: qualquer ponta que encaixe no cabo tem de **funcionar como as outras**: uma ponta que “encaixa, mas quebra o parafuso” é um defeito. **I**: o cabo de uma chave não exige que você leve a furadeira junto. **D**: o cabo aceita **qualquer** ponta (depende do encaixe, não de uma ponta específica). E duas regras de bom senso: **DRY** (não escreva o mesmo manual em dez gavetas) e **KISS/YAGNI** (não compre uma furadeira industrial para pendurar um quadro).

## 🔬 Como funciona por dentro
| Princípio | Em uma frase | Sinal de violação | Onde aparece no MiniShop |
|---|---|---|---|
| **S**RP: responsabilidade única | uma classe/função tem **uma razão para mudar** | “e” na descrição (“valida **e** grava **e** envia e-mail”) | `create_order` dividido em domínio/serviço/repositório (aula 02) |
| **O**CP: aberto/fechado | **estender** sem **modificar** o código que funciona | `if/elif` que cresce a cada novidade | formas de pagamento e cupons (abaixo) |
| **L**SP: substituição de Liskov | um subtipo pode ocupar o lugar do tipo **sem quebrar** as promessas | subclasse que levanta `NotImplementedError` ou “enfraquece” o resultado | `MemoriaPedidoRepository` × `DjangoPedidoRepository` |
| **I**SP: segregação de interfaces | ninguém depende de métodos que não usa | *fake* com 7 métodos para testar 1 | porta pequena (`LeitorDeProdutos`) vs `PedidoRepository` |
| **D**IP: inversão de dependência | alto nível depende de **abstrações**, não de detalhes | serviço importando `httpx`, `channels`, ORM direto | `create_order(user, repo)`; `pedido_pago` (sinal) |

- **SRP não é “uma função por classe”**: é “**uma razão** para mudar”. As razões do `processar_pedido` legado: regra de cupom, regra de pagamento, regra de frete, persistência, log e estoque: **seis** razões na mesma função.
- **OCP em Python** costuma ser um **dicionário de funções** (registro), uma classe-base com subclasses ou funções de ordem superior: não precisa de hierarquias pesadas.
- **LSP** é sobre **contrato**: pré-condições (o que o chamador deve garantir), pós-condições (o que o método promete) e invariantes. O subtipo pode **aceitar mais** e **prometer mais**, nunca **exigir mais** nem **prometer menos**. A ferramenta prática é o **teste de contrato**: as **mesmas asserções** rodando contra **todas** as implementações.
- **ISP em Python** é fácil com **`typing.Protocol`** (tipagem estrutural, “de pato”): cada consumidor declara **só** o que usa, e o `mypy` confere. Interfaces enxutas = *fakes* de 3 linhas.
- **DIP ≠ injeção de dependência** (mas se ajudam): DIP é a **direção** das dependências (alto nível → abstração ← detalhe); injeção é **como** você entrega a dependência (parâmetro, construtor).
- **DRY** (*Don't Repeat Yourself*): “cada **conhecimento** deve ter **uma representação única**”. Não é “código parecido”: é **a mesma decisão escrita duas vezes**. Duplicação **real**: a mesma regra, a mesma constante, a mesma consulta em dois lugares (muda um, esquece o outro). Duplicação **acidental**: dois trechos parecidos que mudam por **razões diferentes**; unificá-los cria a **abstração errada** (“duplicação é muito mais barata que a abstração errada”).
- **KISS** (*Keep It Simple*): entre duas soluções que resolvem o problema, fique com a mais simples. **YAGNI** (*You Aren't Gonna Need It*): não construa o que **ainda** ninguém pediu. A flexibilidade que você “pode precisar” tem **custo imediato** (código, testes, leitura) e **valor hipotético**.
- **Como equilibrar:** aplique um princípio **quando a dor aparece** (o `if/elif` já tem 3 ramos e o 4º vem aí; a duplicação já gerou um bug), não por antecipação. A **regra dos três**: a primeira vez, escreva; a segunda, copie com desconforto; a terceira, **refatore**.
- **Ferramentas que ajudam:** `ruff` com a regra **C901** (complexidade `mccabe`) falha a CI quando uma função passa de um limite; `mypy` confere `Protocol`s; `radon mi` mede a **manutenibilidade**.

## 🛠️ Exemplo prático
**1. OCP: formas de pagamento sem `if/elif`** (`ocp.py`)
```python
"""Aberto para extensão, fechado para modificação: adicionar uma forma de pagamento SEM editar o código existente."""
from decimal import Decimal

D = Decimal


# ---------------------------------------------------------------- ANTES: if/elif (cada novidade EDITA esta função)
def desconto_antes(forma, total):
    if forma == "pix":
        return total * D("0.05")
    elif forma == "cartao":
        return D("0")
    elif forma == "boleto":
        return D("-2.50")                       # na verdade uma taxa de R$ 2,50
    else:
        raise ValueError(f"forma de pagamento inválida: {forma}")


# ---------------------------------------------------------------- DEPOIS: estratégias registradas
REGRAS = {}


def forma_de_pagamento(nome):
    def registrar(fn):
        REGRAS[nome] = fn
        return fn
    return registrar


@forma_de_pagamento("pix")
def _pix(total):
    return total * D("0.05")


@forma_de_pagamento("cartao")
def _cartao(total):
    return D("0")


@forma_de_pagamento("boleto")
def _boleto(total):
    return D("-2.50")


def desconto(forma, total):                      # NÃO muda nunca mais
    try:
        return REGRAS[forma](total)
    except KeyError:
        raise ValueError(f"forma de pagamento inválida: {forma}") from None


# 1) o comportamento é IDÊNTICO ao de antes?
casos = [(f, D(t)) for f in ("pix", "cartao", "boleto") for t in ("10.00", "199.99", "1234.56")]
iguais = all(desconto_antes(f, t) == desconto(f, t) for f, t in casos)
print(f"equivalência em {len(casos)} casos (3 formas × 3 totais): {iguais}")
for f in ("pix", "cartao", "boleto"):
    print(f"  {f:<7} sobre R$ 200,00 → desconto {desconto(f, D('200')):>7}")
try:
    desconto("cheque", D("10"))
except ValueError as e:
    print("forma desconhecida →", e)

# 2) EXTENSÃO: um módulo NOVO acrescenta a forma 'fidelidade', sem tocar em `desconto` nem nas outras
@forma_de_pagamento("fidelidade")
def _fidelidade(total):
    return total * D("0.03")


print("\napós registrar 'fidelidade' em OUTRO lugar do código:")
print("  formas conhecidas:", sorted(REGRAS))
print(f"  fidelidade sobre R$ 200,00 → desconto {desconto('fidelidade', D('200'))}  (nenhuma linha existente foi editada)")
```
```text
equivalência em 9 casos (3 formas × 3 totais): True
  pix     sobre R$ 200,00 → desconto   10.00
  cartao  sobre R$ 200,00 → desconto       0
  boleto  sobre R$ 200,00 → desconto   -2.50
forma desconhecida → forma de pagamento inválida: cheque

após registrar 'fidelidade' em OUTRO lugar do código:
  formas conhecidas: ['boleto', 'cartao', 'fidelidade', 'pix']
  fidelidade sobre R$ 200,00 → desconto 6.00  (nenhuma linha existente foi editada)
```
- Nos 9 casos, a versão com **registro** devolve **exatamente** o mesmo que o `if/elif` (**refatorar = mesmo comportamento**).
- A forma `fidelidade` foi acrescentada **em outro lugar** (poderia ser outro módulo ou *plugin*) **sem editar** `desconto` nem as demais: o código que já funcionava **não foi tocado**, então não pode ter sido quebrado.
- Como achar candidatos no seu código: o `ocp_smell.py` procura cadeias `if/elif` sobre a **mesma expressão** com 3 ou mais valores:
```bash
uv run python ocp_smell.py legado/
```
```text
legado/pedidos_legado.py:45  if/elif sobre "dados.get('forma_pgto')" com 3 valores: ['pix', 'cartao', 'boleto']
legado/pedidos_legado.py:34  if/elif sobre "dados['cupom']" com 3 valores: ['PROMO10', 'PROMO20', 'FRETEGRATIS']
2 cadeia(s) suspeita(s)
```
Ele achou **exatamente** as duas cadeias do código herdado (cupom e forma de pagamento), e **nenhuma** em `apps/`. As próprias regras de preço do legado viram **estratégias** na aula 07.

**2. LSP: o teste de contrato** (`tests/test_contrato_repositorio.py`: **as mesmas asserções** contra o repositório em memória **e** o do banco)
```python
@pytest.fixture(params=["memoria", "django"])
def cenario(request, db, cliente):
    """Monta o MESMO cenário nos dois adaptadores: usuário com 2 unidades do produto 'INF-002' no carrinho."""
    ...


def test_baixar_estoque_so_se_houver(cenario):
    repo, _, pid = cenario
    with repo.transacao():
        assert repo.baixar_estoque(pid, 5) is True            # exatamente o que há
        assert repo.baixar_estoque(pid, 1) is False           # acabou: recusa em vez de ficar negativo
    assert estoque(repo, pid) == 0


def test_transacao_desfaz_o_que_foi_feito_se_der_erro(cenario):
    repo, _, pid = cenario
    with pytest.raises(RuntimeError):
        with repo.transacao():
            assert repo.baixar_estoque(pid, 3)
            raise RuntimeError("falha no meio")
    assert estoque(repo, pid) == 5                            # o rollback restaurou o estoque nos DOIS adaptadores
```
```bash
uv run pytest -q tests/test_contrato_repositorio.py
```
```text
..........                                                               [100%]
10 passed in 3.91s
```
(5 testes × 2 adaptadores = 10 execuções.) Os dois adaptadores **cumprem** as mesmas promessas: é o que permite **trocar** um pelo outro no `create_order`. E um substituto que **quebra** o contrato? (`lsp.py`)
```python
"""Princípio de Liskov: um substituto NÃO PODE quebrar o que o contrato promete. O teste de contrato pega o infrator."""
from decimal import Decimal

from apps.orders.domain import ItemCarrinho, ProdutoInfo
from apps.orders.repositories import MemoriaPedidoRepository


def contrato(fabrica):
    """Roda as promessas da porta contra QUALQUER implementação. Devolve a lista de promessas quebradas."""
    quebradas = []
    def checa(nome, fn):
        try:
            if not fn():
                quebradas.append(nome)
        except Exception as e:
            quebradas.append(f"{nome} (levantou {type(e).__name__}: {e})")

    r = fabrica()
    with r.transacao():
        checa("baixar_estoque devolve True quando há estoque", lambda: r.baixar_estoque(1, 5) is True)
        checa("baixar_estoque devolve False quando NÃO há estoque (nunca fica negativo)", lambda: r.baixar_estoque(1, 1) is False)
    r = fabrica()
    checa("travar_produtos ignora ids inexistentes", lambda: set(r.travar_produtos([1, 999])) == {1})
    r = fabrica()
    try:
        with r.transacao():
            r.baixar_estoque(1, 3)
            raise RuntimeError("falha")
    except RuntimeError:
        pass
    checa("a transação desfaz tudo se houver erro", lambda: r.travar_produtos([1])[1].estoque == 5)
    return quebradas


def fabrica_ok():
    return MemoriaPedidoRepository(carrinhos={}, produtos={1: ProdutoInfo(1, "Mouse", Decimal("59.90"), 5, True)})


class Guloso(MemoriaPedidoRepository):
    """VIOLA a pós-condição: aceita baixar mais do que existe (estoque negativo)."""
    def baixar_estoque(self, product_id, quantidade):
        p = self.produtos[product_id]
        self.produtos[product_id] = ProdutoInfo(p.id, p.nome, p.preco, p.estoque - quantidade, p.ativo)
        return True


class SomenteLeitura(MemoriaPedidoRepository):
    """VIOLA o contrato: 'é um repositório', mas não sabe escrever."""
    def baixar_estoque(self, product_id, quantidade):
        raise NotImplementedError("somente leitura")


class SemRollback(MemoriaPedidoRepository):
    """VIOLA a promessa de atomicidade."""
    def transacao(self):
        from contextlib import nullcontext
        return nullcontext()


def com(cls):
    return lambda: cls(carrinhos={}, produtos={1: ProdutoInfo(1, "Mouse", Decimal("59.90"), 5, True)})


for nome, fab in [("MemoriaPedidoRepository (o original)", fabrica_ok), ("Guloso", com(Guloso)),
                  ("SomenteLeitura", com(SomenteLeitura)), ("SemRollback", com(SemRollback))]:
    q = contrato(fab)
    print(f"{nome:<38} → {'cumpre o contrato' if not q else 'QUEBRA ' + str(len(q)) + ' promessa(s)'}")
    for item in q:
        print(f"      ✘ {item}")
```
```text

MemoriaPedidoRepository (o original)   → cumpre o contrato
Guloso                                 → QUEBRA 1 promessa(s)
      ✘ baixar_estoque devolve False quando NÃO há estoque (nunca fica negativo)
SomenteLeitura                         → QUEBRA 2 promessa(s)
      ✘ baixar_estoque devolve True quando há estoque (levantou NotImplementedError: somente leitura)
      ✘ baixar_estoque devolve False quando NÃO há estoque (nunca fica negativo) (levantou NotImplementedError: somente leitura)
SemRollback                            → QUEBRA 1 promessa(s)
      ✘ a transação desfaz tudo se houver erro
```
- O **`Guloso`** “funciona” (devolve `True`) mas **aceita estoque negativo**: viola a **pós-condição** “recuso quando não há”. Passaria em testes que só conferem “não deu erro”, e **venderia o que não existe**.
- O **`SomenteLeitura`** é “um repositório” que **explode** ao escrever (`NotImplementedError`): o clássico “subclasse que não sabe fazer o que o pai promete”.
- O **`SemRollback`** viola a promessa de **atomicidade**: o teste do contrato é o único que o pega (e foi o *bug* do *fake* ingênuo da aula 02).
Moral: **herdar/implementar uma interface é assumir as promessas dela**.

**3. ISP + DIP: interfaces pequenas, verificadas pelo `mypy`** (`isp.py`)
```python
"""Segregação de interfaces: dependa SÓ do que usa. O mypy verifica de verdade (a porta é um Protocol)."""
from decimal import Decimal
from typing import Protocol


class PedidoRepository(Protocol):                 # a porta "gorda" (7 métodos), como em apps/orders/repositories.py
    def travar_produtos(self, ids: list[int]) -> dict[int, "Produto"]: ...
    def baixar_estoque(self, product_id: int, quantidade: int) -> bool: ...
    def criar_pedido(self, user: str, total: Decimal) -> object: ...
    def esvaziar_carrinho(self, carrinho: object) -> None: ...


class Produto:
    def __init__(self, nome: str, estoque: int) -> None:
        self.nome, self.estoque = nome, estoque


class LeitorDeProdutos(Protocol):                 # a interface MÍNIMA que um relatório de estoque realmente precisa
    def travar_produtos(self, ids: list[int]) -> dict[int, Produto]: ...


def relatorio_de_estoque(leitor: LeitorDeProdutos, ids: list[int]) -> list[str]:
    return [f"{p.nome}: {p.estoque}" for p in leitor.travar_produtos(ids).values()]


class FakeSoDeLeitura:                            # tem APENAS o método que o relatório usa
    def travar_produtos(self, ids: list[int]) -> dict[int, Produto]:
        return {1: Produto("Mouse", 5)}


class SemOMetodo:
    def listar(self) -> list[int]:
        return []


print(relatorio_de_estoque(FakeSoDeLeitura(), [1]))       # ok: o fake é minúsculo (3 linhas), não precisa implementar 7 métodos
print(relatorio_de_estoque(SemOMetodo(), [1]))            # o mypy deve apontar o erro AQUI, antes de rodar
```
```bash
uv add --dev mypy
uv run mypy isp.py
```
```text
../m8/isp.py:37: error: Argument 1 to "relatorio_de_estoque" has incompatible type "SemOMetodo"; expected "LeitorDeProdutos"  [arg-type]
Found 1 error in 1 file (checked 1 source file)
```
O relatório de estoque só precisa de **um** método, e declarou **só ele** (`LeitorDeProdutos`): o *fake* tem **3 linhas** em vez de implementar a porta inteira, e o `mypy` **pegou, sem rodar nada**, o objeto que não tem o método. Isso é **tipagem estrutural**: não há herança; basta “ter a forma”. (O módulo 10 aprofunda tipos e qualidade.)

**4. DRY: duplicações reais do MiniShop** (`duplicados.py`: janelas de 4 linhas normalizadas)
```bash
LAB=$PWD uv run python duplicados.py 4
```
```text
janela de 4 linhas: 1 trecho(s) repetido(s) em 55 arquivos

● repetido 2× em: apps/orders/tasks.py:124, apps/orders/management/commands/reenviar_emails_falhos.py:11
      ids = list(EmailLog.objects.filter(status=EmailLog.Status.FAILED).values_list("order_id", flat=True)
      EmailLog.objects.filter(order_id__in=ids, status=EmailLog.Status.FAILED).update(status=EmailLog.Stat
      for i in ids:
```
Duplicação **real**, herdada das aulas 7.07 e 7.08: o comando `reenviar_emails_falhos` e a tarefa Celery de mesmo nome tinham **o mesmo corpo**: mudar a regra num lugar e esquecer o outro era questão de tempo. A correção é **uma implementação e duas portas de entrada**:
```python
# apps/orders/management/commands/reenviar_emails_falhos.py
from apps.orders.tasks import reenviar_emails_falhos

class Command(BaseCommand):
    help = "Recoloca na fila os e-mails que falharam (depois de corrigir a causa)."

    def handle(self, *args, **opts):
        n = reenviar_emails_falhos()                  # UMA implementação, duas portas de entrada (tarefa agendada e comando)
        self.stdout.write(f"{n} e-mail(s) reenfileirado(s)")
```
Um segundo caso, mais sutil: o **limite de 20 unidades** estava escrito em dois lugares (`QUANTIDADE_MAXIMA = 20` no serviço e `max_value=20` nos serializadores). Mesma **decisão de negócio**, duas cópias; os serializadores passaram a importar a constante do serviço (**fonte única da verdade**). Depois das duas correções:
```text
janela de 4 linhas: 0 trecho(s) repetido(s) em 55 arquivos
```
Os **117 testes** (incluindo o do `schema.yml` commitado: o contrato OpenAPI não mudou) continuaram verdes.

**5. KISS e YAGNI, com números** (`frete_simples.py` × `frete_enterprise.py`: a **mesma** regra “frete grátis a partir de R$ 200, senão R$ 19,90”)
```python
from decimal import Decimal

FRETE_PADRAO = Decimal("19.90")
LIMITE_FRETE_GRATIS = Decimal("200.00")


def calcular_frete(subtotal: Decimal) -> Decimal:
    """Frete grátis a partir de R$ 200,00; senão, R$ 19,90."""
    return Decimal("0") if subtotal >= LIMITE_FRETE_GRATIS else FRETE_PADRAO
```
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ConfiguracaoDeFrete:
    valor_padrao: Decimal = Decimal("19.90")
    limite_gratis: Decimal = Decimal("200.00")


class EstrategiaDeFrete(ABC):
    def __init__(self, configuracao: ConfiguracaoDeFrete) -> None:
        self._configuracao = configuracao

    @abstractmethod
    def calcular(self, subtotal: Decimal) -> Decimal:
        raise NotImplementedError


class EstrategiaDeFreteGratis(EstrategiaDeFrete):
    def calcular(self, subtotal: Decimal) -> Decimal:
        return Decimal("0")


class EstrategiaDeFretePadrao(EstrategiaDeFrete):
    def calcular(self, subtotal: Decimal) -> Decimal:
        return self._configuracao.valor_padrao


class FabricaDeEstrategiasDeFrete:
    def __init__(self, configuracao: Optional[ConfiguracaoDeFrete] = None) -> None:
        self._configuracao = configuracao or ConfiguracaoDeFrete()

    def criar(self, subtotal: Decimal) -> EstrategiaDeFrete:
        if subtotal >= self._configuracao.limite_gratis:
            return EstrategiaDeFreteGratis(self._configuracao)
        return EstrategiaDeFretePadrao(self._configuracao)


class CalculadoraDeFrete:
    def __init__(self, fabrica: Optional[FabricaDeEstrategiasDeFrete] = None) -> None:
        self._fabrica = fabrica or FabricaDeEstrategiasDeFrete()

    def calcular(self, subtotal: Decimal) -> Decimal:
        return self._fabrica.criar(subtotal).calcular(subtotal)
```
```bash
python3 yagni.py
uv run radon raw frete_simples.py frete_enterprise.py; uv run radon mi frete_simples.py frete_enterprise.py -s
```
```text
mesmas respostas nas duas versões? True
exemplos: {'0': '19.90', '50.00': '19.90', '199.99': '19.90', '200.00': '0', '999.99': '0'}
== frete_simples
 LOC: 9  LLOC: 6  SLOC: 5  Comments: 0 
Average complexity: A (2.0)
../m8/frete_simples.py - A (78.02)
== frete_enterprise
 LOC: 47  LLOC: 34  SLOC: 32  Comments: 0 
Average complexity: A (1.7142857142857142)
../m8/frete_enterprise.py - A (54.96)
```
As duas dão **respostas idênticas**. A “empresarial” tem **32 linhas de código contra 5** (≈ 6×), cinco classes, uma fábrica e uma configuração para uma regra de **uma linha**, e o **índice de manutenibilidade** do `radon` cai de **78 para 55**. Se amanhã surgirem **de fato** três tarifas de frete diferentes, aí sim a **estratégia** (aula 04) se paga; até lá, a função é melhor: tem **menos para ler, testar e errar**. E note que a versão simples **não impede** a evolução: refatorar a função para estratégias, quando precisar, é um passo pequeno e **protegido por testes**.

**6. Um limite automático de complexidade na CI** (`ruff`, regra `C901`)
```bash
uv run ruff check apps legado config --select C901 --config 'lint.mccabe.max-complexity=7'
```
```text
apps/catalog/management/commands/seed.py:15:9: C901 `handle` is too complex (8 > 7)
apps/payments/services.py:21:5: C901 `processar_evento` is too complex (10 > 7)
legado/pedidos_legado.py:9:5: C901 `processar_pedido` is too complex (17 > 7)
Found 3 errors.
```
Com limite **7**, o `ruff` aponta três funções: o `processar_pedido` legado (17), o `processar_evento` (10) e o comando de *seed* (8). É a lista de **candidatas** (não de culpadas): você decide **quais** vale dividir **agora**. Na CI (módulo 12) você pode **congelar** o estado atual e só **impedir que piore**.

## 🧠 Pausa para lógica
**Problema (detector de “cheiro” OCP).** Escreva um programa que use o módulo `ast` para achar, num diretório, cadeias `if/elif` que comparam a **mesma expressão** com **3 ou mais constantes** (`==`), imprimindo arquivo, linha, a expressão e os valores.

<details><summary>Dica</summary>
Para cada nó <code>ast.If</code>, siga <code>node.orelse</code> enquanto ele tiver exatamente um <code>If</code> (é o <code>elif</code>). Em cada teste <code>ast.Compare</code> com um único <code>Eq</code> e comparador <code>ast.Constant</code>, guarde <code>(ast.unparse(left), valor)</code>. Reporte se há 3+ itens e uma só expressão distinta. Evite contar o mesmo <code>elif</code> como o início de outra cadeia.
</details>

<details><summary>Solução comentada</summary>

É o `ocp_smell.py` do exemplo 1 (executado: 2 cadeias no legado, nenhuma em `apps/`). Duas observações: (1) é uma **heurística** (não pega cadeias com `in`, `match`/`case` ou dicionários), então é um **alerta**, não um veredito; (2) o `match`/`case` do Python 3.10+ é outra forma de escrever a mesma cadeia e também merece suspeita quando cresce.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Toda nova forma de pagamento “mexe” numa função central | Falta de extensibilidade (OCP) | Registro de estratégias; testes de equivalência antes de migrar |
| Subclasse levanta `NotImplementedError` | Herança onde não há “é-um” (LSP) | Composição, ou uma interface menor |
| *Fake* passa e o real falha | Semânticas diferentes (LSP) | Teste de **contrato** contra os dois |
| `error: Argument 1 to "x" has incompatible type ...; expected "Protocol"` (mypy) | O objeto não tem a forma exigida (ISP/DIP funcionando) | Implementar o método ou ajustar a interface |
| Interface com métodos que ninguém usa em cada cliente | Interface gorda (ISP) | Vários `Protocol` pequenos, por consumidor |
| Mesmo literal/regra em vários arquivos | Duplicação de **conhecimento** (DRY) | Constante/serviço único e importar |
| Função `processa(modo, a, b, c, flag1, flag2)` “genérica” | Abstração errada (DRY mal aplicado) | Voltar a duas funções simples; abstrair só o que é **realmente** igual |
| Classe `*Factory`, `*Manager`, `*Helper` com um método | Super-engenharia (KISS/YAGNI) | Uma função |
| “Vai que precisamos” justificando camadas | YAGNI violado | Construa quando a necessidade existir e houver testes para proteger a mudança |
| Aplicar todos os princípios em um *script* de 30 linhas | Cerimônia | Simplicidade: princípios são para **sistemas que crescem** |
| Refatoração “de OCP” que muda o comportamento | Sem teste de equivalência | Primeiro testes (caracterização), depois refatorar (aula 07) |

- **Princípios são heurísticas**, não leis: servem para **conversar sobre trade-offs** (“isto viola SRP porque tem duas razões de mudança; vale dividir?”).
- **A regra dos três** evita abstrair cedo; **o teste de contrato** evita abstrair errado.
- **Meça** (`radon`, `ruff C901`, `mypy`, duplicados) e **decida** com dados; opinião sem número vira discussão infinita.
- **Prefira composição a herança** (herança só quando há um “é-um” real e LSP respeitado).
- **Nomes**: o melhor “princípio” de legibilidade. Se você não consegue nomear a classe sem “e”, ela provavelmente faz coisa demais.

## 🧩 Exercícios
**1. Fixação**
(a) Associe cada violação ao princípio: subclasse que lança `NotImplementedError`; `if/elif` que cresce a cada novo cupom; serviço que importa `httpx` e `channels`; interface com 7 métodos para um consumidor que usa 1; classe que valida, grava e envia e-mail. (b) O que distingue duplicação “real” de “acidental”? (c) Qual a vantagem do `Protocol` sobre uma classe-base abstrata? (d) Quando **não** aplicar um padrão?

<details><summary>Solução</summary>

(a) LSP; OCP; DIP; ISP; SRP. (b) Real: a **mesma decisão/conhecimento** escrita duas vezes (muda junto); acidental: trechos parecidos que mudam por **razões diferentes**. (c) O `Protocol` é **estrutural**: qualquer objeto com os métodos serve, sem herdar de nada (bom para *fakes* e para código de terceiros); a classe abstrata exige herança. (d) Quando o problema é simples e não há dor (YAGNI/KISS): o custo da abstração supera o benefício.
</details>

**2. Aplicação no projeto MiniShop**
Aplique os princípios com **evidência**.

Critérios de pronto:
- [ ] As **formas de pagamento** do seu pedido (ou regras de desconto/cupom) como **estratégias registradas**, com um teste de equivalência (antes × depois) e um teste que **acrescenta** uma regra nova sem editar as existentes
- [ ] Um **teste de contrato** parametrizado que roda contra os **dois** repositórios de **carrinho** (memória e banco) e três substitutos defeituosos que **devem falhar**
- [ ] Uma interface mínima (`Protocol`) para o **relatório de estoque** e um *fake* de ≤ 5 linhas, verificado com `mypy`
- [ ] Uma duplicação **real** encontrada com o `duplicados.py` (ou à mão) e eliminada, com o *commit* mostrando **só** a eliminação
- [ ] `ruff` com `C901` (limite 10) e `mypy` nos módulos novos, sem erros novos
- [ ] Um parágrafo em `docs/adr/0003-principios.md` registrando **uma** abstração que você **decidiu não criar** (YAGNI) e por quê
- [ ] Commit `refactor: strategies, contract tests and a single source of truth`

<details><summary>Solução de referência (ADR curto)</summary>

```markdown
# ADR 0003: Não abstrair o cálculo de frete (por enquanto)
Status: aceito · Data: 2026-11-08
Contexto: só há UMA regra de frete (grátis ≥ R$ 200, senão R$ 19,90).
Decisão: manter `calcular_frete(subtotal)` como função simples, com constantes nomeadas. Sem estratégia/fábrica.
Consequências: 5 linhas de código e 3 testes; se surgir uma 2ª tarifa (por região, por peso), refatoramos para estratégias registradas (aula 8.04), com testes de equivalência.
Gatilho de revisão: o 2º pedido de uma regra de frete nova.
```
</details>

**3. Desafio (opcional)**
Escreva um **teste de propriedade** (com `hypothesis`) para o contrato do repositório: gere sequências aleatórias de `baixar_estoque` e confira que, nos **dois** adaptadores, o estoque **nunca fica negativo** e a soma das baixas aceitas nunca passa do estoque inicial.

## 🎤 Na entrevista
- **Explique o SOLID com um exemplo seu.** SRP: dividi um caso de uso em domínio, serviço e repositório; OCP: formas de pagamento como estratégias registradas, sem editar o `if/elif`; LSP: um teste de contrato garante que o repositório em memória e o do banco cumprem as mesmas promessas; ISP: um `Protocol` mínimo para o relatório; DIP: o serviço recebe o repositório por parâmetro e depende da porta, não do ORM.
- **O que é o princípio de Liskov, na prática?** Um subtipo deve poder ocupar o lugar do tipo base sem quebrar as promessas (pré-condições, pós-condições, invariantes); testa-se com testes de contrato rodando contra todas as implementações.
- **DRY significa nunca repetir código?** Não: significa não repetir **conhecimento** (a mesma regra em dois lugares). Trechos parecidos que mudam por razões diferentes não devem ser unificados à força, para não criar a abstração errada.
- **O que é YAGNI e como conciliar com “design para extensão”?** Não construir hoje o que ninguém pediu; conciliar mantendo o código **simples e bem testado**, para que a extensão futura seja um refactor pequeno e seguro quando a necessidade aparecer.
- **O que é `typing.Protocol`?** Uma interface estrutural: qualquer classe com os métodos exigidos satisfaz o tipo, sem herança; os verificadores (mypy) conferem em tempo de análise.

## 📚 Para ir além
- 📑 Verbete: [SOLID (Wikipédia)](https://en.wikipedia.org/wiki/SOLID). Resumo dos cinco princípios (em inglês).
- 📑 Verbete: [Princípio da substituição de Liskov](https://en.wikipedia.org/wiki/Liskov_substitution_principle). Contratos e variância (em inglês).
- 📄 Artigo: [Sandi Metz — The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction). “Duplicação é muito mais barata que a abstração errada” (em inglês).
- 📄 Artigo: [Martin Fowler — Yagni](https://martinfowler.com/bliki/Yagni.html). O que é e o que não é (em inglês).
- 📄 Especificação: [PEP 544 — Protocols](https://peps.python.org/pep-0544/). Subtipagem estrutural.
- 📄 Documentação: [mypy — Protocols](https://mypy.readthedocs.io/en/stable/protocols.html). Como o verificador usa `Protocol`.
- 📄 Documentação oficial: [`abc` (Python)](https://docs.python.org/3/library/abc.html). Classes abstratas, quando você realmente precisa de herança.
- 📄 Documentação: [Ruff — C901 `complex-structure`](https://docs.astral.sh/ruff/rules/complex-structure/). Limite de complexidade na CI.
- 📄 Documentação: [radon — linha de comando](https://radon.readthedocs.io/en/latest/commandline.html). `cc`, `raw` e `mi`.
- 📄 Especificação: [PEP 20 — O Zen do Python](https://peps.python.org/pep-0020/). “Simples é melhor que complexo.”
- 🏋️ Prática extra: rode `python -c "import this"` e escolha três linhas do Zen que justifiquem uma decisão de design do seu projeto.

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Sei exemplificar S, O, L, I e D com código meu
- [ ] Troquei um `if/elif` por estratégias registradas, com teste de equivalência
- [ ] Escrevi um teste de contrato que roda contra todas as implementações
- [ ] Usei `Protocol` + `mypy` e eliminei uma duplicação **de conhecimento**
- [ ] Medi a complexidade e registrei uma abstração que **decidi não criar**
