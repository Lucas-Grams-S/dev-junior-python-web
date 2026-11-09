# Checkpoint — Módulo 6: APIs REST

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. O que é uma API REST e quais restrições a definem? O que significa *stateless* e qual a consequência para a autenticação? Em que nível de Richardson está uma API que usa recursos, verbos e status corretos?
2. Diferencie método **seguro** de **idempotente** e classifique `GET`, `PUT`, `PATCH`, `DELETE` e `POST`. Por que `POST /orders/` precisa de uma `Idempotency-Key` e como o servidor deve tratá-la (inclusive quando a operação falha)?
3. Corrija: `POST /api/createOrder`, `GET /api/product/12`, `GET /api/orders?id=7`. Quais status usar para: JSON malformado, senha errada no login, produto sem estoque no pedido, `DELETE` bem-sucedido, método não permitido, limite de requisições excedido? Como representar dinheiro e datas em JSON?
4. Qual a diferença entre `Serializer` e `ModelSerializer`? O que fazem `read_only` e `write_only`? Em que ordem rodam as validações e por que `validate()` pode “não rodar”? Por que não usar `fields = "__all__"`?
5. Compare `@api_view`, `APIView`, views genéricas, `ViewSet` e `ModelViewSet`. O que o router gera? Para que servem `get_queryset()` e `@action`? Por que a regra de negócio fica no **serviço** e não na view?
6. Como você padroniza erros numa API DRF? Diferencie 400 e 422, descreva o formato adotado (`{campo: [...]}` e `{detail, code}`) e explique por que um erro 500 não pode vazar o *traceback*.
7. Descreva o JWT (três partes, o que é assinado e o que **não** é criptografado), o par access/refresh, a rotação com lista de bloqueio e a limitação de revogação. Por que sem credencial o DRF responde 401 com `JWTAuthentication` e 403 com `SessionAuthentication`?
8. Explique permissões no DRF: “negar por padrão”, `DjangoModelPermissions`, `has_permission` × `has_object_permission`, escopo no `get_queryset()` (404) × permissão de objeto (403) e o que é IDOR.
9. Como funcionam filtros, busca e ordenação seguras (`FilterSet`, `ordering_fields`)? Compare paginação por página e por cursor (e por que o cursor não repete itens). Para que serve o throttling, onde fica o contador e o que muda atrás de proxy/vários servidores?
10. O que é CORS, quem o impõe e o que é o preflight? Por que um cabeçalho personalizado (`Idempotency-Key`) exige `CORS_ALLOW_HEADERS`? Como o OpenAPI gerado do código, o versionamento (`/v1/`) e os testes (jornada, contrato, cobertura de rotas) mantêm a API sem quebrar clientes? Compare REST, GraphQL e gRPC em uma frase cada.

<details><summary>Gabarito</summary>

1. Estilo de arquitetura sobre HTTP: recursos com URI, representações (JSON), interface uniforme (verbos), **sem estado**, cache e camadas. *Stateless*: cada requisição traz tudo de que o servidor precisa; a credencial vai em **toda** chamada (token/JWT no cabeçalho), e qualquer instância atende qualquer requisição. Recursos + verbos + status corretos = **nível 2** (o nível 3 acrescenta hipermídia).
2. **Seguro**: não altera estado (`GET`, `HEAD`, `OPTIONS`). **Idempotente**: repetir N vezes deixa o estado como com 1 (`GET`, `PUT`, `DELETE`; `PATCH` depende; `POST` **não**). Um *timeout* deixa o cliente sem saber se o pedido foi criado; com a chave, o servidor guarda `(usuário, chave) → resposta` **na mesma transação** do pedido e, na repetição, devolve o mesmo resultado (cabeçalho `Idempotent-Replayed`). Falhas **não** são guardadas, para a repetição poder ter sucesso depois.
3. `POST /api/v1/orders/`, `GET /api/v1/products/12/`, `GET /api/v1/orders/7/`. Status: `400`; `401`; `422` (regra de negócio); `204`; `405`; `429` com `Retry-After`. Dinheiro como **string decimal** ou centavos inteiros (nunca `float`); datas em **ISO 8601 UTC** com `Z`.
4. `ModelSerializer` deduz campos, validadores e `create/update` do model; `Serializer` declara tudo à mão. `read_only`: sai, mas é ignorado na entrada; `write_only`: entra, nunca sai. Ordem: campo (tipo + validadores) → `validate_<campo>` → `validate()`; este só roda se **todos** os campos passaram. `__all__` expõe qualquer coluna futura (inclusive sensíveis) e aceita escrita indevida: o contrato deve ser explícito.
5. `@api_view`: função; `APIView`: método por verbo; genéricas: `queryset` + `serializer_class` para um pedaço do CRUD; `ViewSet`: agrupa as ações; `ModelViewSet`: CRUD completo. O router transforma o viewset em rotas (`/x/`, `/x/{pk}/`, ações extras). `get_queryset()` define **o que** a requisição enxerga (escopo, `select_related`); `@action` cria rotas não-CRUD (`/orders/{id}/cancel/`). A regra no **serviço** serve a tela HTML, a API e tarefas, sem duplicar.
6. Um `EXCEPTION_HANDLER` converte tudo para um formato único: erros de **campo** como `{campo: [mensagens]}` e o resto como `{detail, code}`; exceções do domínio viram `422` com `code`. `400`: requisição malformada/campos inválidos; `422`: dados válidos que violam regra de negócio. O `500` volta em JSON genérico e o *traceback* vai só para o log: vazá-lo expõe caminhos, SQL e versões.
7. `cabeçalho.payload.assinatura` em Base64URL; a assinatura (HMAC com a chave secreta) impede alterar o payload, mas o conteúdo é **legível** (não criptografado): nada sensível nas claims. Access curto (minutos) em toda chamada; refresh longo para renovar; com **rotação** e *blacklist* o refresh usado/encerrado deixa de valer. Revogar o access antes do `exp` exige estado (consulta); por isso a validade é curta. O 401 com `WWW-Authenticate` só sai se a **primeira** classe de autenticação sabe emitir o cabeçalho (JWT sim, sessão não → 403).
8. `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` (esquecer = fechado) e exceções explícitas. `DjangoModelPermissions` mapeia `POST/PATCH/DELETE` para `add/change/delete` do model, atribuídas por **grupo**. `has_permission` roda antes da ação (lista e criação); `has_object_permission` só em `get_object()` (nunca na lista). Escopo no `queryset`: objeto alheio = **404**; permissão de objeto: **403**. IDOR é acessar objeto alheio trocando o id; evita-se filtrando a consulta pelo dono e testando com dois usuários.
9. `FilterSet` (django-filter) valida e aplica parâmetros declarados (valor inválido = 400); `ordering_fields` é a **lista permitida** (campo fora dela é ignorado); a visibilidade (inativos) fica no `get_queryset()`. **Página/`OFFSET`**: permite “ir à página N” e dá `count`, mas repete/omite itens se entram novos dados e fica lento nas páginas fundas; **cursor**: guarda o último item visto (`WHERE id < último`), custo constante e sem repetição, mas sem salto nem total. **Throttling** limita requisições por IP/usuário/escopo (`429` + `Retry-After`); o contador vive no **cache**; com vários processos precisa de cache compartilhado (Redis) e, atrás de proxy, `NUM_PROXIES`/`X-Forwarded-For` confiável.
10. CORS: o servidor declara por cabeçalhos quais origens podem **ler** suas respostas; **o navegador** impõe (curl ignora). O preflight (`OPTIONS`) precede requisições não simples (JSON, `Authorization`, `PUT/PATCH/DELETE`, cabeçalhos personalizados); se não autorizar, o pedido real **nem sai**. `Idempotency-Key` é cabeçalho personalizado: precisa estar em `CORS_ALLOW_HEADERS`, e o que o JavaScript precisa ler em `CORS_EXPOSE_HEADERS`. O OpenAPI (drf-spectacular) é gerado do código e validado na CI; `/api/v1/` permite evoluir (quebras → nova versão, compatíveis → mesma); os testes (jornada, contrato contra o `schema.yml`, cobertura de rotas, mutação) pegam regressões antes dos clientes. REST: recursos sobre HTTP, simples e cacheável; GraphQL: o cliente escolhe os campos (evita over-fetching, traz N+1/profundidade); gRPC: contrato `.proto`, binário sobre HTTP/2, ótimo entre serviços internos.
</details>

## 🛠️ Entrega prática
Repositório `minishop` na tag `v2.0-minishop-api`:
- [ ] `docs/api-desenho.md` e `docs/api-contrato.md`: recursos, rotas `/api/v1/`, status, formato de erro (`detail`/`code`), papéis, taxas e política de idempotência
- [ ] Serializers com campos explícitos e viewsets/router para produtos, categorias, carrinho e pedidos (incluindo `cancel`); regra de negócio **só** nos serviços
- [ ] Erros padronizados (`EXCEPTION_HANDLER` + `handler500` em JSON) e 422 para regras de negócio
- [ ] JWT (access 15 min, refresh com rotação e lista de bloqueio, logout) e `GET /auth/me/`
- [ ] Permissões “negar por padrão”, papéis por grupo (`Estoquista`, `Gerente`), `IsOwner` no cancelamento e escopo por usuário em carrinho e pedidos
- [ ] Filtros (`category`, `price_min/max`, `in_stock`), busca e ordenação com lista permitida; paginação por página (produtos) e por cursor (pedidos); throttling (`anon`, `user`, `login`)
- [ ] OpenAPI em `/api/schema/`, Swagger em `/api/docs/` e `schema.yml` commitado, com `spectacular --validate --fail-on-warn` limpo; versionamento por caminho
- [ ] CORS por origem explícita, só em `/api/`, incluindo `idempotency-key` e a exposição de `Idempotent-Replayed`
- [ ] `Idempotency-Key` no `POST /orders/` (com comando `purge_idempotency_keys`)
- [ ] Suíte `pytest`: matriz papel × ação, formato de erro, jornada, contrato, **cobertura de rotas do contrato 100%** e cobertura de `apps/` ≥ 90%
- [ ] `frontend/` consumindo a API (login, catálogo, carrinho, pedido), sem `innerHTML` com dado externo, com `node --test` verde e um E2E em navegador real
- [ ] Cinco sinais verdes: `pytest`, `check`, `makemigrations --check`, schema válido e cobertura de rotas; captura de tela em `docs/img/`
- [ ] Tag publicada: `git tag -a v2.0-minishop-api -m "MiniShop API v1" && git push --follow-tags`

**Prova de fogo (40 min, sem consultar):** (1) acrescente `GET /api/v1/products/{id}/related/` (ação de detalhe, só leitura, 5 produtos da mesma categoria, sem N+1) e escreva os testes de 200, 404 e contagem de consultas; (2) um cliente reclama que “`DELETE /products/12/` funcionou para um usuário sem permissão”: escreva primeiro o teste que **reproduz** o problema, depois corrija; (3) explique por que o `POST /orders/` repetido por causa de um *timeout* não cria dois pedidos e **prove** com um teste.

## 🪞 Autoavaliação
Nota de 0 a 3. Se algum item ficar em **0 ou 1**, refaça a aula antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| Princípios REST, idempotência, *stateless*, Richardson | 01 | |
| Convenções de URL, status, formato de dados, contrato | 02 | |
| Serializers: campos, validação, N+1 | 03 | |
| Views, viewsets, routers, `get_queryset`, `@action` | 04 | |
| Validação e erros padronizados (400/422/500) | 05 | |
| JWT: access/refresh, rotação, limites | 06 | |
| Permissões, escopo × objeto, IDOR | 07 | |
| Filtros, busca e ordenação seguras | 08 | |
| Paginação (página × cursor) e throttling | 09 | |
| OpenAPI, Swagger, versionamento | 10 | |
| CORS e preflight | 11 | |
| Testes de API: jornada, contrato, cobertura, mutação | 12 | |
| GraphQL/gRPC (conceito) e `Idempotency-Key` | 13 | |
| Front consumindo a API: tokens, erros, XSS, E2E | 14 | |

## 🧠 Lógica: lista de verificação
Resolveu sem olhar: `pode_repetir` e chave de idempotência (6.01), linter de rotas (6.02), mini serializer (6.03), mini router (6.04), achatar erros (6.05), JWT à mão com HMAC (6.06), permissões compostas com `& | ~` (6.07), ordenação multi-campo segura (6.08), paginação por cursor × offset (6.09), classificação de mudanças e diff de OpenAPI (6.10), decisão de CORS (6.11), cobertura de rotas (6.12), armazém de chaves com TTL (6.13), `comRetry` com `Retry-After` (6.14)? Marque o que faltou e refaça.

## 🧪 Estado de verificação deste módulo
Diferente das aulas 12 a 18 do módulo 5, **o código das aulas 03 a 14 foi executado**: num laboratório com Django 5.2.19, DRF 3.18.3, simplejwt 5.5.1, drf-spectacular 0.30.0, django-filter 26.2, django-cors-headers 4.9.0, graphql-core 3.3.2 e gRPC 1.85, reproduzindo o MiniShop do módulo 5 (modelos, serviços e seed). O laboratório fechou com **65 testes pytest**, **93% de cobertura**, **20/20 operações do contrato com teste**, schema OpenAPI sem avisos, **12 testes `node --test`** do cliente e **15 verificações de ponta a ponta no Chrome 156** (via Puppeteer). As aulas 01 e 02 executam programas só com a biblioteca padrão. **Não foram executados:** o trecho ilustrativo de `v2` (aula 10, exemplo 5) e os desafios opcionais de cada aula. Os **83 links** de “Para ir além” foram conferidos com HTTP 200 em 2026-11-08. O **laboratório não foi PostgreSQL**: a concorrência real (aula 5.17) e o `ILIKE` continuam a ser comprovados no seu ambiente.

➡️ Próximo: [Módulo 7 — Comunicação síncrona e assíncrona](../07-sincrono-assincrono/README.md).
