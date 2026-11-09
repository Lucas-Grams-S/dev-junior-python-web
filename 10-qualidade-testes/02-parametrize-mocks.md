# 2. `parametrize` e mocks

> ⏱️ ~1h30 · Módulo 10 · Pré-requisitos: [10.01](01-piramide-fixtures.md), [8.02 (services e repositories)](../08-arquitetura/02-services-repositories.md), [8.04 (adapters)](../08-arquitetura/04-padroes-de-projeto.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19, pytest 9). **As saídas são reais.** Os "mutantes" da seção 5 são alterações **temporárias e deliberadas** no `create_order` do laboratório, revertidas depois de cada rodada. A suíte do laboratório chegou a **251 passed, 1 skipped, 1 xfailed**.

## 🎯 Objetivos
- Escrever **uma regra, muitos casos** com `@pytest.mark.parametrize`, com `ids` legíveis e `pytest.param`
- Usar `monkeypatch`, `unittest.mock` e `create_autospec` para **dublar as bordas** (relógio, fila, gateway)
- Distinguir **stub, mock, spy e fake** e escolher o certo
- Saber **onde fazer o patch** (onde é *usado*, não onde é *definido*)
- Evitar mocks que **mentem**: mock sem `spec`, mock demais e testes acoplados à implementação

## 🤔 Por que isso importa
Dois erros opostos estragam suítes. O primeiro é **repetir o mesmo teste dez vezes** com valores diferentes (difícil de ler, fácil de esquecer um caso). O segundo é **mockar tudo**: o teste passa, o código está errado, e ninguém percebe. Dominar `parametrize` e saber *o que* e *onde* dublar é o que separa uma suíte que dá confiança de uma que só dá cobertura. E "mock × fake" é uma pergunta frequente de entrevista.

## 💡 Intuição (explicação simples)
- **`parametrize`** é a **planilha de casos**: a fórmula (o teste) escrita uma vez e uma linha por caso de entrada e saída esperada.
- **Dublê de cinema:** para a cena do carro explodindo você não usa o ator principal, usa um **dublê**. Em testes, dublamos o que é **perigoso, lento ou fora do seu controle**: o provedor de pagamento, o relógio, a fila. Um dublê ruim, porém, **aceita qualquer fala**: se o roteiro pede "salte do prédio" e o dublê responde "ok" a qualquer frase, mesmo errada, a cena sai gravada com erro. É o mock sem `spec`.
- **Fake × mock:** um *fake* é um **simulador de verdade** (um repositório em memória que realmente guarda e devolve dados); um *mock* é um **gravador de chamadas** ("alguém me chamou com estes argumentos?").

## 🔬 Como funciona por dentro
- **`parametrize`:** o pytest gera **um teste por linha**. Cada um passa ou falha independente, com id próprio (`teste[caso]`). Dá para dar nomes (`ids=`/`pytest.param(..., id=...)`), marcar um caso como `xfail`, e combinar parâmetros (produto cartesiano ao empilhar decoradores).
- **Vocabulário (Fowler):**
  | Dublê | Faz | Verifica |
  |---|---|---|
  | **Stub** | devolve respostas prontas | nada (só alimenta o teste) |
  | **Mock** | grava as chamadas | que a interação aconteceu (`assert_called_once_with`) |
  | **Spy** | executa o real e grava | idem, sem substituir o comportamento |
  | **Fake** | implementação simplificada, mas funcional (em memória) | o **estado** resultante |
  | **Dummy** | só preenche um parâmetro | nada |
- **Teste de estado × teste de interação.** Estado: "depois de agir, o mundo ficou assim" (estoque 3, carrinho vazio). Interação: "o código chamou X com Y". Estado sobrevive a refatorações; interação **acopla o teste à implementação**.
- **O que dublar:** as **bordas** do sistema: rede, relógio, fila, e-mail, provedor externo, aleatoriedade. **O que não dublar:** o seu próprio domínio e a sua própria lógica. Se você precisou mockar três coisas internas para testar uma função, o design está pedindo ajuda (aula 8.02: injetar um repositório que pode ser um *fake*).
- **`Mock` solto aceita qualquer atributo e chamada.** **`create_autospec(Classe)`** (ou `Mock(spec=...)`) copia a **forma** do objeto real: método inexistente → `AttributeError`; argumentos errados → `TypeError`.
- **Onde fazer o patch:** `from x import f` cria um **nome novo** no módulo que importou. Para trocar `f` no código sob teste, troque o nome **onde ele é usado** (`modulo_que_usa.f`), não onde foi definido. `monkeypatch.setattr` desfaz sozinho no fim do teste.
- **Relógio:** não use `sleep` nem mexa nos dados para "envelhecer"; troque a função que lê a hora (`timezone.now`) por uma que devolve o instante desejado (ou use `freezegun`/`time-machine`). Melhor ainda: **receber a hora como parâmetro** (aula 7.04).
- **Cuidado com o escopo do patch:** `monkeypatch.setattr(timezone, "now", ...)` troca o atributo do **módulo** para todo o processo durante o teste; é restaurado no fim, mas qualquer outra coisa que chame `timezone.now()` no meio também vê o relógio falso.

## 🛠️ Exemplo prático
**1. `parametrize` com nomes que contam a história** (`tests/test_parametrize_mocks.py`). A função `notificar_pedido_criado` faz coisas diferentes conforme `ORDER_EMAIL_MODE`; em vez de três testes quase iguais, uma tabela:
```python
class EspiaDaTarefa:
    """Substituto simples da tarefa de e-mail: registra o que foi pedido."""
    def __init__(self):
        self.chamadas, self.enfileiradas = [], []

    def __call__(self, order_id):
        self.chamadas.append(order_id)

    def delay(self, order_id):
        self.enfileiradas.append(order_id)


@pytest.mark.parametrize("modo,executa_agora,enfileira_no_commit", [
    pytest.param("sync", True, False, id="sync-executa-na-hora"),
    pytest.param("async", False, True, id="async-enfileira-so-no-commit"),
    pytest.param("off", False, False, id="off-nao-faz-nada"),
])
def test_notificacao_conforme_o_modo(db, modo, executa_agora, enfileira_no_commit, settings, monkeypatch, django_capture_on_commit_callbacks):
    settings.ORDER_EMAIL_MODE = modo
    espia = EspiaDaTarefa()
    monkeypatch.setattr(notifications, "send_order_confirmation_email", espia)      # onde é USADA (não onde é definida)
    pedido = type("Pedido", (), {"pk": 42})()
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        notifications.notificar_pedido_criado(pedido)
    assert (espia.chamadas == [42]) is executa_agora
    assert espia.enfileiradas == []                                                   # nada sai antes do commit
    for cb in callbacks:
        cb()
    assert (espia.enfileiradas == [42]) is enfileira_no_commit
```
O `EspiaDaTarefa` é um **spy** feito à mão (três linhas); o patch vai em `notifications.send_order_confirmation_email`, **onde o nome é usado**. A saída lista um teste por linha, com os ids que escrevi:
```text
test_notificacao_conforme_o_modo[sync-executa-na-hora] PASSED
test_notificacao_conforme_o_modo[async-enfileira-so-no-commit] PASSED
test_notificacao_conforme_o_modo[off-nao-faz-nada] PASSED
test_cancela_pendentes_antigos_avancando_o_relogio PASSED
test_pagar_com_gateway_dublado[gateway-ok] PASSED
test_pagar_com_gateway_dublado[gateway-fora-do-ar] PASSED
```
Quando um caso falha, o relatório diz **qual** (`[async-enfileira-so-no-commit]`), e dá para rodar só ele: `pytest "tests/...::test_notificacao_conforme_o_modo[off-nao-faz-nada]"`. *(Um detalhe: o caso `async` precisou da fixture `db`, porque `transaction.on_commit` consulta a conexão; a minha primeira versão falhou com "Database access not allowed" e a mensagem já dizia o remédio.)*

**2. Relógio controlado em vez de `sleep`.** O cancelamento de pedidos pendentes antigos (aula 7.08) tinha um teste que **alterava `created_at`** no banco para "envelhecer" o pedido. O novo adianta o **relógio**:
```python
def test_cancela_pendentes_antigos_avancando_o_relogio(cliente, criar_produto, monkeypatch):
    from apps.cart import services as carrinho
    from apps.orders import services
    p = criar_produto(estoque=10)
    carrinho.add_item(cliente, p.pk, 2)
    pedido = services.create_order(cliente)
    cancelar_pedidos_pendentes_antigos(horas=24)
    pedido.refresh_from_db()
    assert pedido.status == Order.Status.PENDING                                      # agora mesmo: ainda vale

    futuro = timezone.now() + timedelta(hours=25)
    monkeypatch.setattr(timezone, "now", lambda: futuro)                              # o "amanhã" chegou, sem dormir
    cancelar_pedidos_pendentes_antigos(horas=24)
    pedido.refresh_from_db()
    assert pedido.status == Order.Status.CANCELLED
    p.refresh_from_db()
    assert p.stock == 10                                                              # e o estoque voltou
```
O mesmo pedido, "agora": continua pendente; "daqui a 25 horas": cancelado, e o estoque voltou. Nenhum `sleep`, nenhum dado adulterado.

**3. Dublando o gateway de pagamento com `autospec`.** A mesma tabela cobre o caminho feliz e a falha do provedor:
```python
@pytest.mark.parametrize("resultado,status_http,corpo", [
    pytest.param(Cobranca(ref="mock-123"), 201, {"payment_ref": "mock-123"}, id="gateway-ok"),
    pytest.param(GatewayIndisponivel("fora do ar"), 422, {"code": "gateway_unavailable"}, id="gateway-fora-do-ar"),
])
def test_pagar_com_gateway_dublado(api_as, pedido_pendente, monkeypatch, resultado, status_http, corpo):
    gateway = create_autospec(PaymentGateway, instance=True)                          # só aceita o que a PORTA real tem
    if isinstance(resultado, Exception):
        gateway.criar_cobranca.side_effect = resultado
    else:
        gateway.criar_cobranca.return_value = resultado
    monkeypatch.setattr("apps.payments.api.obter_gateway", lambda: gateway)           # onde é USADO
    r = api_as("cliente").post(f"/api/v1/orders/{pedido_pendente.pk}/pay/")
    assert r.status_code == status_http and all(r.json()[k] == v for k, v in corpo.items())
    gateway.criar_cobranca.assert_called_once_with(pedido_pendente.pk, Decimal("100.00"))
```
`create_autospec(PaymentGateway, instance=True)` copia a **porta** da aula 8.04. A chamada é verificada com os argumentos exatos (`pedido_pendente.pk` e `Decimal("100.00")`), e o patch está em `apps.payments.api.obter_gateway`, **onde a view usa o nome**.

**4. As armadilhas, em testes** (`tests/test_armadilhas_de_mock.py`):
```text
test_patch_no_alvo_errado_nao_tem_efeito FAILED
test_mock_sem_spec_aceita_metodo_inexistente PASSED
test_autospec_recusa_metodo_inexistente PASSED
test_autospec_recusa_argumentos_errados PASSED
[XPASS(strict)] armadilha didática: patch em apps.payments.gateway não afeta apps.payments.api
FAILED test_patch_no_alvo_errado_nao_tem_efeito
========================= 1 failed, 3 passed in 0.50s ==========================
```
- **Mock sem `spec`:** `Mock()` aceitou `criar_cobranca_com_erro_de_digitacao(10, 99)` e o teste ficou **verde** com um método que não existe. Com `create_autospec`, o mesmo erro vira `AttributeError`, e argumentos a mais viram `TypeError`.
- **Patch no alvo errado:** troquei `apps.payments.gateway.obter_gateway` (onde é *definido*), mas a view usa o nome que já importou em `apps.payments.api`; quem respondeu foi o `GatewayFake` real e a asserção `assert_called_once()` falhou. O teste está marcado `xfail(strict=True)`: **documenta o erro** e, se alguém o "consertar" sem querer, a suíte avisa (`XPASS(strict)` vira falha).
> 🔎 **O mesmo patch errado, resultado diferente conforme a ordem.** Na primeira versão desse teste, **rodando o arquivo sozinho**, o patch no alvo errado *funcionou* (`XPASS`), mas na suíte completa não. Motivo: o módulo `apps.payments.api` só é importado quando a primeira URL é resolvida; se o `setattr` acontece **antes** desse import, a view já nasce usando a função trocada. É um teste **dependente de ordem**, a fonte clássica de falhas intermitentes. Corrigi forçando o `import apps.payments.api` no início do teste. Lição: prefira `monkeypatch.setattr(objeto_que_usa, "nome", ...)` ao patch por *string* quando puder, e rode em ordem aleatória (aula 01).

**5. Mock × fake: o que acontece quando o código muda?** Três testes para o **mesmo** caso de uso `create_order` (`tests/test_mocks_vs_fakes.py`), aplicados a quatro versões do código (a original e três alterações temporárias):
```python
"""Três jeitos de testar o MESMO caso de uso (create_order): com um FAKE (estado) e com MOCKS (interações)."""
from decimal import Decimal
from unittest.mock import create_autospec

from apps.orders import services
from apps.orders.domain import ItemCarrinho, ProdutoInfo
from apps.orders.repositories import MemoriaPedidoRepository, PedidoRepository


def repo_com_fake():
    p = ProdutoInfo(1, "Caneta", Decimal("10.00"), 5, True)
    return MemoriaPedidoRepository(carrinhos={"ana": [ItemCarrinho(1, 2)]}, produtos={1: p})


def test_estado_com_fake_o_resultado_importa():
    repo = repo_com_fake()
    pedido = services.create_order("ana", repo=repo)
    assert pedido.total == 20 and repo.produtos[1].estoque == 3 and repo.carrinhos["ana"] == []


def mock_do_repo():
    repo = create_autospec(PedidoRepository, instance=True)
    repo.itens_do_carrinho.return_value = [ItemCarrinho(1, 2)]
    repo.travar_produtos.return_value = {1: ProdutoInfo(1, "Caneta", Decimal("10.00"), 5, True)}
    repo.baixar_estoque.return_value = True
    return repo


def test_mock_sequencia_exata_de_chamadas():
    repo = mock_do_repo()
    services.create_order("ana", repo=repo)
    nomes = [c[0] for c in repo.mock_calls if not c[0].startswith("transacao")]
    assert nomes == ["travar_carrinho", "itens_do_carrinho", "travar_produtos", "criar_pedido", "baixar_estoque", "esvaziar_carrinho"]


def test_mock_so_o_essencial():
    repo = mock_do_repo()
    services.create_order("ana", repo=repo)
    repo.criar_pedido.assert_called_once()
    repo.esvaziar_carrinho.assert_called_once()
```
| Versão do código | Teste de **estado** (fake) | Mock: **sequência exata** | Mock: **só o essencial** |
|---|---|---|---|
| 0) original | ✅ passa | ✅ passa | ✅ passa |
| 1) **refatoração inofensiva** (esvaziar o carrinho antes de baixar o estoque; dentro da transação o resultado é o mesmo) | ✅ passa | ❌ **falha** (falso alarme) | ✅ passa |
| 2) **bug real**: não baixa o estoque | ❌ falha (correto) | ❌ falha (correto, por acaso) | ✅ **passa (o bug escapou!)** |
| 3) **bug real**: não esvazia o carrinho | ❌ falha (correto) | ❌ falha (correto) | ❌ falha (correto) |
Conclusões medidas, não opinadas:
1. O mock de **sequência exata** quebra numa refatoração que não muda nada (**falso alarme**): ele testa *como*, não *o quê*.
2. O mock **superficial** deixou passar um **bug real** (estoque não baixado), porque só conferia o que o autor lembrou de conferir.
3. O teste de **estado com um fake** pegou os dois bugs e **ignorou** a refatoração: é o que dá liberdade para melhorar o código.
Por isso a regra de bolso: **fakes para o que é seu** (repositórios, relógio injetado), **mocks para a borda externa** (provedor de pagamento, e-mail, fila), e interação só quando a chamada **é** o resultado (por exemplo, "o e-mail foi pedido uma vez").

**6. Estado final do laboratório**
```text
251 passed, 1 skipped, 1 xfailed       (pytest-randomly, sementes 5, 6 e 7: o mesmo resultado)
```

## 🧠 Pausa para lógica
**Problema.** Você precisa testar `calcular_frete(subtotal, regiao)`, que tem 3 regiões × 4 faixas de subtotal (12 combinações) e uma regra "frete grátis a partir de R$ 200 em qualquer região". (a) Como organizar com `parametrize` sem escrever 12 testes à mão? (b) Que casos de **fronteira** você incluiria? (c) A função chama a API dos Correios; o que dublar e como?

<details><summary>Dica</summary>Pense em empilhar dois decoradores <code>parametrize</code>, nos valores exatamente na borda (199,99 / 200,00 / 200,01) e em separar o cálculo da chamada de rede.</details>

<details><summary>Solução comentada</summary>

(a) Dois `@pytest.mark.parametrize` empilhados geram o produto cartesiano (`regiao` × `subtotal`); a **tabela de preços esperados** vai num dicionário ou numa lista de `pytest.param(..., id="sul-ate-100")` para os casos que não seguem a fórmula. (b) `199.99`, `200.00`, `200.01` (a fronteira do frete grátis), `0`, o menor valor aceito, um valor enorme, e uma região desconhecida (erro esperado). (c) Dubla-se **a chamada de rede**, não a função: injete um cliente (ou uma função `consultar_correios`) e passe um **stub** com a resposta pronta; cubra também a falha (`TimeoutError`) com outro caso. Melhor ainda: separe o **cálculo puro** (testado em unidade, sem dublê) da **consulta externa** (testada em integração com o provedor falso), como no gateway da aula 8.04.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Teste passa com método que não existe | `Mock()` sem `spec` | `create_autospec(Classe, instance=True)` |
| `patch` não tem efeito | Alvo errado (onde é definido) | Patch **onde é usado**; ou `monkeypatch.setattr(objeto, "nome", ...)` |
| Resultado do patch muda com a ordem | Import tardio do módulo | Importar antes; rodar em ordem aleatória |
| Refatoração quebra vários testes sem mudar comportamento | Testes de interação demais | Testar estado; usar *fakes* para o que é seu |
| Bug passa porque "o mock nunca falha" | Asserções superficiais | Verificar o **resultado**; validar por mutação (aula 9.05) |
| Mockar três coisas internas para testar uma função | Design acoplado | Injetar dependências; separar lógica pura de I/O |
| `parametrize` com 40 linhas ilegíveis (`teste[3-7-True]`) | Sem ids | `ids=` / `pytest.param(..., id="...")` |
| Muitos parâmetros que não variam | Tabela inchada | Parametrize só o que muda; o resto vira constante |
| `sleep` nos testes para testar tempo | Não controlar o relógio | Trocar o relógio (`monkeypatch`, `time-machine`) ou injetá-lo |
| Mock de `datetime.datetime.now` direto | `datetime` é tipo embutido em C | Mockar `timezone.now` do Django, ou a função da sua base |
| Esquecer de desfazer o patch | `setattr` manual | `monkeypatch` desfaz sozinho |

- **Um caso por linha**, nomeado pelo **comportamento**, não pelo número.
- **Mocks na borda; fakes no meio; funções puras no centro.**
- **Teste de estado primeiro;** interação só quando a chamada é o objetivo.
- **Valide seus testes por mutação**, como fizemos acima.

## 🧩 Exercícios
**1. Fixação.** (a) Qual a diferença entre stub, mock e fake? (b) Por que `create_autospec` é mais seguro que `Mock()`? (c) Onde fazer o patch de uma função importada com `from x import f`? (d) Por que um teste de sequência exata de chamadas é frágil?

<details><summary>Solução</summary>

(a) Stub devolve respostas prontas; mock grava e verifica chamadas; fake é uma implementação simplificada e funcional (em memória). (b) Copia a assinatura do objeto real: atributo inexistente ou argumentos errados viram erro. (c) No módulo que **usa** o nome (`modulo_que_importou.f`). (d) Ele fixa a ordem interna da implementação; qualquer refatoração inofensiva o quebra (falso alarme), como mostrou a versão 1 da tabela.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] Converter **três** grupos de testes repetitivos em `parametrize`, com `ids` legíveis
- [ ] Um teste com **relógio controlado** (sem `sleep`, sem alterar datas no banco)
- [ ] O gateway de pagamento dublado com `create_autospec`, cobrindo sucesso **e** falha
- [ ] Os três estilos de teste do `create_order` (fake, mock exato, mock superficial) e a **tabela de mutantes** no README, com a sua análise
- [ ] Um teste de armadilha com `xfail(strict=True)` (patch no alvo errado)
- [ ] Revisar a suíte: nenhum `Mock()` sem `spec` para objetos que existem no código
- [ ] Commit `test: parametrized cases, controlled clock and autospec gateway`

**3. Desafio (opcional).** Escreva um teste de **propriedade** com `hypothesis` para `domain.total(linhas)`: para qualquer lista de linhas, o total é a soma de `quantidade × preço`, nunca negativo e independente da ordem. Veja o que a biblioteca descobre (valores extremos, decimais).

## 🎤 Na entrevista
- **Para que serve `parametrize`?** Executar a mesma lógica de teste com vários conjuntos de entrada e saída, gerando um teste independente por caso, com ids legíveis.
- **Mock, stub e fake: qual a diferença?** Stub devolve respostas prontas; mock registra e verifica interações; fake é uma implementação funcional simplificada (como um repositório em memória). Prefiro fakes e testes de estado para o que é meu, e mocks para bordas externas.
- **Por que `autospec`?** Porque um `Mock` solto aceita qualquer coisa e esconde erros de digitação e de assinatura; `autospec` exige que o uso bata com o objeto real.
- **Onde se faz o `patch`?** Onde o nome é **usado**, não onde é definido.
- **Como testar código que depende do horário?** Controlando o relógio (trocando `timezone.now` ou usando `freezegun`/`time-machine`), idealmente injetando o relógio; nunca com `sleep`.
- **O que é um teste frágil?** Um que quebra quando a implementação muda sem que o comportamento mude; costuma vir de mocks que verificam a sequência interna de chamadas.

## 📚 Para ir além
- 📄 Documentação oficial: [pytest — `parametrize`](https://docs.pytest.org/en/stable/how-to/parametrize.html). `ids`, `pytest.param` e combinações.
- 📄 Documentação oficial: [pytest — `monkeypatch`](https://docs.pytest.org/en/stable/how-to/monkeypatch.html). `setattr`, `setenv`, `chdir` e desfazimento automático.
- 📄 Documentação oficial: [`unittest.mock`](https://docs.python.org/3/library/unittest.mock.html) e a seção [onde fazer o patch](https://docs.python.org/3/library/unittest.mock.html#where-to-patch).
- 📄 Documentação: [pytest-django — Helpers](https://pytest-django.readthedocs.io/en/latest/helpers.html). `django_capture_on_commit_callbacks` e outras.
- 📄 Artigo: [Martin Fowler — Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html). Estado × interação e o vocabulário dos dublês (em inglês).
- 📄 Documentação oficial: [pytest — `xfail`](https://docs.pytest.org/en/stable/reference/reference.html#pytest-mark-xfail-ref). `strict=True`.
- 🧰 Bibliotecas: [time-machine](https://pypi.org/project/time-machine/) e [freezegun](https://pypi.org/project/freezegun/). Controlar o relógio (em inglês).

## ✅ Checklist da aula
- [ ] Converti testes repetitivos em `parametrize` com ids legíveis
- [ ] Controlei o relógio sem `sleep`
- [ ] Dublei o gateway com `create_autospec` e sei onde fazer o patch
- [ ] Diferencio stub, mock, spy e fake, e sei quando usar cada um
- [ ] Validei meus testes por mutação e entendi o custo dos mocks de interação
