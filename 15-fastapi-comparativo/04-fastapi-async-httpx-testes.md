# 4. FastAPI: testes e chamadas async com `httpx`

> ⏱️ ~1h30 · Módulo 15 · Pré-requisitos: [15.03](03-async-dependencias-docs.md), [7.04 (httpx, timeouts e retries)](../07-sincrono-assincrono/04-httpx-timeouts-retries.md), [10.02 (parametrize e mocks)](../10-qualidade-testes/02-parametrize-mocks.md), [10.03 (testes de API)](../10-qualidade-testes/03-integracao-api-cobertura.md)

> ✅ **Verificação.** Executado em 2026-11-09 com **pytest 9.2.0, pytest-asyncio 1.4.1, httpx 0.28.1**. A suíte do `catalog-fastapi` tem **30 testes** (25 da API em `tests/test_produtos.py` + 5 do cliente de frete em `tests/test_frete.py`): **30 passaram em SQLite (memória) em ~2 s e 30 passaram em PostgreSQL 18.6 em ~3,3 s**; `ruff` e `mypy --strict` limpos. O ganho de paralelismo (5 consultas de 0,3 s em 0,30 s) foi medido pelo próprio teste. **Não medido:** cobertura (não configurei `pytest-cov` neste serviço), testes de WebSocket e testes com servidor real subido por `uvicorn`.

## 🎯 Objetivos
- Testar rotas async com `pytest-asyncio` e `httpx.AsyncClient(transport=ASGITransport(app=app))`, **sem rede e sem porta**
- Isolar o banco por **dependência substituída** e rodar a **mesma suíte** em SQLite e PostgreSQL
- Escrever um cliente HTTP assíncrono (`httpx.AsyncClient`) com **timeout**, falha controlada e cliente **injetado**, e testá-lo com `httpx.MockTransport`
- Executar chamadas independentes **em paralelo** (`asyncio.gather`) e provar o ganho em teste
- Reconhecer armadilhas: *lifespan* não roda, `StaticPool`, escopo do laço de eventos

## 🤔 Por que isso importa
Um serviço sem testes é um serviço que ninguém ousa mexer. No mundo async, há armadilhas novas (laços de eventos, conexões que "pertencem" a um laço, `await` esquecido que faz o teste passar por engano). E quase toda API de verdade **chama outras APIs** (frete, pagamento, e-mail): saber testar isso sem depender da internet é o que torna a suíte rápida e confiável (aula 10). Em entrevista: "como você testa código que chama um serviço externo?" é pergunta de rotina.

## 💡 Intuição (explicação simples)
Testar uma rota normalmente seria **subir a loja, abrir a porta e mandar um cliente de verdade**. O `ASGITransport` é um **boneco de teste** que entra direto na loja pelo caixa (chama o app como função), sem rua nem porta. Para o serviço de frete externo, o `MockTransport` é um **telefone de brinquedo**: do outro lado atende um roteiro seu ("responda 500", "demore", "devolva este JSON"). Assim você testa a **sua** reação a falhas que, no mundo real, só acontecem às 3 da manhã.

## 🔬 Como funciona por dentro
```mermaid
flowchart LR
    T[teste async] --> C[httpx.AsyncClient<br/>transport=ASGITransport]
    C -->|chama como função ASGI| A[app FastAPI]
    A --> D{Depends}
    D -->|override| S[sessão do banco de teste<br/>SQLite memória / PostgreSQL]
    T2[teste do cliente de frete] --> C2[httpx.AsyncClient<br/>transport=MockTransport]
    C2 -->|handler Python| H[resposta/erro que você escreveu]
```
**pytest-asyncio.** Roda funções `async def test_...` num laço de eventos. Com `asyncio_mode = "auto"` (no `pyproject.toml`) todo teste/fixture `async` é reconhecido sem `@pytest.mark.asyncio`. `asyncio_default_fixture_loop_scope = "function"`: um **laço novo por teste** (isolamento máximo; custo pequeno).

**Por que "laço por teste" importa.** Conexões async (asyncpg, aiosqlite) **pertencem ao laço** em que foram criadas. Um *engine* global reutilizado entre testes (cada um com seu laço) pode falhar ("attached to a different loop"). Por isso a fixture `engine` cria **um engine por teste** (`NullPool` em PostgreSQL; `StaticPool` em SQLite-memória, onde **uma** conexão compartilhada precisa existir, senão cada conexão enxerga um banco vazio diferente).

**`ASGITransport` e o *lifespan*.** O `httpx.ASGITransport` chama o app, mas **não executa** os eventos de `lifespan` (startup/shutdown). Medi: com `ASGITransport` direto, a lista de eventos ficou `[]`; envolvendo com `async with app.router.lifespan_context(app):` ficou `['startup', 'shutdown']`. Se o seu app inicializa coisas no `lifespan` (pool, cache, cliente HTTP), os testes precisam fazer isso explicitamente. O nosso `lifespan` só fecha o *engine*, por isso não precisamos.

**Cliente externo bem-comportado.** Regras (já vistas na aula 7.04, agora no `httpx.AsyncClient`):
1. **Sempre timeout** (`httpx.Timeout(2.0, connect=1.0)`): sem ele, uma dependência lenta prende sua requisição para sempre.
2. **Reaproveitar o cliente** (`AsyncClient` é um *pool* de conexões): criar um por chamada desperdiça conexões TCP/TLS.
3. **Injetar** o cliente (parâmetro da função): em teste entra o `MockTransport`, em produção o real.
4. **Falha controlada**: capturar `httpx.HTTPError` (timeout, conexão, `raise_for_status`), registrar, e decidir o que o seu serviço faz sem a resposta (aqui: devolve `None`; o catálogo segue sem frete, **falha aberta**, como na aula 14.03).
5. **Retentativas** só para operações idempotentes e com *backoff* (aula 7.07); não implementadas aqui.

## 🛠️ Exemplo prático
**1. Configuração** (`pyproject.toml`, trecho) e dependências de desenvolvimento (`uv`):
```toml
[dependency-groups]
dev = ["pytest", "pytest-asyncio", "httpx", "ruff", "mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
filterwarnings = ["error"]          # aviso vira falha: pega o `await` esquecido (ver "Pausa para lógica")
```

**2. Fixtures** (`tests/conftest.py`, trecho comentado):
```python
@pytest.fixture
async def engine():
    url = os.environ.get("CATALOG_TEST_DATABASE_URL")          # PostgreSQL se definida...
    if url:
        eng = create_async_engine(url, poolclass=NullPool)
        async with eng.begin() as conn: await conn.run_sync(Base.metadata.drop_all)
    else:                                                       # ...senão, SQLite em memória
        eng = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    async with eng.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()

@pytest.fixture
async def client(seeded, monkeypatch):
    async def _session():
        async with seeded() as s: yield s
    app.dependency_overrides[get_session] = _session            # a rota usa o banco de teste
    monkeypatch.setattr(settings, "api_token", TOKEN)           # token só dentro do teste
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```
Observe: o **seed** é o mesmo do Django (64 produtos; 3 inativos), usado nos testes e na comparação da aula 05.

**3. Testes da API** (`tests/test_produtos.py`, amostras). Note `async def` e `await`:
```python
async def test_lista_paginada_so_ativos(client):
    j = (await client.get("/api/v1/products/")).json()
    assert set(j) == {"count", "next", "previous", "results"}
    assert len(j["results"]) == 20 and j["count"] == 64 - 3

async def test_criar_exige_token(client, auth):
    assert (await client.post(URL, json=NOVO)).status_code == 401
    r = await client.post(URL, json=NOVO, headers=auth)
    assert r.status_code == 201 and r.json()["slug"] == "nobreak-pro"

@pytest.mark.parametrize(("mudanca", "campo"), [({"sku": "ABC123"}, "sku"), ({"price": "0"}, "price"),
                         ({"price": "10.999"}, "price"), ({"stock": -1}, "stock"), ({"intruso": 1}, "intruso"), ...])
async def test_validacao_422(client, auth, mudanca, campo):
    r = await client.post(URL, json={**NOVO, **mudanca}, headers=auth)
    assert r.status_code == 422
```
`parametrize` (aula 10.02) funciona igual. O arquivo cobre: paginação, filtros, busca, ordenação (e `ordering=password` recusado com 400), `page_size` limitado, detalhe/404, inativo oculto do público, token ausente/errado/vazio, validações, categoria inexistente (422), SKU duplicado (409), apagar e categorias.

**4. Cliente de frete + testes com `MockTransport`** (`app/frete.py`, `tests/test_frete.py`):
```python
async def consultar_frete(client: httpx.AsyncClient, cep: str) -> Decimal | None:
    try:
        r = await client.get("/frete", params={"cep": cep}, timeout=httpx.Timeout(2.0, connect=1.0))
        r.raise_for_status()
        return Decimal(str(r.json()["valor"]))
    except (httpx.HTTPError, KeyError, ValueError):
        logger.warning("frete_indisponivel cep=%s", cep, exc_info=True)
        return None

async def consultar_varios(client, ceps):
    valores = await asyncio.gather(*(consultar_frete(client, c) for c in ceps))
    return dict(zip(ceps, valores, strict=True))
```
```python
def cliente(handler):  # o "servidor" é uma função Python
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://frete.test")

async def test_timeout_vira_none():
    def h(request): raise httpx.ReadTimeout("lento demais", request=request)
    async with cliente(h) as c:
        assert await consultar_frete(c, "01001000") is None

async def test_varios_em_paralelo():
    async def h(request):
        await asyncio.sleep(0.3)
        return httpx.Response(200, json={"valor": "10"})
    async with cliente(h) as c:
        t0 = time.perf_counter(); r = await consultar_varios(c, ["1","2","3","4","5"]); dt = time.perf_counter() - t0
    assert dt < 0.6      # 5 x 0,3 s = 1,5 s em série; juntas, ~0,3 s
```
Cobrem: sucesso (e o parâmetro `cep` enviado), erro 500, timeout simulado, JSON sem o campo `valor` e o paralelismo.

**5. Rodar.**
```bash
cd projeto/referencia-api-m15/catalog-fastapi
uv run pytest -q
# 30 passed in ~2 s   (SQLite em memória)

docker run -d --name m15-lab-pg -e POSTGRES_PASSWORD=lab -p 127.0.0.1:55415:5432 postgres:18
docker exec m15-lab-pg psql -U postgres -c "create database catalog_test"
CATALOG_TEST_DATABASE_URL=postgresql+asyncpg://postgres:lab@127.0.0.1:55415/catalog_test uv run pytest -q --durations=3
# 30 passed in ~3.3 s  (o mais lento: test_varios_em_paralelo, 0.30 s)
docker rm -f m15-lab-pg                            # limpe o laboratório
```
O nome `m15-lab-pg` e a porta `55415` **não colidem** com o `minishop-pg` do curso (lição do incidente do módulo 11). Ferramentas: `uv run ruff check .` (inclui a regra `ASYNC`), `uv run ruff format --check .`, `uv run mypy app` (`--strict` via `pyproject`): todas limpas.

**6. Um achado do teste em dois bancos.** A primeira versão do teste de categorias comparava a **ordem** (`audio, casa, informatica`) e passava num banco e falhava no outro (collation, aula 02). Rodar a mesma suíte em **dois SGBDs** pegou isso; só SQLite não pegaria. O mesmo vale para o `server_default` da migração (aula 02): o teste em PostgreSQL é a prova.

## 🧠 Pausa para lógica
**Problema.** Um teste async faz `r = client.get("/health/")` (sem `await`) e depois `assert r.status_code == 200`. (a) O que acontece? (b) E se fosse `assert client.get("/x")` sem `await`? (c) Como o `ruff` ajuda? (d) 5 chamadas de 0,3 s feitas com `for ... await` em vez de `gather` levam quanto?

<details><summary>Dica</summary>Sem `await`, o que você tem na mão é a **corrotina**, não a resposta.</details>

<details><summary>Solução comentada</summary>

(a) `r` é uma corrotina: `r.status_code` levanta `AttributeError` (o teste falha, o que é bom), e o Python avisa `coroutine ... was never awaited`. (b) **Perigoso**: uma corrotina é um objeto "verdadeiro"; o `assert` **passa** sem executar nada. Teste falso-positivo! (c) **Medido** (arquivo de teste descartável): sem configuração, `test_a` falhou e `test_b`/`test_c` **passaram** com 2 avisos. `-W error::RuntimeWarning` e `-W error::pytest.PytestUnraisableExceptionWarning` **não** mudaram isso (o aviso nasce na coleta de lixo e o pytest o trata como "não levantável"). Já `-W error` (ou `filterwarnings = ["error"]` no `pyproject.toml`) fez os **dois** falharem. O `mypy` (com os testes anotados) acusa `test_c` (`unused-coroutine: ... Are you missing an await?`), mas **não** `assert client.get(...)` (`test_b`). O `ruff` não acusou nenhum. Portanto: `filterwarnings = ["error"]` + `mypy` nos testes + revisão. (d) Em série: 5 × 0,3 = **1,5 s**; com `gather`, ~0,3 s (o teste prova com `dt < 0.6`).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / erro | Causa | Correção |
|---|---|---|
| `RuntimeWarning: coroutine ... was never awaited` | faltou `await` | `await`; `filterwarnings = ["error"]` no pytest (medido: `-W error::RuntimeWarning` **não** basta) |
| Teste async "passa" sem rodar | função `async def` sem plugin/modo auto | `asyncio_mode = "auto"` ou `@pytest.mark.asyncio` |
| `no such table: products` em SQLite-memória | cada conexão vê um banco vazio | `StaticPool` + `check_same_thread=False` |
| `RuntimeError: ... attached to a different loop` | engine/conexão criada em outro laço | engine **por teste** (ou escopo de laço compatível); `NullPool` |
| Startup/shutdown do app não ocorrem nos testes | `ASGITransport` não roda o `lifespan` | `async with app.router.lifespan_context(app)` |
| `dependency_overrides` vaza para outros testes | não limpou | `app.dependency_overrides.clear()` no teardown da fixture |
| Teste de cliente depende da internet | usou serviço real | `httpx.MockTransport` / cliente injetado |
| `ReadTimeout` sem tratamento derruba a rota | cliente sem `try/except` | capturar `httpx.HTTPError`, decidir o fallback |
| `await` dentro de `asyncio.gather` com a **mesma** `AsyncSession` | sessão não é concorrente | uma sessão por tarefa |
| Suíte passa só em SQLite | diferenças de dialeto (booleano, collation, fuso) | rodar também em PostgreSQL (variável de ambiente) |
| Tempo de teste cresce | banco recriado por teste | aceitável aqui (~0,1 s); para suítes grandes, escopo de módulo + *rollback* por teste |

**Boas práticas.** Uma asserção principal por teste; nomes que dizem o comportamento; `parametrize` para variações de entrada inválida; nada de rede nos testes unitários; a **mesma suíte** nos bancos que você usa; testar também os **caminhos de erro** do cliente externo (timeout, 5xx, JSON malformado).

## 🧩 Exercícios
**1. Fixação.** (a) O que o `ASGITransport` evita? (b) Por que `StaticPool` com SQLite em memória? (c) Para que serve o `MockTransport`? (d) Qual a diferença entre `gather` e `await` em sequência? (e) O que o `ASGITransport` **não** faz?

<details><summary>Solução</summary>

(a) Servidor e rede: chama o app direto. (b) Para que todas as operações usem a mesma conexão (e portanto o mesmo banco em memória). (c) Responder a requisições do `httpx` com uma função sua, simulando o serviço externo. (d) `gather` inicia tudo junto e espera o conjunto (tempo ≈ o mais lento); a sequência soma os tempos. (e) Executar o `lifespan`.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `uv run pytest -q` verde (30) em SQLite **e** em PostgreSQL (com `CATALOG_TEST_DATABASE_URL`)
- [ ] Acrescente `test_lifespan_roda` que **prova** o comportamento medido acima (com e sem `lifespan_context`)
- [ ] Acrescente teste do frete para `httpx.ConnectError` e para resposta `404` (deve virar `None`)
- [ ] Confirme que `filterwarnings = ["error"]` está no `pyproject.toml` (os 30 testes seguem verdes) e mostre que um `await` esquecido (inclusive o `assert client.get(...)`) agora **falha** o teste; teste também `-W error::RuntimeWarning` e explique por que não basta
- [ ] Liste 3 diferenças entre este conftest e o `conftest.py` do Django (`APIClient`, `@pytest.mark.django_db`, fixtures)
- [ ] Commit `test(catalog-fastapi): async api tests on sqlite and postgres, mock transport for external calls`

**3. Desafio (opcional).** Implemente retentativa com *backoff* exponencial e *jitter* para `5xx` e timeouts em `consultar_frete` (máximo 3 tentativas) e teste com um `MockTransport` que falha duas vezes e responde na terceira. Quanto tempo total máximo a chamada pode levar? E por que **não** retentar em `4xx`?

## 🎤 Na entrevista
- **"Como você testa uma API FastAPI?"** — `pytest` + `pytest-asyncio`, `httpx.AsyncClient` com `ASGITransport` (sem rede), banco isolado por `dependency_overrides`, `parametrize` nos casos inválidos; e a mesma suíte no SGBD de produção.
- **"Como testar um código que chama um serviço externo?"** — Injetar o cliente e usar um transporte simulado (`MockTransport`, ou `respx`/mocks), testando sucesso e também timeout, 5xx e resposta inesperada; nunca depender da internet.
- **"Por que um teste async pode passar sem executar nada?"** — Se faltar o `await`, a corrotina é um objeto verdadeiro e o `assert` passa; mitigar com avisos tratados como erro e revisão.

## 📚 Para ir além
- 📄 Documentação oficial: [FastAPI — Testando](https://fastapi.tiangolo.com/tutorial/testing/) e [testes assíncronos](https://fastapi.tiangolo.com/advanced/async-tests/).
- 📄 Documentação oficial: [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/stable/). Modos `auto`/`strict` e escopos de laço (em inglês).
- 📄 Documentação oficial: [HTTPX — Async](https://www.python-httpx.org/async/), [Transports](https://www.python-httpx.org/advanced/transports/) (`ASGITransport`, `MockTransport`) e [Timeouts](https://www.python-httpx.org/advanced/timeouts/).
- 📄 Documentação oficial: [FastAPI — Dependências](https://fastapi.tiangolo.com/tutorial/dependencies/). Para `dependency_overrides`.
- 🏋️ Prática extra: troque `NullPool` por um pool normal na fixture do PostgreSQL e provoque o erro de laço; explique a mensagem.

## ✅ Checklist da aula
- [ ] Testo rotas async com `ASGITransport`, sem subir servidor
- [ ] Isolo o banco com `dependency_overrides` e limpo no teardown
- [ ] Rodo a mesma suíte em SQLite e PostgreSQL
- [ ] Testo um cliente externo com `MockTransport` (sucesso, 5xx, timeout, JSON ruim)
- [ ] Provo o ganho do `gather` com um teste
- [ ] Sei que o `ASGITransport` não roda o `lifespan` e que `await` esquecido pode gerar teste falso-positivo
