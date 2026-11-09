# 5. FastAPI: endpoints do catálogo do MiniShop

> ⏱️ ~1h30 · Módulo 15 · Pré-requisitos: [15.01](01-fastapi-pydantic.md), [15.02](02-sqlalchemy-alembic.md), [15.03](03-async-dependencias-docs.md), [15.04](04-fastapi-async-httpx-testes.md), [6.08 (filtros, busca e ordenação)](../06-apis-rest/08-filtros-busca-ordenacao.md), [6.09 (paginação)](../06-apis-rest/09-paginacao-throttling.md)

> ✅ **Verificação.** Executado em 2026-11-09. As duas APIs (Django/DRF do módulo 14 e FastAPI) rodaram **lado a lado**, com o **mesmo seed** (64 produtos), e o script `scripts/comparar.py` fez **16 consultas** em cada uma: **13 respostas idênticas** (após remover `created_at` e `image_url`) e **3 diferenças reais**, listadas abaixo. 30 testes do serviço verdes em SQLite e em PostgreSQL 18.6. **Não implementado** no FastAPI (de propósito, é uma fatia): `PUT/PATCH`, upload de imagem, cache, usuários/JWT, pedidos, throttling, métricas e Docker. **Não medido:** comportamento com 200 mil produtos (a aula 06 mede só com o seed pequeno).

## 🎯 Objetivos
- Implementar `GET /products` (filtros, busca, ordenação, paginação), `GET /products/{id}`, `POST /products` e `DELETE` em FastAPI + SQLAlchemy + Pydantic, **equivalentes** aos do DRF
- Verificar a equivalência de forma **automatizada** (comparando as duas APIs) e interpretar as diferenças
- Reconhecer as decisões de design que mudam entre os frameworks (404 de página, validação do `ordering`, formato de erro)
- Listar o que **falta** para o serviço FastAPI substituir o catálogo do Django

## 🤔 Por que isso importa
É fácil dizer "FastAPI e DRF fazem o mesmo". Só uma comparação **executável** mostra onde são diferentes de verdade (e as diferenças são justamente o que quebra um front-end quando alguém troca o backend). Em time, a pergunta nunca é "qual é o melhor", e sim "o que muda para quem consome, e o que perdemos de funcionalidade". Aqui você aprende a responder com evidência.

## 💡 Intuição (explicação simples)
Imagine duas padarias que vendem o "mesmo pão": para saber se é igual, você **compra 16 pães diferentes de cada uma e confere um a um**. Treze são idênticos; em três, uma dá o troco de um jeito e a outra de outro. Essas três diferenças são o que importa registrar.

## 🔬 Como funciona por dentro
**Mapa DRF → FastAPI no catálogo**
| Peça do DRF | No FastAPI | Arquivo |
|---|---|---|
| `ProductViewSet.list` | `list_products` | `app/routers/products.py` |
| `ProductFilter` (`django_filters`) | parâmetros de query tipados (`category`, `price_min`, `price_max`, `in_stock`) | idem |
| `SearchFilter` (`icontains` em OR) | `ilike` em `name`, `sku`, `description` com parâmetro vinculado | idem |
| `OrderingFilter` (`ordering_fields`) | dicionário `ORDERING` + função `ordenacao` | idem |
| `StandardPagination` | `page_params` + `Page[T]` (`count/next/previous/results`) | `pagination.py`, `schemas.py` |
| `get_queryset` (público só vê ativos) | `where` condicional a `Staff` | idem |
| `DjangoModelPermissionsOrAnonReadOnly` | `Depends(require_staff)` (token de serviço) | `security.py` |
| `ProductSerializer` | `ProductIn` / `ProductOut` | `schemas.py` |
| `Product.objects.select_related("category")` | `contains_eager(Product.category)` | idem |
| `slugify` do Django | `app/slug.py` | `slug.py` |
| `seed` | `app/seed.py` (mesmos SKUs, preços, estoques) | `seed.py` |

**A listagem, passo a passo.** (1) Monta a lista de condições `where` a partir dos parâmetros (público só vê `is_active`). (2) Executa um `COUNT` com o mesmo `JOIN`/`WHERE`. (3) Executa o `SELECT` com `ORDER BY` (a coluna pedida **mais o `id`** como desempate, para a ordem não "pular" itens entre páginas), `LIMIT`/`OFFSET`. (4) Converte cada linha em `ProductOut` e monta `Page` com `next`/`previous` a partir da URL da requisição. São **duas** consultas, como no DRF.

**Segurança embutida no desenho.** `ordering` só aceita nomes de uma lista (nada de `ORDER BY` livre vindo do cliente); a busca usa **parâmetro vinculado** (nada de concatenar SQL); `extra="forbid"` rejeita campos desconhecidos no `POST`; `UNIQUE` no banco é a garantia final contra SKU duplicado (o `409` vem do `IntegrityError`, **não** de uma checagem "antes de inserir", que teria condição de corrida); o `DELETE` e o `POST` exigem o token; token vazio no servidor fecha tudo.

## 🛠️ Exemplo prático
**1. Subir os dois lados com o mesmo banco de dados lógico (seed idêntico).**
```bash
# FastAPI (SQLite local; troque CATALOG_DATABASE_URL para PostgreSQL se quiser)
cd projeto/referencia-api-m15/catalog-fastapi
uv sync && uv run alembic upgrade head && uv run python -m app.seed      # Seed ok: 64 produtos
CATALOG_API_TOKEN=segredo uv run uvicorn app.main:app --port 8815 &

# Django (módulo 14, com banco temporário)
cd ../../referencia-api-m14
DEBUG=1 DATABASE_URL=sqlite:////tmp/dj-m15.sqlite3 uv run python manage.py migrate && \
DEBUG=1 DATABASE_URL=sqlite:////tmp/dj-m15.sqlite3 uv run python manage.py seed       # Seed ok: 64 produtos
DEBUG=1 DATABASE_URL=sqlite:////tmp/dj-m15.sqlite3 uv run python manage.py runserver 8816 --noreload &
```
Cuidado: o `DEBUG=1` aqui é **só para o seed** (ele cria usuários com senha conhecida; o comando recusa rodar sem isso, aula 9). **Não** reuse esse banco depois.

**2. Chamadas reais ao FastAPI.**
```bash
curl -s "localhost:8815/api/v1/products/?page_size=2"
# {"count":61,"next":"http://localhost:8815/api/v1/products/?page_size=2&page=2","previous":null,
#  "results":[{"id":49,"sku":"CAS-049","name":"Cadeira Básico","slug":"cadeira-basico","description":"Cadeira, versão Básico.",
#              "price":"701.20","stock":28,"is_active":true,"category":{"id":3,"name":"Casa","slug":"casa"},
#              "created_at":"2026-11-09T11:42:50.167784","in_stock":true}, ...]}

curl -s -X POST localhost:8815/api/v1/products/ -H 'Authorization: Bearer segredo' --json \
  '{"sku":"inf-900","name":"Nobreak Pro","price":"399.90","stock":3,"category_slug":"informatica"}'
# 201, cabeçalho Location: /api/v1/products/<id>/, corpo com sku "INF-900" (normalizado) e slug "nobreak-pro"  (o teste test_criar_exige_token confere isso)
```
Sem o token: `401` com `www-authenticate: Bearer` e `{"detail":"Credenciais ausentes ou inválidas."}`.

**3. A comparação automatizada.**
```bash
cd projeto/referencia-api-m15/catalog-fastapi
uv run python scripts/comparar.py http://localhost:8816 http://localhost:8815
```
Saída real:
```text
IGUAL     DRF=200 FastAPI=200  /products/
IGUAL     DRF=200 FastAPI=200  /products/?page_size=7&page=3
IGUAL     DRF=200 FastAPI=200  /products/?page_size=1000          <- aceito nos dois (o máximo é 100; com 61 itens, tudo cabe numa página)
IGUAL     DRF=200 FastAPI=200  /products/?category=audio
IGUAL     DRF=200 FastAPI=200  /products/?price_min=500&price_max=900
IGUAL     DRF=200 FastAPI=200  /products/?in_stock=true&ordering=-price
IGUAL     DRF=200 FastAPI=200  /products/?search=mouse
IGUAL     DRF=200 FastAPI=200  /products/?search=MOUSE&ordering=price
IGUAL     DRF=200 FastAPI=200  /products/?category=casa&in_stock=false
IGUAL     DRF=200 FastAPI=200  /products/?ordering=-created_at&page_size=5
DIFERENTE DRF=404 FastAPI=200  /products/?page=99
          DRF    : {"detail":"Página inválida.","code":"not_found"}
          FastAPI: {"count":61,"next":null,"previous":null,"results":[]}
DIFERENTE DRF=404 FastAPI=422  /products/?page=0
          DRF    : {"detail":"Página inválida.","code":"not_found"}
          FastAPI: {"detail":[{"type":"greater_than_equal","loc":["query","page"],"msg":"Input should be greater than or equal to ...
DIFERENTE DRF=200 FastAPI=400  /products/?ordering=password
          DRF    : {"count":61,"next":".../?ordering=password&page=2","previous":null,"results":[...]}
          FastAPI: {"detail":"ordering inválido: use um de ['created_at', 'name', 'price'] (prefixo - para decrescente)."}
IGUAL     DRF=200 FastAPI=200  /products/1/
IGUAL     DRF=404 FastAPI=404  /products/17/                      <- inativo, ambos escondem do público
IGUAL     DRF=404 FastAPI=404  /products/999999/
```
**13 iguais, 3 diferentes.** O script devolve código de saída 1 se houver diferença (útil como **teste de contrato** em CI, se você migrar de verdade). O que cada diferença ensina:
1. **Página fora do intervalo.** DRF: `404 Página inválida`; FastAPI (meu código): `200` com lista vazia. É uma **decisão de design**, não limitação do framework; escolha uma e documente. Para clientes que "paginam até o `next` ser nulo", ambas funcionam; para quem testa o erro, não.
2. **`page=0`.** DRF: `404` (trata como página inválida); FastAPI: `422` (o `Query(ge=1)` recusa antes da rota).
3. **`ordering=password`.** O DRF **ignora em silêncio** o campo não permitido e devolve a ordem padrão (200); o FastAPI, no meu código, **recusa com 400**. Recusar é mais honesto (o cliente descobre o erro de digitação); ignorar é mais tolerante. Note que o DRF **não** deixou ordenar por `password` (a lista é permitida), só não avisou.

**4. O que a comparação NÃO diz.** Ignorei `created_at` (cada banco criou os registros em instantes diferentes) e `image_url` (existe só no Django, módulo 13). A **ordem de itens com chave igual** pode divergir entre bancos (por isso o FastAPI desempata por `id`; o DRF, em `ordering=name`, depende do banco para empates). E o corpo `POST` não foi comparado (autenticação diferente: token de serviço × permissões de usuário do Django).

**5. Rodar os testes e o resto.**
```bash
uv run pytest -q                  # 30 passed
uv run ruff check . && uv run mypy app
```

**6. O que falta para "substituir" o catálogo do Django.** `PUT/PATCH`; upload de imagem (S3, aula 13.06); o cache com versão (aula 14.03); throttling e métricas; autenticação de **usuários** (hoje há só um token de serviço); logs JSON com `request_id`; `Dockerfile` e CI do novo serviço; e, sobretudo, **uma estratégia de convivência**: o FastAPI lendo o mesmo banco do Django (tabelas `catalog_*`, sem duplicar dados) ou tendo o seu próprio (e sincronizando). **Não implementei nada disso**; é trabalho de dias, e é exatamente o custo que a aula 06 coloca na balança.

## 🧠 Pausa para lógica
**Problema.** O catálogo tem 61 produtos ativos e `page_size=20`. (a) Quantas páginas existem? (b) O que a página 4 devolve no DRF e no FastAPI do projeto? (c) Um cliente que repete `GET ...&page=N` até `next == null` vê diferença entre os dois? (d) O que acontece se, entre a página 1 e a 2, alguém insere um produto que cai **antes** na ordem por nome?

<details><summary>Dica</summary>⌈61/20⌉. E pense em `OFFSET`: ele conta posições, não identidades.</details>

<details><summary>Solução comentada</summary>

(a) ⌈61/20⌉ = **4** páginas (20, 20, 20, 1). (b) A página 4 tem 1 item nos dois. A página **5**: DRF `404`, FastAPI `200` vazio. (c) Não: ambos terminam em `next == null` na página 4. (d) Com `OFFSET`, o item que era o 20º da página 1 passa a ser o 21º e **aparece de novo** no início da página 2 (duplicado); se a inserção fosse depois, ninguém notaria. É a fragilidade da paginação por `OFFSET`; a solução é **paginação por cursor/keyset** (aulas 6.09 e 14.04), mais estável e de custo constante.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / erro | Causa | Correção |
|---|---|---|
| Duas vezes `JOIN categories` no SQL | `join` explícito + `joinedload` | `contains_eager` (aula 02) |
| `422` onde o front esperava `400` | convenções diferentes | documentar, ou tratador de erro que converta |
| `next`/`previous` com host errado atrás de proxy | `request.url` vê o host interno | `--proxy-headers`/`--forwarded-allow-ips` no uvicorn (aula 11.06) e `X-Forwarded-*` |
| Ordem instável entre páginas | `ORDER BY` sem desempate | adicionar `id` como último critério |
| SKU duplicado dá `500` | só `UNIQUE` no banco, sem tratar `IntegrityError` | capturar e responder `409` (testado) |
| Condição de corrida "checar e inserir" | verificação antes do `INSERT` | confiar no `UNIQUE` e tratar o erro |
| `ILIKE '%x%'` lento com muitos produtos | varredura completa | índice trigrama (`pg_trgm`) – só PostgreSQL (aula 14.04) |
| `LIKE` com `%` e `_` do usuário | caracteres curinga na busca | escapar (`ilike(..., escape="\\")`); decisão consciente |
| Preço em `float` na migração do banco | tipo errado | `Numeric(10, 2)` (aula 02) |
| Exposição de `/docs` com a escrita ativa | padrão | desligar ou proteger em produção |
| Comparar APIs com `created_at` | instantes diferentes | normalizar campos voláteis (como o script faz) |

**Boas práticas.** Teste de **contrato** entre implementações antes de migrar; escolha explícita para cada diferença; `Page[T]` genérico reaproveitável; separar `routers`, `schemas`, `models` como aqui; documente o que o novo serviço **não** faz.

## 🧩 Exercícios
**1. Fixação.** (a) Quantas consultas SQL a listagem faz e quais? (b) Por que desempatar o `ORDER BY` por `id`? (c) Por que o `409` vem do `IntegrityError`? (d) O que significa "teste de contrato" entre duas APIs?

<details><summary>Solução</summary>

(a) Duas: `COUNT(*)` e o `SELECT` da página (com `JOIN` carregando a categoria). (b) Sem desempate, itens com o mesmo valor podem trocar de lugar entre consultas, duplicando/omitindo itens na paginação. (c) Para não ter condição de corrida: o banco é quem garante a unicidade. (d) Comparar respostas de duas implementações para as mesmas entradas e acusar diferenças.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `catalog-fastapi/` rodando com `GET/POST /api/v1/products/` e a documentação em `/docs`
- [ ] `scripts/comparar.py` executado contra o Django: **13 iguais, 3 diferentes** (reproduza e explique cada diferença)
- [ ] Faça **uma** das 3 diferenças desaparecer (ex.: a página fora do intervalo devolver `404` como o DRF) e **atualize** o teste; o que mudou em `comparar.py`?
- [ ] Acrescente `PATCH /api/v1/products/{id}/` (corpo parcial, mesmas regras de validação) com testes
- [ ] Liste, em `docs/pendencias.md` do serviço, tudo que falta (seção 6) com estimativa de esforço
- [ ] Commit `feat(catalog-fastapi): products endpoints equivalent to drf, contract comparison script`

**3. Desafio (opcional).** Faça o FastAPI ler as **mesmas tabelas** do Django (`catalog_product`, `catalog_category`) no PostgreSQL, mapeando `__tablename__` e colunas, **sem** Alembic gerenciando essas tabelas. Quais riscos de ter dois sistemas escrevendo no mesmo esquema? Quem é dono das migrações?

## 🎤 Na entrevista
- **"Como você garantiria que a nova API se comporta como a antiga?"** — Testes de contrato: as mesmas requisições nas duas, comparação automática das respostas (ignorando campos voláteis), e decisão explícita para cada diferença; depois, migração gradual com *feature flag*/proxy.
- **"Como você faz paginação, filtros e busca com segurança numa API?"** — Parâmetros tipados e limitados (`page_size` com máximo), lista permitida para ordenação, parâmetros vinculados no SQL, e desempate estável; para listas grandes, cursor em vez de `OFFSET`.
- **"Por que tratar `IntegrityError` em vez de checar antes de inserir?"** — Checar-e-inserir tem condição de corrida entre requisições; a restrição `UNIQUE` do banco é atômica, então se captura a violação e se responde `409`.

## 📚 Para ir além
- 📄 Documentação oficial: [FastAPI — Tutorial (rotas, query, corpo)](https://fastapi.tiangolo.com/tutorial/).
- 📄 Documentação oficial: [SQLAlchemy — Carregamento de relacionamentos](https://docs.sqlalchemy.org/en/21/orm/queryguide/relationships.html). `contains_eager`.
- 📄 Documentação oficial: [FastAPI — Tratando erros](https://fastapi.tiangolo.com/tutorial/handling-errors/). Para trocar 422 por 400.
- 📄 Documentação oficial: [DRF — Paginação](https://www.django-rest-framework.org/api-guide/pagination/) e [Filtros](https://www.django-rest-framework.org/api-guide/filtering/). Para comparar com `Page[T]` e os parâmetros.
- 🏋️ Prática extra: rode `comparar.py` com `?search=` contendo `%` e `_` e veja o que cada API faz.

## ✅ Checklist da aula
- [ ] Implementei/li `GET` (lista e detalhe), `POST` e `DELETE` com as mesmas regras do DRF
- [ ] Rodei as duas APIs lado a lado e o `comparar.py` (13 iguais, 3 diferentes) e sei explicar cada diferença
- [ ] Sei que o `409` vem do `UNIQUE` e que o `ORDER BY` precisa de desempate
- [ ] Sei listar o que falta para o FastAPI substituir o catálogo do Django
- [ ] Os 30 testes passam em SQLite e PostgreSQL
