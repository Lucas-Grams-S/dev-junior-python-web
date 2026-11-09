# 1. Pirâmide de testes e fixtures

> ⏱️ ~1h30 · Módulo 10 · Pré-requisitos: [Módulo 9 (checkpoint aprovado)](../09-seguranca/checkpoint.md), [5.18 (consolidação do Django)](../05-django/18-consolidacao-seed.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19, pytest 9, pytest-django, pytest-randomly 5.0). **As saídas são reais.** O ponto de partida é a suíte que já existia (235 testes) e, como o módulo trata de *qualidade*, a aula **mede** antes de opinar.

## 🎯 Objetivos
- Explicar a **pirâmide de testes** (unidade, integração, ponta a ponta) e o que ela otimiza: **velocidade e diagnóstico**
- **Classificar** os testes do MiniShop por nível e medir o custo de cada um
- Escrever **fixtures** que reduzem repetição: fábricas, escopo, `yield` para limpeza e `conftest.py`
- **Medir e reduzir** o tempo de uma suíte (a nossa caiu de 39 s para 8,7 s)
- Garantir que os testes são **independentes**: passam em qualquer ordem

## 🤔 Por que isso importa
Testes valem pela **confiança** que dão para mudar o código. Uma suíte lenta deixa de ser rodada; uma suíte frágil (que falha “às vezes”) deixa de ser levada a sério; uma suíte cheia de repetição vira um peso na hora de mudar qualquer coisa. Em entrevistas, “como você estrutura os testes de um projeto?” é pergunta clássica, e a resposta madura é sobre **proporção, custo e independência**, não sobre ferramenta.

## 💡 Intuição (explicação simples)
Imagine a revisão de um carro. Dá para (1) testar **cada peça** na bancada (barato, rápido, aponta exatamente a peça que falhou), (2) testar **conjuntos** montados (motor com câmbio), e (3) **dirigir o carro inteiro** numa pista (mais realista, mas lento, caro, e se falhar você só sabe que “algo” falhou). A boa prática é ter **muitos** testes de bancada, **alguns** de conjunto e **poucos** de pista: é a pirâmide. As **fixtures** são a oficina montada antes de cada teste: ferramentas e peças no lugar, para o mecânico dizer só o que importa naquela verificação.

## 🔬 Como funciona por dentro
- **Os três níveis:**
  | Nível | O que exercita | Velocidade | Quando falha, você sabe… |
  |---|---|---|---|
  | **Unidade** | uma função/classe isolada (sem banco, sem rede) | milissegundos | exatamente onde |
  | **Integração** | várias peças reais juntas (serviço + banco, tarefa + fila) | dezenas de ms | em qual junção |
  | **Ponta a ponta (E2E)** | o sistema inteiro, como o usuário (API/navegador) | segundos | que “algo” quebrou |
- **A forma importa.** Pirâmide (base larga de unidades) é rápida e diagnostica bem. **Sorvete de casquinha** (muito E2E, pouca unidade) é lenta, frágil e cara de manter. Um bom desenho **empurra regra de negócio para código puro** (aulas 8.01 e 8.03) justamente para poder testá-la na base.
- **O que separa os níveis na prática** não é o nome, é o **custo**: toca banco? rede? relógio? processo externo? Quanto mais coisas reais, mais lento e mais difícil de diagnosticar.
- **Fixtures (pytest):** funções marcadas com `@pytest.fixture` que preparam (e opcionalmente desfazem) o que o teste precisa. O teste as **pede pelo nome** como parâmetro. Quatro ideias:
  1. **Escopo:** `function` (padrão: refaz a cada teste, máximo isolamento), `module`, `session` (uma vez só, mais rápido, mais risco de estado vazando).
  2. **`yield`:** o que vem antes do `yield` é preparação; o que vem depois é limpeza, mesmo que o teste falhe.
  3. **`conftest.py`:** fixtures compartilhadas pelo diretório, sem `import`.
  4. **Fábricas como fixture:** a fixture devolve uma **função** (`criar_produto(...)`), e o teste diz só o que é relevante (`estoque=0`), deixando o resto com padrões sensatos.
- **Anatomia de um bom teste (AAA):** **A**rrange (preparar), **A**ct (agir), **A**ssert (verificar), uma ideia por teste, nome que diz o comportamento (`test_produto_inativo_nao_entra_no_carrinho`), sem lógica condicional.
- **Independência:** cada teste cria o que usa e **não depende de outro**. Um teste que só passa depois de outro é um defeito escondido. A prova é rodar em **ordem aleatória** (`pytest-randomly`).
- **Medir antes de otimizar:** `pytest --durations=N` mostra os mais lentos e separa `setup`, `call` e `teardown`; um perfil (`cProfile`) mostra *onde* o tempo vai.

## 🛠️ Exemplo prático
**1. O ponto de partida: onde o tempo da suíte é gasto?** A suíte tinha 235 testes e levava ~39 s. `--durations` separa execução (`call`) de preparação (`setup`):
```bash
uv run pytest -q --durations=0 | grep -E "s (call|setup|teardown)" | awk '{t[$2]+=$1} END{for(k in t)print k, t[k]}'
```
```text
call   7.68
setup  31.53
```
**A preparação custava 4× mais que os testes em si.** Suspeita: o fixture `seed` (cria 64 produtos e 3 usuários). Em vez de supor, um perfil do comando (`perfil_seed.py`):
```text
Seed ok: 64 produtos
seed completo: 247 ms
3    0.000    0.000    0.161    0.054 /tmp/claude-1000/-home-lucas-docs-dev-junior/2ff48105-b6fe-4487-bd2d-98f127918b70/scratchpad/lab10/.venv/lib/pyt
3    0.000    0.000    0.161    0.054 /tmp/claude-1000/-home-lucas-docs-dev-junior/2ff48105-b6fe-4487-bd2d-98f127918b70/scratchpad/lab10/.venv/lib/pyt
3    0.000    0.000    0.161    0.054 /tmp/claude-1000/-home-lucas-docs-dev-junior/2ff48105-b6fe-4487-bd2d-98f127918b70/scratchpad/lab10/.venv/lib/pyt
3    0.000    0.000    0.158    0.053 /tmp/claude-1000/-home-lucas-docs-dev-junior/2ff48105-b6fe-4487-bd2d-98f127918b70/scratchpad/lab10/.venv/lib/pyt
3    0.157    0.052    0.157    0.052 {built-in method _argon2_cffi_bindings._ffi.argon2_hash}
70    0.001    0.000    0.060    0.001 /tmp/claude-1000/-home-lucas-docs-dev-junior/2ff48105-b6fe-4487-bd2d-98f127918b70/scratchpad/lab10/.venv/lib/py
6    0.000    0.000    0.003    0.001 /tmp/claude-1000/-home-lucas-docs-dev-junior/2ff48105-b6fe-4487-bd2d-98f127918b70/scratchpad/lab10/.venv/lib/pyt
```
O `seed` leva ~250 ms, e **157 ms (64%) são 3 chamadas ao Argon2** (≈ 52 ms cada: lento *de propósito*, aula 9.04). Multiplicado por centenas de testes, explica os 31 s. Nada de errado na produção; o problema é pagar esse custo **nos testes**.

**2. A correção: um *hasher* rápido só na suíte** (`config/settings_test.py`, que herda tudo de `settings.py` e troca só o que precisa):
```python
"""Configuração SÓ para a suíte de testes. Tudo o mais é igual à de produção (herda de `config.settings`)."""
from django.contrib.auth.hashers import PBKDF2PasswordHasher

from .settings import *  # noqa: F401,F403


class HasherRapidoParaTestes(PBKDF2PasswordHasher):
    """Mesmo formato do PBKDF2, mas com 1 iteração: criar um usuário custa microssegundos, não ~50 ms de Argon2."""
    iterations = 1


PASSWORD_HASHERS = ["config.settings_test.HasherRapidoParaTestes"]
```
E o `pytest.ini` passa a usar `DJANGO_SETTINGS_MODULE = config.settings_test`. Resultado, duas execuções de cada:
```text
antes:
235 passed, 1 skipped in 39.37s antes (execução 1): 40.05 s 
235 passed, 1 skipped in 39.04s antes (execução 2): 39.72 s 
depois:
235 passed, 1 skipped in 8.69s depois (execução 1): 9.37 s 
235 passed, 1 skipped in 8.71s depois (execução 2): 9.38 s 
```
**39 s → 8,7 s (4,5× mais rápido)**, com os mesmos 235 testes. Mas atenção ao **custo escondido**: agora quase nenhum teste usa o Argon2 real. Os dois testes que **precisam** dele (`test_senhas_novas_usam_argon2id` e a migração de hash no login) pedem a fixture `hasher_de_producao`, que restaura a configuração de produção só para eles:
```python
def hasher_de_producao(settings):
    """Para os poucos testes que verificam o COMPORTAMENTO do hash real (Argon2id, migração de hashes)."""
    from config import settings as producao
    settings.PASSWORD_HASHERS = producao.PASSWORD_HASHERS
```
E a conferi **por mutação**: ao tirar `hasher_de_producao` de um desses testes, ele **falhou**; ao devolvê-la, `11 passed`. Regra: *acelerar a suíte nunca pode enfraquecer o que ela verifica*.

**3. Classificando os testes na pirâmide.** Em vez de rotular 235 testes à mão, o `conftest.py` marca cada um pelo que ele **usa** (banco? cliente HTTP?):
```python
# --- Pirâmide de testes: cada teste ganha um marcador de nível, pelo que ele USA (aula 10.01) ---------------------
import inspect  # noqa: E402

FIXTURES_DE_API = {"client", "api_as", "api_anonimo", "admin_client", "admin_user"}
USOS_DE_API = ("Client(", "APIClient(", "client.", "cliente_http(")
FIXTURES_DE_BANCO = {"db", "transactional_db", "seed", "django_db_reset_sequences"}


def pytest_collection_modifyitems(items):
    for item in items:
        fixtures = set(getattr(item, "fixturenames", []))
        try:
            codigo = inspect.getsource(item.function)
        except (OSError, TypeError):
            codigo = ""
        usa_banco = bool(fixtures & FIXTURES_DE_BANCO) or item.get_closest_marker("django_db") is not None
        usa_api = bool(fixtures & FIXTURES_DE_API) or any(u in codigo for u in USOS_DE_API)
        if usa_api:
            item.add_marker("api")
        elif usa_banco:
            item.add_marker("integracao")
        else:
            item.add_marker("unidade")
```
Os marcadores são registrados no `pytest.ini` com `--strict-markers` (um marcador com erro de digitação vira erro, não teste ignorado). Rodando cada nível separadamente:
```bash
uv run pytest -q -m unidade ; uv run pytest -q -m integracao ; uv run pytest -q -m api
```
```text
unidade    44 passed, 192 deselected in 1.03s
integracao 99 passed, 1 skipped, 136 deselected in 4.52s
api        92 passed, 144 deselected in 4.08s
```
| Nível | Testes | Tempo | Por teste |
|---|---|---|---|
| Unidade | 44 | 1,03 s | ≈ 23 ms |
| Integração | 99 (+1 pulado) | 4,52 s | ≈ 45 ms |
| API | 92 | 4,08 s | ≈ 44 ms |
**Leitura honesta:** não é uma pirâmide, é mais um **losango**: a base de unidades (44) é *menor* que as camadas de cima (99 e 92). Duas explicações: (1) muita regra do MiniShop ainda precisa do banco para ser exercitada (serviços e repositórios); (2) as diferenças de custo por teste são **pequenas aqui** porque o banco é SQLite em memória e a API roda no cliente de teste do Django (sem rede). Num projeto real, com PostgreSQL, filas e navegador, a unidade custa microssegundos e o E2E, segundos: a proporção importa muito mais. O exercício desta aula é **engordar a base**: a aula 8.02 mostrou que o repositório em memória permite testar a regra do pedido **sem banco** (`tests/test_pedido_dominio.py`, `test_precificacao.py`); cada regra movida para código puro vira um teste de milissegundos.

**4. Fixtures como fábricas: menos repetição.** Quatro arquivos repetiam a criação de categoria e produtos “à mão”:
```text
tests/test_sqli_defesa.py:11:    cat = Category.objects.create(name="Geral", slug="geral")
tests/test_legado_caracterizacao.py:36:    cat = Category.objects.create(name="Geral", slug="geral")
tests/test_legado_seguranca.py:13:    cat = Category.objects.create(name="Geral", slug="geral")
tests/test_lacunas.py:12:    return Product.objects.create(category=Category.objects.get(slug="audio"), ...
```
Fábricas no `conftest.py`:
```python
# --- Fábricas como fixtures: o teste diz só o que IMPORTA; o resto vem com padrões sensatos (aula 10.01) ---------
import itertools  # noqa: E402
from decimal import Decimal  # noqa: E402


@pytest.fixture
def criar_produto(db):
    contador = itertools.count(1)

    def _criar(sku=None, nome=None, preco="10.00", estoque=5, ativo=True, categoria=None, **extra):
        from apps.catalog.models import Category, Product
        categoria = categoria or Category.objects.get_or_create(slug="geral", defaults={"name": "Geral"})[0]
        n = next(contador)
        return Product.objects.create(category=categoria, sku=sku or f"TST-{n:03d}", name=nome or sku or f"Produto {n}",
                                      price=Decimal(preco), stock=estoque, is_active=ativo, **extra)
    return _criar


@pytest.fixture
def criar_usuario(db, django_user_model):
    contador = itertools.count(1)

    def _criar(username=None, senha="dev-somente-local-123", **extra):
        n = next(contador)
        return django_user_model.objects.create_user(username=username or f"usuario{n}", password=senha, **extra)
    return _criar
```
E os testes passam a dizer **só o que importa**:
```python
# antes (5 linhas de preparação)                 # depois
cat = Category.objects.create(name="Geral", ...)  def produtos(criar_produto):
Product.objects.create(category=cat, sku=..,          for sku, nome, ativo in [...]:
        name=.., price="10.00", stock=1, ...)             criar_produto(sku=sku, nome=nome, ativo=ativo)
```
Das 7 linhas de criação manual, **sobrou 1** (a de `test_lacunas.py`, que usa uma categoria do seed e foi mantida de propósito). A refatoração foi validada pela própria rede: o **golden master do legado** (270 casos, aula 8.07) continuou verde sem alterar uma linha do teste de comportamento. As fábricas têm os seus próprios testes (`tests/test_fabricas.py`), porque **fixture também é código**: produto padrão válido e ativo, só o que se pede muda, SKUs automáticos não colidem, usuário consegue autenticar.
```text
239 passed, 1 skipped          (235 anteriores + 4 das fábricas)
```

**5. Independência: ordem aleatória.** Se algum teste dependesse de outro, uma ordem diferente o revelaria:
```bash
uv add --dev pytest-randomly
for seed in 1 2 3 12345; do uv run pytest -q -p randomly --randomly-seed=$seed | tail -1; done
```
```text
seed 1     → 235 passed, 1 skipped in 8.68s
seed 2     → 235 passed, 1 skipped in 8.69s
seed 3     → 235 passed, 1 skipped in 8.64s
seed 12345 → 235 passed, 1 skipped in 8.66s
```
Quatro ordens diferentes, nenhuma falha: a suíte é independente. Se uma falhar, o `pytest-randomly` imprime a semente, e `--randomly-seed=<n>` **reproduz** exatamente a mesma ordem para depurar. (Esse resultado só é possível porque os testes que criam dados estão em transações revertidas pelo `pytest-django` e porque o teste de concorrência restaura o estado com `serialized_rollback`, ajustes feitos nos módulos 8 e 9.)

**6. Regras de bolso**
- Teste **comportamento**, não implementação: se você refatora e o teste quebra sem o comportamento mudar, o teste era frágil.
- Um **motivo** para falhar por teste; o nome conta a história.
- Prefira **dados mínimos explícitos** no teste a um “mundo” gigante escondido numa fixture.
- Escopo `function` por padrão; suba o escopo só com **medição** e com estado imutável.

## 🧠 Pausa para lógica
**Problema.** Uma suíte tem 10 000 testes: 8 000 de unidade (2 ms cada), 1 500 de integração (60 ms) e 500 E2E (3 s). Calcule o tempo total e a parte de cada nível. Depois, o time decide trocar 200 E2E por 200 testes de integração mais 400 de unidade. Qual o novo tempo e o que se perde em cobertura de comportamento?

<details><summary>Dica</summary>Multiplique quantidade por tempo e some; depois reflita sobre o que só o E2E verifica.</details>

<details><summary>Solução comentada</summary>

Antes: unidade 8 000 × 2 ms = **16 s**; integração 1 500 × 60 ms = **90 s**; E2E 500 × 3 s = **1 500 s (25 min)**. Total ≈ **1 606 s ≈ 26,8 min**, e 93% do tempo é o E2E (5% dos testes). Depois: unidade 8 400 × 2 ms = 16,8 s; integração 1 700 × 60 ms = 102 s; E2E 300 × 3 s = 900 s. Total ≈ **1 019 s ≈ 17 min** (−37%). O que se perde: só o E2E verifica a **integração de verdade** (navegador, rede, configuração, deploy); por isso se **mantém um conjunto pequeno de jornadas críticas** (login → compra → pagamento) e se cobre as variações nos níveis baixos. A troca é boa se os 200 removidos eram variações de regra (que a unidade cobre melhor) e ruim se eram jornadas distintas.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Suíte lenta que ninguém roda | Custos escondidos no `setup` | `--durations`, perfil; hasher rápido, menos dados por teste |
| Acelerar a suíte e enfraquecê-la | Trocar a configuração sem cobrir o caso real | Fixture que restaura o real nos testes que dependem dele; validar por mutação |
| Teste que só passa depois de outro | Estado compartilhado | `pytest-randomly`; cada teste cria o que usa |
| Fixture gigante “monta o mundo” | Reuso por comodidade | Fábricas pequenas; o teste explicita o relevante |
| `scope="session"` com dados mutáveis | Otimizar sem medir | Estado imutável ou `function`; medir o ganho |
| Repetição de `Model.objects.create(...)` em todo teste | Sem fábrica | Fixture-fábrica com padrões sensatos |
| Tudo é E2E | “Testa o que o usuário vê” | Pirâmide: regra em unidade, jornada crítica em E2E |
| Testes que dependem de relógio, rede ou aleatoriedade | Acoplamento ao mundo | Injetar relógio/semente; *fakes* nas bordas (aula 02) |
| Marcador com erro de digitação ignorado | Sem `--strict-markers` | Registrar marcadores e usar `--strict-markers` |
| Asserção fraca (`assert resposta`) | Preguiça | Verificar o valor/efeito específico |
| Testar detalhes privados | Acoplar à implementação | Testar a interface pública |

- **Rode a suíte rápida o tempo todo** (unidade) e a completa antes de integrar.
- **Quebrou? Ótimo, o teste serviu.** Nunca apague um teste para “passar”; entenda por que ele falhou.
- **Fixture é código:** nomeie bem, teste as fábricas, evite mágica.

## 🧩 Exercícios
**1. Fixação.** (a) Por que a pirâmide tem a base larga? (b) O que separa teste de unidade de teste de integração na prática? (c) Quando subir o escopo de uma fixture, e qual o risco? (d) Por que rodar em ordem aleatória?

<details><summary>Solução</summary>

(a) Testes de unidade são baratos, rápidos e apontam a causa; os de cima são caros e diagnosticam mal, então devem ser poucos. (b) O custo/realismo: unidade não toca banco, rede nem relógio; integração junta peças reais. (c) Quando a preparação é cara **e o estado é imutável**; o risco é um teste alterar o estado e afetar os seguintes. (d) Para descobrir dependências escondidas entre testes antes que elas virem falhas intermitentes.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] Marcadores `unidade`/`integracao`/`api` automáticos, registrados com `--strict-markers`, e a tabela de contagem e tempo por nível no README
- [ ] Medição da suíte (`--durations`) e **ao menos uma otimização com antes/depois** (como o hasher rápido), sem enfraquecer nenhum teste (validar por mutação)
- [ ] Fábricas `criar_produto` e `criar_usuario` (e mais uma à sua escolha, por exemplo `criar_pedido`), com testes das fábricas
- [ ] Eliminar a repetição de criação manual de objetos em pelo menos 3 arquivos de teste
- [ ] `pytest-randomly` instalado e a suíte passando em 4 sementes
- [ ] Mover **uma** regra de negócio para código puro e escrever os testes de unidade correspondentes (engordar a base)
- [ ] Commit `test: pyramid markers, factory fixtures and fast test hasher`

**3. Desafio (opcional).** Escreva um *plugin* mínimo de `conftest.py` que **falha a suíte** se algum teste de nível `unidade` abrir uma conexão com o banco (dica: a fixture `django_db_blocker`/`pytest.mark.django_db` ausente já bloqueia; verifique o que acontece e mostre a mensagem).

## 🎤 Na entrevista
- **O que é a pirâmide de testes?** Muitos testes de unidade (rápidos, baratos, diagnosticam bem), alguns de integração e poucos de ponta a ponta (lentos e frágeis); otimiza velocidade e clareza do diagnóstico.
- **Qual a diferença entre teste de unidade e de integração?** Unidade isola uma peça (sem banco/rede); integração exercita peças reais juntas, como serviço e banco.
- **O que é uma fixture no pytest?** Uma função que prepara (e limpa) o que o teste precisa, pedida pelo nome como parâmetro; tem escopo (`function`, `module`, `session`) e pode usar `yield` para limpeza.
- **Como acelerar uma suíte lenta?** Medir primeiro (`--durations`, perfil), atacar os custos de preparação, usar fábricas e dados mínimos, paralelizar, e mover regra para código puro; sem enfraquecer o que os testes verificam.
- **O que é um teste flaky e como evitar?** Um que falha de forma intermitente por dependência de ordem, tempo, rede ou aleatoriedade; evita-se com isolamento, injeção de relógio/semente, *fakes* e rodando em ordem aleatória.
- **O que significa AAA?** Arrange, Act, Assert: preparar, agir, verificar.

## 📚 Para ir além
- 📄 Documentação oficial: [pytest — Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html). Escopo, `yield`, `conftest.py` e fábricas.
- 📄 Documentação oficial: [pytest — Marcadores](https://docs.pytest.org/en/stable/how-to/mark.html). Registrar e selecionar por `-m`.
- 📄 Documentação: [pytest-django](https://pytest-django.readthedocs.io/en/latest/). Banco, transações e `settings` nos testes.
- 📄 Documentação oficial: [Django — Testes (visão geral)](https://docs.djangoproject.com/en/5.2/topics/testing/overview/) e [Acelerando os testes](https://docs.djangoproject.com/en/5.2/topics/testing/advanced/#speeding-up-the-tests). Hasher rápido e paralelismo.
- 📄 Artigo: [Martin Fowler — Test Pyramid](https://martinfowler.com/bliki/TestPyramid.html) e [A Prática da Pirâmide de Testes](https://martinfowler.com/articles/practical-test-pyramid.html). Proporções e exemplos (em inglês).
- 📄 Artigo: [Google Testing Blog — Just Say No to More End-to-End Tests](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html). Por que poucos E2E (em inglês).
- 🧰 Ferramenta: [pytest-randomly](https://pypi.org/project/pytest-randomly/). Ordem aleatória reprodutível (em inglês).
- 🧰 Biblioteca: [factory_boy](https://factoryboy.readthedocs.io/en/stable/). Fábricas de modelos mais completas, quando as fixtures simples não bastam (em inglês).

## ✅ Checklist da aula
- [ ] Sei explicar a pirâmide e o que cada nível custa e diagnostica
- [ ] Classifiquei os testes do MiniShop por nível e medi o tempo de cada um
- [ ] Reduzi o tempo da suíte medindo antes, sem enfraquecer nenhum teste
- [ ] Escrevi fábricas como fixtures e removi repetição
- [ ] A suíte passa em ordem aleatória (várias sementes)
