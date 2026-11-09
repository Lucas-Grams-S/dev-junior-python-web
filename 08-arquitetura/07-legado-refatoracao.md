# 7. Lidando com código legado: testes de caracterização e refatoração segura

> ⏱️ ~1h30 · Módulo 8 · Pré-requisitos: [8.02](02-services-repositories.md), [8.03](03-solid-dry-kiss-yagni.md), [5.17 (transações)](../05-django/17-pedidos-estoque-transacao.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19, SQLite; `radon` 6.0.1, `ruff` 0.17.4, `coverage` 7.17.2). **As saídas são reais.** O “código herdado” (`legado/pedidos_legado.py`) foi escrito por mim, de propósito, com os vícios típicos de código antigo; não é código de ninguém. A suíte completa ficou em **146 passed, 1 skipped** (o teste de concorrência só roda em PostgreSQL).

## 🎯 Objetivos
- Escrever um **teste de caracterização** (*golden master*): fixar o que o código **faz hoje**, certo ou errado
- Medir a **rede de segurança** (cobertura de ramos e testes de **mutação** manual)
- Refatorar em **passos pequenos**, rodando a rede a cada passo, separando **refatoração** (não muda comportamento) de **correção** (muda)
- Medir o resultado com `radon` e `ruff` (complexidade, linhas, índice de manutenibilidade)
- Descobrir e corrigir uma **injeção de SQL** sem quebrar o resto

## 🤔 Por que isso importa
Quase todo emprego começa com código que **já existe**, sem testes e com regras que ninguém lembra por quê. A habilidade que separa o júnior que “tem medo de mexer” do que **melhora o sistema com segurança** é esta: criar uma rede de testes *antes* e refatorar em passos pequenos. Aparece em entrevista como “como você mexeria num código sem testes?”.

## 💡 Intuição (explicação simples)
Antes de reformar uma casa **habitada**, você **fotografa cada cômodo**. Durante a obra, de tempos em tempos compara com as fotos para ver se nada mudou sem querer. O teste de caracterização é essa **foto**: ele não diz que o cômodo está bonito, só que está **igual**. E reforma é feita um cômodo por vez, não derrubando a casa.

## 🔬 Como funciona por dentro
- **Refatorar** = mudar a **estrutura** sem mudar o **comportamento observável**. Se o comportamento muda, é **correção ou funcionalidade**, e deve ser um passo **separado** (e commit separado).
- **Teste de caracterização / golden master (Michael Feathers):** execute o código atual com muitas entradas, **grave** as saídas e efeitos colaterais e, depois, compare. É a ferramenta para código **sem testes e sem especificação**.
- **Quão boa é a rede?** Duas medidas: **cobertura de ramos** (todos os caminhos foram exercitados?) e **mutação manual** (se eu estragar uma regra de propósito, o teste quebra?). Cobertura sem mutação pode dar falsa confiança.
- **Passos pequenos, rede verde a cada passo:** extrair função → mover → substituir condicional por tabela. Qualquer passo que quebre a rede é revertido (`git revert`/desfazer), não “consertado em cima”.
- **Congelar não é aprovar.** O golden master também grava os **bugs**. Por isso há um passo explícito para decidir, caso a caso, o que é **bug** (corrige-se com teste novo) e o que é **regra de negócio** (mantém-se).
- **Estratégia para sistemas grandes:** *Strangler Fig* — o código novo cresce ao redor do antigo, assumindo rotas aos poucos, até o legado poder ser removido.

## 🛠️ Exemplo prático
**1. O legado** (`legado/pedidos_legado.py`, uma função de 63 linhas)
```python
# -*- coding: utf-8 -*-
# "Código herdado" do MiniShop v0: funciona, ninguém tem coragem de mexer. (Escrito de propósito para a aula 8.07.)
from django.db import connection

TOTAL_PEDIDOS = 0          # contador global "para o relatório"
LOG = []


def processar_pedido(dados):
    global TOTAL_PEDIDOS
    c = connection.cursor()
    itens = dados["itens"]
    if len(itens) == 0:
        return {"ok": False, "erro": "sem itens"}
    total = 0
    linhas = []
    for i in itens:
        c.execute("select id, price, stock, is_active from catalog_product where sku = '" + i["sku"] + "'")
        p = c.fetchone()
        if p is None:
            return {"ok": False, "erro": "produto " + i["sku"] + " nao existe"}
        else:
            if p[3] == 0:
                return {"ok": False, "erro": "produto " + i["sku"] + " inativo"}
            else:
                if p[2] < i["qtd"]:
                    return {"ok": False, "erro": "sem estoque " + i["sku"]}
                else:
                    sub = float(p[1]) * i["qtd"]
                    total = total + sub
                    linhas.append((p[0], i["qtd"], float(p[1])))
    desc = 0
    if dados.get("cupom"):
        if dados["cupom"] == "PROMO10":
            desc = total * 0.10
        elif dados["cupom"] == "PROMO20":
            if total > 500:
                desc = total * 0.20
            else:
                desc = total * 0.10
        elif dados["cupom"] == "FRETEGRATIS":
            desc = 0
        else:
            return {"ok": False, "erro": "cupom invalido"}
    if dados.get("forma_pgto") == "pix":
        desc = desc + total * 0.05
    elif dados.get("forma_pgto") == "cartao":
        desc = desc + 0
    elif dados.get("forma_pgto") == "boleto":
        desc = desc - 2.5
    else:
        return {"ok": False, "erro": "forma de pagamento invalida"}
    frete = 0
    if total - desc < 200:
        frete = 19.9
    if dados.get("cupom") == "FRETEGRATIS":
        frete = 0
    final = total - desc + frete
    final = round(final, 2)
    c.execute("insert into orders_order (user_id, status, total, created_at) values (%s, 'pending', %s, datetime('now'))", [dados["user_id"], str(final)])
    oid = c.lastrowid
    for l in linhas:
        c.execute("insert into orders_orderitem (order_id, product_id, quantity, unit_price) values (%s, %s, %s, %s)", [oid, l[0], l[1], str(l[2])])
        c.execute("update catalog_product set stock = stock - %s where id = %s", [l[1], l[0]])
    TOTAL_PEDIDOS = TOTAL_PEDIDOS + 1
    LOG.append("pedido " + str(oid) + " total " + str(final))
    print("pedido criado", oid)
    return {"ok": True, "pedido_id": oid, "total": final, "frete": frete, "desconto": round(desc, 2)}
```
Cheiros: SQL por **concatenação**, `if` aninhado, dinheiro em `float`, **estado global** (`TOTAL_PEDIDOS`, `LOG`), `print`, regras de preço misturadas com acesso a dados, e SQL específico do SQLite (`datetime('now')`).

**2. A rede de segurança: 270 casos** (`tests/test_legado_caracterizacao.py`). A matriz combina **9 carrinhos × 6 cupons × 5 formas de pagamento** e registra a resposta, o **estoque depois** e o contador global:
```python

CARRINHOS = {
    "vazio": [],
    "barato": [{"sku": "A-100", "qtd": 1}],                          # total 100
    "medio": [{"sku": "A-100", "qtd": 3}],                           # total 300
    "caro": [{"sku": "B-300", "qtd": 2}],                            # total 600 (> 500: PROMO20 vale 20%)
    "misto": [{"sku": "A-100", "qtd": 2}, {"sku": "D-020", "qtd": 1}],
    "limite_frete": [{"sku": "A-100", "qtd": 2}],                    # total 200 EXATO (a fronteira do frete)
    "sku_inexistente": [{"sku": "ZZZ", "qtd": 1}],
    "inativo": [{"sku": "C-OFF", "qtd": 1}],
    "sem_estoque": [{"sku": "D-020", "qtd": 2}],
}
CUPONS = [None, "", "PROMO10", "PROMO20", "FRETEGRATIS", "XPTO"]
FORMAS = ["pix", "cartao", "boleto", "cheque", None]
CASOS = [(c, k, f) for c, k, f in itertools.product(CARRINHOS, CUPONS, FORMAS)]


@pytest.fixture
def mundo(django_user_model):
    cat = Category.objects.create(name="Geral", slug="geral")
    for sku, preco, estoque, ativo in [("A-100", "100.00", 10, True), ("B-300", "300.00", 5, True), ("C-OFF", "50.00", 5, False), ("D-020", "20.00", 1, True)]:
        Product.objects.create(category=cat, sku=sku, name=sku, price=preco, stock=estoque, is_active=ativo)
    return django_user_model.objects.create_user(username="legado", password="x" * 12)
```
Gravação do “retrato” e leitura do que o legado realmente faz:
```bash
GOLDEN=gravar uv run pytest tests/test_legado_caracterizacao.py -rs
```
```text
SKIPPED [1] tests/test_legado_caracterizacao.py:61: golden master gravado: 270 casos
```
Alguns comportamentos descobertos (nenhum estava documentado):
| Caso | Resposta gravada | Observação |
|---|---|---|
| 3 × A (R$ 300), `PROMO20`, `pix` | desconto 45.0, total **255.0** | `PROMO20` só dá 20% acima de R$ 500; abaixo, 10% (+ 5% do pix) |
| `limite_frete` (R$ 200 exato), sem cupom | frete **0** | a fronteira é `< 200`: R$ 200 já ganha frete grátis |
| `boleto` | desconto **−2,5** | “desconto negativo” é na verdade um **acréscimo** |
| cupom `""` (vazio) | tratado como sem cupom | texto vazio é “falso” em Python |
| forma de pagamento `None` | erro “forma de pagamento invalida” | a forma é obrigatória |

**3. Quão forte é a rede?**
```bash
uv run pytest -q tests/test_legado_caracterizacao.py --cov=legado --cov-branch --cov-report=term-missing
```
```text
legado/pedidos_legado.py      56      0     32      0   100%
TOTAL                         56      0     32      0   100%
1 passed in 0.69s
```
**100% dos ramos.** E quatro **mutações manuais** (estragar uma regra de propósito e rodar a rede):
```text
mutação 's/total \* 0.10/total * 0.11/' -> 1 failed in 0.49s
mutação 's/frete = 19.9/frete = 20.9/' -> 1 failed in 0.49s
mutação 's/if total - desc < 200/if total - desc <= 200/' -> 1 failed in 0.50s
mutação 's/desc = desc - 2.5/desc = desc - 2.0/' -> 1 failed in 0.49s
```
> 🔁 **Revalidado no módulo 10.** Como os quatro mutantes têm o mesmo tamanho de arquivo e foram aplicados em sequência, reexecutei a rodada com um diretório de cache de bytecode **novo a cada mutante** (`PYTHONPYCACHEPREFIX`), para excluir a chance de o Python reutilizar um `.pyc` antigo (armadilha explicada na aula 10.04). O resultado foi o mesmo: o original passa e os 4 mutantes falham.

Os quatro mutantes foram **detectados** (a fronteira do frete, o percentual, o valor do frete e o acréscimo do boleto). Só então é seguro mexer.

**4. Passo 1: extrair funções** (comportamento idêntico, SQL ainda concatenado). `processar_pedido` passou de 63 linhas para um orquestrador que chama `_ler_linhas`, `_desconto_cupom`, `_ajuste_pagamento`, `_frete` e `_gravar`; os `return {"ok": False...}` viraram uma exceção `PedidoInvalido`. A rede: `1 passed` (270 casos iguais).

**5. O que o golden master não deve proteger: injeção de SQL.** Ao ler o passo 1, o `where sku = '" + i["sku"] + "'"` chama atenção. Escrevi o teste **antes** de corrigir (`tests/test_legado_seguranca.py`) e rodei contra o código com o defeito:
```text
E       assert (True is False)
E       assert (True is False)
E           sqlite3.OperationalError: near "Brien": syntax error
E           django.db.utils.OperationalError: near "Brien": syntax error
FAILED tests/test_legado_seguranca.py::test_sku_estranho_e_tratado_como_texto[' or '1'='1]
FAILED tests/test_legado_seguranca.py::test_sku_estranho_e_tratado_como_texto[A-100' or '1'='1]
FAILED tests/test_legado_seguranca.py::test_sku_estranho_e_tratado_como_texto[O'Brien]
3 failed in 0.61s
```
Duas falhas reais: o SKU `' or '1'='1` **fez o pedido passar** (a consulta devolveu um produto qualquer) e um SKU legítimo com apóstrofo (`O'Brien`) **derrubou** o processamento com erro de sintaxe SQL. Os dois sintomas têm a mesma causa. **Passo 2:** parametrizar a consulta (`where sku = %s` com `[i["sku"]]`). Resultado, rodando as duas redes:
```text
4 passed
```
O golden master **continuou verde**: nenhum dos 270 casos legítimos mudou. Só a entrada maliciosa mudou de comportamento, que é o que se queria. **Dois commits separados:** `refactor: extract functions from processar_pedido` e `fix(security): parametrize sku lookup`.

**6. Passo 3: regras puras fora do I/O** (`legado/precificacao.py`, sem banco). Os `if/elif` de cupom e forma de pagamento viraram **tabelas** (o padrão *Strategy* da aula 03):
```python
"""Regras de preço do legado, PURAS (sem banco, sem I/O). Extraídas de `processar_pedido`; o comportamento (inclusive em float) é o mesmo."""


class PedidoInvalido(Exception):
    pass


# Cada cupom é uma função (total -> desconto). Cupom novo = uma linha na tabela, sem mexer em nenhum `if`.
CUPONS = {
    "PROMO10": lambda total: total * 0.10,
    "PROMO20": lambda total: total * 0.20 if total > 500 else total * 0.10,
    "FRETEGRATIS": lambda total: 0,
}
# Ajuste por forma de pagamento (positivo = desconto; negativo = acréscimo).
FORMAS_PAGAMENTO = {
    "pix": lambda total: total * 0.05,
    "cartao": lambda total: 0,
    "boleto": lambda total: -2.5,
}
FRETE_PADRAO = 19.9
FRETE_GRATIS_ACIMA_DE = 200


def desconto_cupom(total, cupom):
    if not cupom:
        return 0
    if cupom not in CUPONS:
        raise PedidoInvalido("cupom invalido")
    return CUPONS[cupom](total)


def ajuste_pagamento(total, forma):
    if forma not in FORMAS_PAGAMENTO:
        raise PedidoInvalido("forma de pagamento invalida")
    return FORMAS_PAGAMENTO[forma](total)


def frete(total, desconto, cupom):
    if cupom == "FRETEGRATIS":
        return 0
    return FRETE_PADRAO if total - desconto < FRETE_GRATIS_ACIMA_DE else 0


def precificar(total, cupom, forma):
    """(desconto, frete, valor final arredondado)"""
    desc = desconto_cupom(total, cupom) + ajuste_pagamento(total, forma)
    f = frete(total, desc, cupom)
    return desc, f, round(total - desc + f, 2)
```
E o que sobrou no arquivo do legado:
```python
def _gravar(c, user_id, linhas, final):
    c.execute("insert into orders_order (user_id, status, total, created_at) values (%s, 'pending', %s, datetime('now'))", [user_id, str(final)])
    oid = c.lastrowid
    for produto_id, qtd, preco in linhas:
        c.execute("insert into orders_orderitem (order_id, product_id, quantity, unit_price) values (%s, %s, %s, %s)", [oid, produto_id, qtd, str(preco)])
        c.execute("update catalog_product set stock = stock - %s where id = %s", [qtd, produto_id])
    return oid


def processar_pedido(dados):
    global TOTAL_PEDIDOS
    c = connection.cursor()
    if len(dados["itens"]) == 0:
        return {"ok": False, "erro": "sem itens"}
    try:
        linhas, total = _ler_linhas(c, dados["itens"])
        desc, frete, final = precificar(total, dados.get("cupom"), dados.get("forma_pgto"))
    except PedidoInvalido as e:
        return {"ok": False, "erro": str(e)}
    oid = _gravar(c, dados["user_id"], linhas, final)
    TOTAL_PEDIDOS = TOTAL_PEDIDOS + 1
    LOG.append("pedido " + str(oid) + " total " + str(final))
    print("pedido criado", oid)
    return {"ok": True, "pedido_id": oid, "total": final, "frete": frete, "desconto": round(desc, 2)}
```
Rede após o passo 3: `4 passed`. Os testes unitários das regras puras (`tests/test_precificacao.py`, **sem banco**, 0,02 s) cobrem fronteiras e provam que um **cupom novo é uma linha na tabela**:
```text
9 passed in 0.02s
```

**7. Medindo o resultado**
```bash
uv run radon cc legado -s -a      # complexidade ciclomática
uv run radon raw legado/...       # linhas
uv run radon mi legado/... -s     # índice de manutenibilidade
```
| Métrica | Antes (`processar_pedido`) | Depois |
|---|---|---|
| Complexidade ciclomática | **17 (C)** | **3 (A)** |
| Complexidade média do módulo | 17,0 | 3,3 (`pedidos_legado`) e 2,0 (`precificacao`) |
| Linhas de código (SLOC) | 63 em 1 função | 41 + 32 em funções pequenas |
| Índice de manutenibilidade | 50,56 (A, mas no limite) | 61,88 e 65,66 |

E o `ruff` com regras de complexidade e segurança (limite 10), antes e depois:
```text
== ../m8/leg_v0.py
leg_v0.py:9:5: C901 `processar_pedido` is too complex (17 > 10)
leg_v0.py:9:5: PLR0912 Too many branches (22 > 12)
leg_v0.py:10:12: PLW0603 Using the global statement to update `TOTAL_PEDIDOS` is discouraged
leg_v0.py:18:19: S608 Possible SQL injection vector through string-based query construction
leg_v0.py:67:5: T201 `print` found
1 unsafe fix available with `--fix --unsafe-fixes`.
== legado/pedidos_legado.py
legado/pedidos_legado.py:39:12: PLW0603 Using the global statement to update `TOTAL_PEDIDOS` is discouraged
legado/pedidos_legado.py:51:5: T201 `print` found
1 unsafe fix available with `--fix --unsafe-fixes`.
== legado/precificacao.py
```
Sumiram `C901` (complexidade), `PLR0912` (ramos demais) e `S608` (**injeção de SQL**). Restam **dois avisos conscientes**: o `global TOTAL_PEDIDOS` e o `print`, que ficam para um próximo passo (o contador vai para métrica/log, e o `print` para `logging`); **não dá para fazer tudo de uma vez** sem perder a rede, e é melhor deixar o resto anotado do que misturar mudanças.

**8. O que ainda não foi feito (honestamente)**
- Dinheiro continua em **`float`**: o golden master prende esse comportamento. Migrar para `Decimal` **muda** valores em casos limite (ex.: `0,1 + 0,2`), então é um passo de **correção** com decisão de negócio, e merece o golden master atualizado e revisado caso a caso.
- O legado só roda em **SQLite** (`datetime('now')`, `lastrowid`); em PostgreSQL esses testes são pulados. A saída é substituí-lo pela rota nova (`create_order` do módulo) em vez de portá-lo.
- *Strangler Fig*: o próximo passo real seria rotear o fluxo novo ao lado do legado, comparando as respostas das duas implementações (**execução em sombra**) até o legado poder morrer.

## 🧠 Pausa para lógica
**Problema.** Um colega propõe: “vamos trocar `float` por `Decimal` junto com a extração das funções, é mais rápido.” Dê dois motivos para recusar e escreva a ordem correta dos commits.

<details><summary>Dica</summary>Se algo quebrar, você saberá se foi a refatoração ou a mudança de tipo?</details>

<details><summary>Solução comentada</summary>

(1) Misturar refatoração e mudança de comportamento **destrói o valor da rede**: se o golden master falhar, não dá para saber qual das duas mudanças causou. (2) `Decimal` altera resultados em casos limite; isso é uma **decisão de negócio** que merece revisão própria. Ordem: commit 1 `refactor: extract functions` (rede verde, nada muda); commit 2 `refactor: move pricing rules` (rede verde); commit 3 `fix: use Decimal for money` (a rede **vai falhar nos casos afetados**, o diff do golden master é revisado e regravado de propósito).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| “Reescrevo do zero, fica melhor” | Subestima o que o legado sabe (regras escondidas) | Caracterizar, refatorar, estrangular aos poucos |
| Refatoração e correção no mesmo commit | Passo grande demais | Um tipo de mudança por commit |
| Rede com 100% de cobertura que não pega nada | Cobertura sem asserções fortes | Mutação manual (estrague uma regra, veja quebrar) |
| Golden master gravado sem olhar | Aprova bugs | Revisar a saída e anotar o que é bug |
| Testes de caracterização frágeis (ids, datas) | Gravam o que varia | Normalizar o que depende do ambiente (ex.: `pedido_id` → `True`) |
| Refatorar sem rodar a rede a cada passo | Descobre o erro 5 passos depois | Rede verde a cada passo; passo vermelho é desfeito |
| Mexer em tudo de uma vez (global, print, float…) | Perde a rede | Lista de dívidas; um item por vez |
| Concatenar SQL | Falta de parâmetros | `execute(sql, [params])` sempre |

- **Primeiro a rede, depois o conserto.** Sem rede, só mexa no que for indispensável.
- **Commits pequenos e reversíveis**, com mensagens que dizem se mudam ou não o comportamento.
- **Regra do escoteiro:** deixe o código um pouco melhor do que encontrou, mas só dentro da rede.

## 🧩 Exercícios
**1. Fixação.** (a) O que é um teste de caracterização e quando usá-lo? (b) Por que 100% de cobertura não prova que a rede é boa? (c) Por que o golden master ficou verde após corrigir a injeção de SQL?

<details><summary>Solução</summary>

(a) Um teste que grava o comportamento **atual** do código, usado quando não há testes nem especificação. (b) Porque a cobertura mede que a linha **executou**, não que o resultado foi **verificado**; a mutação mostra se as asserções pegam erros. (c) Porque nenhum dos 270 casos usava entrada maliciosa; a correção só mudou o que era defeito.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `tests/test_legado_caracterizacao.py` com a matriz e o `legado.json`, com **100% de ramos** no legado
- [ ] Pelo menos **3 mutações manuais** detectadas, registradas no README
- [ ] Refatoração em **3 passos**, cada um com a rede verde e um commit
- [ ] Teste de segurança da injeção, escrito **antes** da correção (ver falhar, depois passar)
- [ ] `radon`/`ruff` antes e depois, na tabela do README
- [ ] Lista de dívidas pendentes (`float`, `global`, `print`, SQL do SQLite) anotada, sem “resolver tudo”
- [ ] Commits: `test(legacy): characterization tests`, `refactor(legacy): extract functions`, `fix(security): parametrize sku lookup`, `refactor(legacy): pure pricing rules`

**3. Desafio (opcional).** Troque `float` por `Decimal` em `precificacao.py`, rode o golden master e **liste quais dos 270 casos mudaram** e por quê. Decida, com a explicação, se o golden master novo deve substituir o antigo.

## 🎤 Na entrevista
- **Como você mexe num código sem testes?** Primeiro crio testes de caracterização (golden master) cobrindo os caminhos, meço a rede com cobertura de ramos e mutação, e refaço em passos pequenos, rodando a rede a cada passo.
- **Qual a diferença entre refatorar e corrigir um bug?** Refatorar muda a estrutura sem mudar o comportamento; corrigir muda o comportamento. Faço em commits separados.
- **Reescrever do zero ou refatorar?** Quase sempre refatorar e estrangular aos poucos (*Strangler Fig*): reescrever perde regras escondidas e adia o valor.
- **O que é injeção de SQL e como evitar?** Entrada do usuário interpretada como SQL; evita-se com consultas parametrizadas (`execute(sql, [params])`) ou o ORM.
- **Como você sabe que a refatoração melhorou algo?** Métricas (complexidade ciclomática, linhas, manutenibilidade), a rede continuando verde, e a facilidade de mudar (cupom novo = uma linha).

## 📚 Para ir além
- 📄 Catálogo: [Refactoring Guru — Refatoração](https://refactoring.guru/refactoring). Cheiros e técnicas (em inglês, com versão em português).
- 📄 Artigo: [Martin Fowler — Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html). Substituição gradual (em inglês).
- 📄 Referência: [OWASP — SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection). Como funciona e como evitar (em inglês).
- 📄 Documentação oficial: [Django — SQL cru](https://docs.djangoproject.com/en/5.2/topics/db/sql/). Parâmetros em `cursor.execute`.
- 📄 Documentação: [radon](https://radon.readthedocs.io/en/latest/). Métricas de complexidade.
- 📄 Documentação: [Regras do ruff](https://docs.astral.sh/ruff/rules/). `C901`, `S608` e outras.
- 📘 Livro: *Working Effectively with Legacy Code*, de Michael Feathers (em inglês). A referência sobre caracterização e “seams”.

## ✅ Checklist da aula
- [ ] Gravei um golden master e medi a rede (ramos + mutação)
- [ ] Refatorei em passos pequenos com a rede verde a cada passo
- [ ] Separei refatoração de correção (commits e testes)
- [ ] Corrigi uma injeção de SQL com teste escrito antes
- [ ] Medi o antes e o depois (radon/ruff) e anotei as dívidas restantes
