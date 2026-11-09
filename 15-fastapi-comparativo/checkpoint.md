# Checkpoint — Módulo 15: FastAPI (comparativo)

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. Como o FastAPI decide se um parâmetro vem do **caminho**, da **query** ou do **corpo**? Dê um exemplo de cada e diga o que acontece com `GET /itens/abc` quando `item_id: int`.
2. Compare um **serializer do DRF** e um **modelo Pydantic**: onde fica a regra de um campo, a regra entre campos, o campo calculado, o tratamento de campo desconhecido, o status e o formato do erro, e o idioma das mensagens. Por que usar `ProductIn` e `ProductOut` separados?
3. O 422 do FastAPI devolve `loc`, `type`, `msg` e `input`. O que cada um diz e qual o **risco de segurança** do `input`? O `"sim"` é aceito como booleano? E um preço `10.999` num campo de 2 casas?
4. Explique **Engine**, **Session** e `AsyncSession`. Por que uma sessão por requisição e por que ela **não** pode ser compartilhada entre tarefas concorrentes? O que é `MissingGreenlet` e como `lazy="raise"` e `contains_eager` ajudam?
5. Qual foi o defeito que a leitura do SQL revelou na listagem de produtos e como foi corrigido? Como você enxerga o SQL no SQLAlchemy e no Django?
6. Alembic: o que fazem `revision --autogenerate`, `upgrade head`, `downgrade -1`, `check`, `upgrade --sql` e `history`? Por que a migração `0001` **quebrou no PostgreSQL** e qual a correção? Por que o *autogenerate* exige revisão (cite renomeação)?
7. `async def` × `def` numa rota: onde cada uma executa, e o que o experimento mediu (20 e 60 requisições; três rotas; o `/ping`)? Qual a regra prática e por que `async` não acelera uma consulta lenta?
8. Como funciona `Depends` (árvore, cache por requisição, `yield`) e `dependency_overrides`? Quais decisões de segurança há em `is_staff`/`require_staff`? Que três imprecisões o OpenAPI gerado tinha?
9. Testes: o que faz o `ASGITransport` e o que ele **não** faz? Por que `StaticPool` com SQLite em memória e engine por teste? Como o `MockTransport` testa o cliente de frete (4 casos) e como o teste prova o ganho do `gather`? Por que `filterwarnings = ["error"]`?
10. Comparativo: das 16 consultas, quais 3 diferiram entre DRF e FastAPI e o que cada uma ensina? O que a medição de desempenho mostrou, por que a primeira medição estava **inválida** e o que você pode e **não** pode concluir? Quando escolher Django, FastAPI ou Flask?

<details><summary>Gabarito</summary>

1. Nome presente na URL (`/itens/{item_id}`) → **caminho**; tipo simples fora do caminho (`detalhe: bool`) → **query**; `BaseModel` (`item: Item`) → **corpo JSON**. `GET /itens/abc` com `item_id: int` → **422** `int_parsing`, `loc: ["path","item_id"]`; a função de rota nem roda.
2. Regra de um campo: `validate_<campo>` (DRF) × `@field_validator` (Pydantic). Entre campos: `validate()` × `@model_validator(mode="after")`. Calculado: `SerializerMethodField` × `@computed_field`. Campo desconhecido: DRF **ignora** × Pydantic ignora por padrão e `extra="forbid"` recusa (usado). Erro: DRF `400` `{campo: [msgs]}` em **pt-br** × FastAPI `422` lista `{type, loc, msg, input}` em **inglês**. Dois modelos para não expor/aceitar campo interno por acidente e para um contrato OpenAPI preciso.
3. `loc`: onde (`body`/`query`/`path`) e qual campo (até o índice da lista); `type`: o código do erro; `msg`: texto; `input`: o valor recebido. Risco: o `input` **ecoa** o que o cliente mandou (senha, token) para a resposta e logs; personalize o tratador de `RequestValidationError`. `"sim"` → **não** (`bool_parsing`; vale `true/false/1/0`). `10.999` → `decimal_max_places`.
4. Engine: fábrica de conexões com pool (uma por app). Session: unidade de trabalho (`add`, `commit`), **uma por requisição**. `AsyncSession`: versão com `await`; **não é segura para concorrência** (uma por tarefa). `MissingGreenlet`: acesso *lazy* (E/S escondida num atributo) em contexto async. `lazy="raise"` faz o esquecimento falhar cedo; `contains_eager`/`joinedload`/`selectinload` carregam explicitamente.
5. O `JOIN categories` aparecia **duas vezes** (o `join` do filtro mais o `joinedload`). Correção: `.join(Product.category).options(contains_eager(Product.category))` e `COUNT` direto no `JOIN`. Os testes passavam nas duas versões. SQLAlchemy: `echo=True` ou o logger `sqlalchemy.engine` em INFO; Django: `str(queryset.query)`, `connection.queries`, `CaptureQueriesContext`.
6. `--autogenerate` compara `Base.metadata` com o banco e propõe a migração; `upgrade head` aplica até a última; `downgrade -1` desfaz a última; `check` falha se o modelo diverge do banco (equivale a `makemigrations --check`); `upgrade --sql` imprime o SQL sem executar; `history` lista a cadeia. A `0001` foi gerada contra **SQLite** com `server_default=sa.text('1')`; no PostgreSQL deu `column "is_active" is of type boolean but default expression is of type integer`; correção `sa.true()` (cada dialeto renderiza o seu). Renomeação vira `drop_column` + `add_column` (perde dados); corrigir com `op.alter_column(..., new_column_name=...)`.
7. `async def` roda no laço de eventos (cooperativo, 1 thread); `def` roda numa thread do pool (40 por padrão). Medido: 20 requisições de 0,5 s → `async` correto 0,53 s, `def` 0,53 s, **`async` com `time.sleep` 10,02 s**; com 60: 0,59 s, 1,11 s (limite de 40 threads), 30,08 s; o `/ping` foi de 1,3 ms para 2 405 ms com 5 bloqueadoras. Regra: biblioteca async → `async def`; bloqueante → `def`; nunca bloquear dentro de `async def`; CPU → processos/fila. `async` só evita **ficar parado esperando**; a consulta continua lenta (índice, `EXPLAIN`).
8. `Depends` resolve os parâmetros da dependência (que podem depender de outras) por requisição, com **cache por requisição**; `yield` separa *setup*/*teardown* (sessão); `app.dependency_overrides[orig] = outra` troca em testes e deve ser limpo no fim. Segurança: `hmac.compare_digest` (tempo constante), **token vazio no servidor = escrita fechada**, token errado vira acesso público (não erro nem equipe). Imprecisões do OpenAPI: `GET` aparece protegido embora público; faltam `401/404/409/400`; a entrada de `price` aceita `number` ou `string` (saída é `string`).
9. `ASGITransport` chama o app como função (sem rede/porta) e **não executa o `lifespan`** (medi `[]`; com `lifespan_context`: `['startup','shutdown']`). `StaticPool` mantém **uma** conexão para o banco em memória não "sumir"; engine por teste porque conexões async pertencem ao laço (um laço por teste). `MockTransport`: sucesso (confere o parâmetro `cep`), 500 → `None`, `ReadTimeout` → `None`, JSON sem `valor` → `None`; o paralelo: 5 × 0,3 s em ~0,30 s (`dt < 0.6`) contra 1,5 s em série. `filterwarnings = ["error"]` transforma o aviso "coroutine never awaited" em falha (medido: `-W error::RuntimeWarning` **não** basta; um `assert client.get(...)` sem `await` passava).
10. Diferiram: `?page=99` (DRF 404 × FastAPI 200 vazio), `?page=0` (404 × 422) e `?ordering=password` (DRF 200 ignorando × FastAPI 400); 13 iguais. Ensinam que são **decisões de design** a documentar, e que um teste de contrato as encontra. Desempenho (mediana de 5 rodadas × 600): c=1 Django 330 × FastAPI 312 req/s; c=20 469 × 470; empate prático (±10%). A primeira medição estava inválida: o Django devolvia **429** (throttle `anon` e `user` do DRF) em >80% das requisições (`falhas=531..630`), e respostas de erro são rápidas. Pode concluir: numa API dominada pelo banco o framework não foi o gargalo; **não** pode concluir nada sobre alta concorrência de E/S, vários processos, 200 mil linhas, memória ou produção. Django: loja/sistema completo com admin e regras; FastAPI: API focada, muita E/S concorrente, contrato tipado, microsserviço; Flask: protótipo/serviço mínimo; não migrar por modismo.
</details>

## 🛠️ Entrega prática
Repositório `minishop` na tag `v4.2-fastapi` (a referência está em `projeto/referencia-api-m15/catalog-fastapi/`):
- [ ] **Serviço:** `catalog-fastapi/` com `GET /api/v1/products/` (filtros, busca, ordenação, paginação), `GET /{id}/`, `POST` (token), `DELETE` e `GET /categories/`, `/docs` e `/health/`
- [ ] **Modelos:** `ProductIn`/`ProductOut` com os validadores (SKU, preço > 0, regra de estoque), `extra="forbid"`, `Page[T]`
- [ ] **Banco:** SQLAlchemy 2 tipado, `lazy="raise"`, `contains_eager`, `0001` aplicada em SQLite **e** PostgreSQL, `alembic check` limpo e a `0002` de exemplo feita em uma cópia (upgrade, downgrade, `--sql`)
- [ ] **Async e DI:** `get_session` com `yield`, `is_staff`/`require_staff`, `page_params`; `async_demo` + `medir_async` rodados e **seus tempos** colados
- [ ] **Testes:** os **30** verdes em SQLite e em PostgreSQL (`CATALOG_TEST_DATABASE_URL`), `filterwarnings = ["error"]`, `ruff`, `ruff format --check` e `mypy --strict` limpos
- [ ] **Cliente externo:** `app/frete.py` com timeout e `MockTransport` (4 casos + paralelo)
- [ ] **Comparação:** `comparar.py` contra o Django: **13 iguais, 3 diferentes**, cada diferença explicada
- [ ] **Medição:** `carga.py` com `falhas=0`, 5 rodadas, mediana e faixa **suas**, e a armadilha do 429 registrada
- [ ] **Documento:** `15-fastapi-comparativo/comparativo.md` com 3 cenários seus e um ADR de 10 linhas
- [ ] Tag: `git tag -a v4.2-fastapi -m "MiniShop: catálogo em FastAPI (comparativo)" && git push --follow-tags`

**Prova de fogo (40 min, sem consultar):** (1) uma rota `async def` que chama `requests.get` deixa a API "travada" sob 30 clientes: explique, prove com um experimento de 10 linhas e corrija de duas maneiras; (2) o time quer "migrar o Django para FastAPI porque é 10× mais rápido": liste cinco perguntas, na ordem, que você faria antes de aceitar, e um experimento que você rodaria em um dia; (3) `alembic upgrade head` falha em produção no meio de uma migração com `NOT NULL`: o que você verifica, como recupera e o que muda no processo.

## 🪞 Autoavaliação
Nota de 0 a 3. Se algum item ficar em **0 ou 1**, refaça a aula antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| Tipos viram validação; Pydantic × serializer; ler o 422 | 01 | |
| SQLAlchemy 2, sessões, carregamento sem N+1, Alembic e seus limites | 02 | |
| `async def` × `def`, `Depends`, `dependency_overrides`, OpenAPI | 03 | |
| Testes async, `ASGITransport`, `MockTransport`, mesma suíte em dois bancos | 04 | |
| Endpoints do catálogo, teste de contrato entre APIs | 05 | |
| Comparativo, medição honesta e critérios de escolha | 06 | |

## 🧠 Lógica: lista de verificação
Resolveu sem olhar: `tags` como string e `Decimal` (15.01), renomear coluna sem perder dados (15.02), o tempo de `gather` e do passo de CPU (15.03), o `await` esquecido e o teste falso-positivo (15.04), páginas e `OFFSET` duplicando itens (15.05), a Lei de Amdahl no "10× mais rápido" (15.06)? Marque o que faltou e refaça.

## 🧪 Estado de verificação deste módulo
**Executado:** serviço `catalog-fastapi` (FastAPI 0.162.2, Pydantic 2.14.3, SQLAlchemy 2.1.8 async, Alembic 1.20.1, Python 3.13.18): **30 testes** em SQLite e em **PostgreSQL 18.6** (contêiner descartável `m15-lab-pg`), `ruff`, `ruff format`, `mypy --strict`; migrações `0001` (nos dois bancos) e `0002` de exemplo (upgrade, downgrade, `--sql`, `check`); servidor real com `uvicorn`, `/docs` e `/redoc` com 200 e `openapi.json` inspecionado; o experimento async (60 requisições, 30 s de bloqueio medidos); `comparar.py` contra o **Django do módulo 14** (13 iguais, 3 diferentes); medição de carga Django × FastAPI (5 rodadas × 600, c=1 e c=20, PostgreSQL); um Flask mínimo (3.1.3) com o cliente de testes; links das aulas com HTTP 200 (2026-11-09).

**Descobertas e correções (registradas nas aulas):** a listagem fazia `JOIN` duplicado (corrigido com `contains_eager`); a `0001` gerada em SQLite quebrou no PostgreSQL (`server_default`); a ordem de "Áudio" difere entre SQLite e PostgreSQL (collation) e `created_at` perde o fuso no SQLite; `ASGITransport` não roda o `lifespan`; `-W error::RuntimeWarning` não pega o `await` esquecido (só `-W error`); a primeira medição do Django estava inválida por **429** do throttle (`anon` **e** `user`); o `input` do 422 ecoa o valor recebido; `parar o servidor` com `pkill -f` encerrou o meu próprio shell mais uma vez (use o PID).

**Não executado:** `PUT/PATCH`, imagem, cache, JWT/usuários e pedidos no FastAPI; `Dockerfile` e CI do serviço; WebSocket; carga com vários processos, com 200 mil linhas ou com chamadas externas lentas; o Django em modo síncrono/WSGI e `async` do Django; Flask além de um exemplo mínimo; cobertura de testes; a tela do `/docs` em um navegador. Os números de desempenho são desta máquina (cliente e servidores juntos). Código em [`projeto/referencia-api-m15/catalog-fastapi/`](../projeto/referencia-api-m15/catalog-fastapi/README.md).

➡️ Próximo: [Módulo 16 — Pronto para o mercado](../16-pronto-para-o-mercado/README.md).
