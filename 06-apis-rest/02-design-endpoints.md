# 2. Design de endpoints e convenções

> ⏱️ ~1h30 · Módulo 6 · Pré-requisitos: [6.01](01-principios-rest.md), [2.02 HTTP](../02-como-a-web-funciona/02-http-metodos-status-headers.md), [5.15](../05-django/15-paginacao-busca.md) (busca e paginação)

> ✅ **Verificação.** O código desta aula usa só a biblioteca padrão do Python 3 e **foi executado** em 2026-11-08; as saídas abaixo são as reais. Links conferidos (HTTP 200) na mesma data.

## 🎯 Objetivos
Ao final desta aula você consegue:
- Nomear recursos e URLs seguindo as convenções (substantivos no plural, minúsculas, hierarquia rasa)
- Escolher o **status HTTP** certo para cada resultado e o **formato** correto para dinheiro, datas e erros
- Decidir entre **filtros por query string**, **sub-recursos** e **ações** (`/cancel/`)
- Definir o formato de **listagem paginada** e de **erro** da API e o que é uma resposta consistente
- Escrever o **contrato** da API do MiniShop antes de programar (e revisá-lo com um linter simples)

## 🤔 Por que isso importa
O código de uma API se troca; o **contrato** (URLs, campos, status) não, porque há clientes dependendo dele: apps no celular que não se atualizam, parceiros, o seu próprio front-end. Mudar `/api/products` para `/api/produtos` depois que outros usam é um incidente. Por isso o desenho vem **antes** do código, e como júnior você será cobrado por consistência (“por que este endpoint devolve `200` com erro e aquele `400`?”) em *code review*.

## 💡 Intuição (explicação simples)
Pense nos **endereços de uma cidade**. Se toda rua segue o mesmo padrão (“Rua X, número Y”), qualquer pessoa acha qualquer lugar sem perguntar. Se cada bairro inventa o seu (“a casa depois do poste azul”), ninguém se orienta. Convenções de API são o **padrão de endereçamento**: quem aprendeu `GET /api/products/` adivinha `GET /api/orders/` sem abrir a documentação.

## 🔬 Como funciona por dentro
**1. URLs: recursos, não ações**
| Regra | Bom | Ruim |
|---|---|---|
| Substantivos, no **plural** | `/api/products/` | `/api/getProduct/`, `/api/product/` |
| Minúsculas e **hífen** (*kebab-case*) | `/api/order-items/` | `/api/orderItems/`, `/api/order_items/` |
| Identificador no caminho | `/api/products/12/` | `/api/products?id=12` |
| Hierarquia **rasa** (até 2 níveis) | `/api/orders/7/items/` | `/api/customers/1/orders/7/items/3/` |
| O **método** é o verbo | `DELETE /api/products/12/` | `POST /api/products/12/delete/` |
| Filtros na *query string* | `/api/products/?category=audio&ordering=price` | `/api/products/audio/by-price/` |
| Barra final **consistente** | sempre com (DRF) ou sempre sem | misturar |

- **Sub-recurso** (`/orders/7/items/`) quando o filho só existe dentro do pai. Se o item pode ser acessado sozinho, `/api/order-items/{id}/` costuma ser mais simples. Regra de bolso: se a URL tem mais de **dois ids**, achate.
- **Ações** que não são CRUD (cancelar, pagar, enviar e-mail) viram **sub-recurso de ação** com `POST`: `POST /api/orders/7/cancel/`. É a exceção aceita, desde que seja `POST` e o nome seja um verbo claro.
- **Coleção × item:** `GET /products/` (lista), `POST /products/` (cria), `GET /products/12/` (detalhe), `PUT/PATCH /products/12/` (altera), `DELETE /products/12/` (remove). Esse conjunto de cinco rotas é o que o DRF gera automaticamente (aula 04).

**2. Status HTTP: diga a verdade**
| Situação | Status |
|---|---|
| Leitura ou alteração com sucesso e corpo | `200 OK` |
| Recurso criado | `201 Created` (+ cabeçalho `Location`) |
| Sucesso sem corpo (ex.: `DELETE`) | `204 No Content` |
| JSON malformado / campo inválido | `400 Bad Request` |
| Não autenticado (sem token / token inválido) | `401 Unauthorized` (+ `WWW-Authenticate`) |
| Autenticado, sem permissão | `403 Forbidden` |
| Recurso não existe (ou não deve revelar que existe) | `404 Not Found` |
| Método não permitido naquela URL | `405 Method Not Allowed` (+ `Allow`) |
| Conflito de estado (duplicata, versão antiga) | `409 Conflict` |
| Dados válidos, mas violam regra de negócio (sem estoque) | `422 Unprocessable Content` (ou `400`, desde que seja **consistente**) |
| Limite de requisições excedido | `429 Too Many Requests` (+ `Retry-After`) |
| Erro nosso, inesperado | `500 Internal Server Error` |

Dois erros clássicos: devolver **`200` com `{"erro": ...}`** (os clientes e monitores acreditam que deu certo) e **`401` × `403`** trocados (401 = “quem é você?”, 403 = “eu sei quem é, mas não pode”).

**3. Formato dos dados**
- **Dinheiro:** nunca `float`. Use **string decimal** (`"59.90"`) ou **centavos inteiros** (`5990`). O DRF serializa `DecimalField` como string por padrão. A escolha tem de ser a mesma em toda a API.
- **Datas e horas:** **ISO 8601** em UTC, com `Z` (`"2026-11-08T14:30:00Z"`; RFC 3339 é o perfil usado na web). Evite formatos locais (`08/11/26` é ambíguo).
- **Nomes de campos:** uma convenção só. O DRF/Python usa `snake_case` (`created_at`); é a que adotamos, e o front converte se precisar.
- **Booleanos e nulos de verdade:** `true`/`false`/`null`, não `"sim"`, `"0"` ou `""`.
- **Identificadores:** inteiros ou UUID; opacos para o cliente (ele não deve deduzir nada do valor).

**4. Listas, erros e formato de resposta**
- **Lista paginada** (padrão do DRF `PageNumberPagination`; aula 09):
```json
{"count": 64, "next": "https://…/api/products/?page=2", "previous": null, "results": [ … ]}
```
  Devolver um objeto (e não um *array* solto) permite acrescentar `count`/`next` sem quebrar os clientes. Os links `next`/`previous` são a hipermídia (HATEOAS) que a maioria das APIs usa.
- **Erro:** um formato **único** para toda a API. O DRF devolve `{"detail": "…"}` para erros gerais e `{"campo": ["mensagem"]}` para validação. A RFC 9457 (*Problem Details*) padroniza `type/title/status/detail`; veremos o formato escolhido na aula 05.
- **Filtros, ordenação e busca:** `?category=audio`, `?price_min=10&price_max=50`, `?ordering=-price`, `?search=mouse`; todos opcionais, e parâmetros desconhecidos ignorados ou rejeitados de modo consistente (aula 08).
- **`PUT` × `PATCH`** (aula 6.01): `PUT` exige o recurso completo; `PATCH` aceita parcial. Muitas APIs aceitam só `PATCH` no dia a dia.
- **Cache e concorrência:** `ETag` + `If-None-Match` fazem o servidor responder `304 Not Modified` (sem corpo) quando nada mudou; `If-Match` evita sobrescrever alteração de outra pessoa (`412 Precondition Failed`).
- **Versionamento:** a URL precisa poder evoluir sem quebrar clientes (`/api/v1/…`); detalhes na aula 10. Já nasça com o prefixo `/api/v1/`.
- **Ordem do trabalho:** (1) liste os **recursos**, (2) escreva as **rotas** e os **status**, (3) escreva exemplos de **requisição/resposta**, (4) só então programe. Esse documento é o *contrato* (na aula 10 ele vira OpenAPI gerado do código).

## 🛠️ Exemplo prático
**1. Por que o formato dos dados importa (código executado)**
```python
# json_conv.py
import json
from datetime import datetime, timezone
from decimal import Decimal

preco = Decimal("59.90")
try:
    json.dumps({"price": preco})
except TypeError as e:
    print("Decimal direto no JSON →", type(e).__name__, ":", e)

print("float no JSON    :", json.dumps({"total": 0.1 + 0.2}))          # erro de ponto flutuante vai para o cliente
print("string decimal   :", json.dumps({"total": str(Decimal("0.1") + Decimal("0.2"))}))
print("centavos inteiros:", json.dumps({"total_cents": 30}))

agora = datetime(2026, 11, 8, 14, 30, tzinfo=timezone.utc)
print("data ISO 8601    :", json.dumps({"created_at": agora.isoformat().replace("+00:00", "Z")}))
print("data ambígua     :", json.dumps({"created_at": "08/11/26"}), "← 8 de novembro ou 11 de agosto?")
```
```bash
python3 json_conv.py
```
```text
Decimal direto no JSON → TypeError : Object of type Decimal is not JSON serializable
float no JSON    : {"total": 0.30000000000000004}
string decimal   : {"total": "0.3"}
centavos inteiros: {"total_cents": 30}
data ISO 8601    : {"created_at": "2026-11-08T14:30:00Z"}
data ambígua     : {"created_at": "08/11/26"} ← 8 de novembro ou 11 de agosto?
```
Três lições: o JSON puro não conhece `Decimal` (o DRF resolve com string); `float` leva o erro de arredondamento para o cliente; e a data em formato local é ambígua.

**2. Escolher o status certo (código executado)**
```python
# status.py
def status_para(metodo, resultado):
    """Escolhe o status HTTP conforme a convenção REST. `resultado` descreve o que aconteceu."""
    tabela = {
        ("GET", "ok"): 200,
        ("GET", "nao_existe"): 404,
        ("POST", "criado"): 201,
        ("POST", "dados_invalidos"): 400,
        ("POST", "regra_de_negocio"): 422,
        ("POST", "conflito"): 409,
        ("PUT", "substituido"): 200,
        ("PATCH", "alterado"): 200,
        ("DELETE", "removido"): 204,
        ("DELETE", "nao_existe"): 404,
        ("*", "sem_login"): 401,
        ("*", "sem_permissao"): 403,
        ("*", "metodo_nao_permitido"): 405,
        ("*", "muitas_requisicoes"): 429,
    }
    return tabela.get((metodo, resultado)) or tabela.get(("*", resultado))


for m, r in [("GET", "ok"), ("POST", "criado"), ("POST", "regra_de_negocio"), ("DELETE", "removido"),
             ("PATCH", "sem_login"), ("PUT", "sem_permissao"), ("GET", "muitas_requisicoes")]:
    print(f"{m:<6} {r:<18} → {status_para(m, r)}")
```
```text
GET    ok                 → 200
POST   criado             → 201
POST   regra_de_negocio   → 422
DELETE removido           → 204
PATCH  sem_login          → 401
PUT    sem_permissao      → 403
GET    muitas_requisicoes → 429
```

**3. O contrato do MiniShop (a API que vamos construir)**
| Método e URL | Efeito | Status de sucesso | Acesso |
|---|---|---|---|
| `GET /api/v1/products/` | lista paginada, com `?search=`, `?category=`, `?ordering=` | 200 | público |
| `GET /api/v1/products/{id}/` | detalhe | 200 / 404 | público |
| `POST /api/v1/products/` | cria produto | 201 + `Location` | `catalog.add_product` |
| `PATCH /api/v1/products/{id}/` | altera campos | 200 | `catalog.change_product` |
| `DELETE /api/v1/products/{id}/` | remove/desativa | 204 | `catalog.delete_product` |
| `GET /api/v1/categories/` | lista | 200 | público |
| `GET /api/v1/cart/` | meu carrinho com total | 200 | autenticado |
| `POST /api/v1/cart/items/` | adiciona item `{"product": 12, "quantity": 2}` | 201 | autenticado |
| `PATCH /api/v1/cart/items/{id}/` | muda a quantidade | 200 | autenticado |
| `DELETE /api/v1/cart/items/{id}/` | remove item | 204 | autenticado |
| `POST /api/v1/orders/` | finaliza o carrinho (`Idempotency-Key`) | 201 | autenticado |
| `GET /api/v1/orders/` e `/{id}/` | meus pedidos | 200 / 404 | dono |
| `POST /api/v1/orders/{id}/cancel/` | cancela e devolve estoque | 200 | dono |
| `POST /api/v1/auth/token/` | troca usuário/senha por JWT | 200 | público |

Exemplo de requisição e resposta (guarde no contrato):
```http
POST /api/v1/cart/items/ HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{"product": 12, "quantity": 2}
```
```http
HTTP/1.1 201 Created
Location: /api/v1/cart/items/31/
Content-Type: application/json

{"id": 31, "product": 12, "quantity": 2, "unit_price": "59.90", "subtotal": "119.80"}
```
```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/json

{"quantity": ["Estoque insuficiente: restam 1 unidade(s)."]}
```
Repare em como o contrato **reaproveita** as regras já escritas: as mesmas funções de serviço das aulas 5.16 e 5.17 (`add_item`, `create_order`) serão chamadas pela API. A regra mora no serviço; a view, a tela HTML e a API são só “entradas”.

**4. Um linter de rotas (código executado)**
Para transformar convenções em algo verificável, este script aplica as regras da tabela a uma lista de rotas.
```python
# linter.py
import re

REGRAS = []


def regra(f):
    REGRAS.append(f)
    return f


VERBOS = {"get", "create", "delete", "update", "add", "remove", "list", "criar", "excluir", "listar", "buscar"}


@regra
def sem_verbo(caminho):
    for parte in caminho.strip("/").split("/"):
        palavra = re.split(r"[-_A-Z]", parte)[0].lower() if parte and not parte.startswith("{") else ""
        if palavra in VERBOS:
            return f"verbo '{parte}' no caminho: use o método HTTP"


@regra
def colecao_no_plural(caminho):
    partes = [p for p in caminho.strip("/").split("/") if not p.startswith("{") and p != "api"]
    for p in partes[:1]:
        if not p.endswith("s"):
            return f"'{p}' parece singular: coleções ficam no plural"


@regra
def minusculas_e_hifen(caminho):
    for p in caminho.strip("/").split("/"):
        if not p.startswith("{") and (p != p.lower() or "_" in p):
            return f"'{p}': use minúsculas e hífen (kebab-case)"


@regra
def aninhamento_raso(caminho):
    n = sum(1 for p in caminho.strip("/").split("/") if p.startswith("{"))
    if n > 2:
        return f"{n} ids aninhados: prefira um caminho mais plano"


@regra
def barra_final_consistente(caminho):
    if not caminho.endswith("/"):
        return "sem barra final (o projeto usa barra final, como o DRF)"


def avaliar(rotas):
    for metodo, caminho in rotas:
        problemas = [msg for r in REGRAS if (msg := r(caminho))]
        print(f"{'OK ' if not problemas else 'XX '} {metodo:<6} {caminho}")
        for p in problemas:
            print(f"        - {p}")


avaliar([
    ("GET", "/api/products/"),
    ("GET", "/api/products/{id}/"),
    ("POST", "/api/products/create/"),
    ("GET", "/api/getProducts/"),
    ("GET", "/api/product/{id}/"),
    ("DELETE", "/api/order_items/{id}/"),
    ("GET", "/api/customers/{cid}/orders/{oid}/items/{iid}/"),
    ("POST", "/api/orders/{id}/cancel/"),
    ("GET", "/api/products"),
])
```
```bash
python3 linter.py
```
```text
OK  GET    /api/products/
OK  GET    /api/products/{id}/
XX  POST   /api/products/create/
        - verbo 'create' no caminho: use o método HTTP
XX  GET    /api/getProducts/
        - verbo 'getProducts' no caminho: use o método HTTP
        - 'getProducts': use minúsculas e hífen (kebab-case)
XX  GET    /api/product/{id}/
        - 'product' parece singular: coleções ficam no plural
XX  DELETE /api/order_items/{id}/
        - 'order_items': use minúsculas e hífen (kebab-case)
XX  GET    /api/customers/{cid}/orders/{oid}/items/{iid}/
        - 3 ids aninhados: prefira um caminho mais plano
OK  POST   /api/orders/{id}/cancel/
XX  GET    /api/products
        - sem barra final (o projeto usa barra final, como o DRF)
```
Note que `POST /api/orders/{id}/cancel/` passa de propósito: `cancel` é uma **ação** sobre um recurso, a exceção aceita. É um linter de brinquedo (a heurística de “plural” só olha o `s` final e erraria em `/api/status/`), mas mostra a ideia: convenção que se **automatiza** não depende da memória de quem revisa.

## 🧠 Pausa para lógica
**Problema (o linter, mais esperto).** Estenda o linter com uma regra de **substantivos irregulares**: aceite coleções que não terminam em `s` mas já são plurais ou invariáveis (`status`, `news`) através de uma lista de exceções configurável, e acrescente a regra “`PUT`/`PATCH`/`DELETE` exigem um `{id}` no caminho; `POST` não”. A assinatura de `avaliar` passa a receber o método.

<details><summary>Dica</summary>
As regras agora recebem <code>(metodo, caminho)</code>. A regra de id: <code>tem_id = "{" in caminho</code>; erro se <code>metodo in {"PUT","PATCH","DELETE"} and not tem_id</code>, ou se <code>metodo == "POST" and tem_id</code> — exceto quando a última parte for uma ação (<code>cancel</code>, <code>pay</code>).
</details>

<details><summary>Solução comentada</summary>

```python
EXCECOES = {"status", "news", "health"}
ACOES = {"cancel", "pay", "refund"}


def colecao_valida(metodo, caminho):
    partes = [p for p in caminho.strip("/").split("/") if not p.startswith("{") and p != "api"]
    if partes and partes[0] not in EXCECOES and not partes[0].endswith("s"):
        return f"'{partes[0]}' parece singular"


def id_coerente(metodo, caminho):
    ultima = caminho.strip("/").split("/")[-1]
    tem_id = "{" in caminho
    if ultima in ACOES:                                   # ação em sub-recurso: POST com id é esperado
        return None if metodo == "POST" else f"ação '{ultima}' deve ser POST"
    if metodo in {"PUT", "PATCH", "DELETE"} and not tem_id:
        return f"{metodo} precisa de um id no caminho"
    if metodo == "POST" and tem_id:
        return "POST cria na coleção: sem id no caminho"


for m, c in [("PATCH", "/api/products/"), ("POST", "/api/products/{id}/"), ("POST", "/api/orders/{id}/cancel/"),
             ("GET", "/api/status/"), ("DELETE", "/api/products/{id}/"), ("GET", "/api/orders/{id}/cancel/")]:
    erros = [e for f in (colecao_valida, id_coerente) if (e := f(m, c))]
    print(f"{m:<6} {c:<28}", "OK" if not erros else "; ".join(erros))
```
```text
PATCH  /api/products/               PATCH precisa de um id no caminho
POST   /api/products/{id}/          POST cria na coleção: sem id no caminho
POST   /api/orders/{id}/cancel/     OK
GET    /api/status/                 OK
DELETE /api/products/{id}/          OK
GET    /api/orders/{id}/cancel/     ação 'cancel' deve ser POST
```
(Executado em 2026-11-08; saída real.)
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / erro | Causa | Solução |
|---|---|---|
| Cliente trata `200` com `{"erro":…}` como sucesso | Status sempre `200` | Use o status certo (400/404/422…) |
| `404` onde deveria ser `405` (ou o contrário) | Rota existe, método não | `405` + `Allow` quando a URL existe mas o método não |
| `401` para quem está logado sem permissão | 401 × 403 trocados | Sem credencial = 401; sem permissão = 403 |
| `TypeError: Object of type Decimal is not JSON serializable` | `Decimal` em `json.dumps` | Serializer do DRF ou `str()` |
| Total “0.30000000000000004” no app | `float` no JSON | String decimal ou centavos |
| `/api/v1/products` e `/api/v1/products/` com respostas diferentes | Barra final inconsistente | Escolha uma e redirecione (`APPEND_SLASH`) |
| Front quebra quando uma lista vira objeto com `results` | Lista solta no início | Já comece com o envelope paginado |
| Campos `createdAt` e `updated_at` na mesma API | Mistura de convenções | Uma convenção para todos |
| Endpoint novo vazando campos internos (`password`, `cost`) | Expor o model inteiro | Escolher os campos no serializer (aula 03) |
| Mudar um campo e quebrar o app do cliente | Sem versionamento | `/api/v1/…` desde o início |

- **Consistência vale mais que a convenção “perfeita”.** Um time que decide e segue uma regra (mesmo não ideal) produz uma API mais fácil de usar.
- **Desenhe do ponto de vista do cliente:** o que ele quer fazer? A API não precisa espelhar as tabelas do banco.
- **Não exponha o banco.** `id` interno serve; campos como `cost_price`, `is_staff` ou hashes não devem sair.
- **Nunca coloque segredos na URL** (token em `?token=…`): fica em logs e histórico. Use o cabeçalho `Authorization`.
- Mudanças que **quebram** (remover/renomear campo, mudar tipo) exigem nova versão; mudanças **compatíveis** (campo novo opcional) não.

## 🧩 Exercícios
**1. Fixação**
(a) Corrija: `POST /api/createOrder`, `GET /api/product/12`, `GET /api/orders?id=7`. (b) Qual status para: JSON malformado; senha errada no login; produto sem estoque no pedido; `DELETE` bem-sucedido? (c) Por que a lista vem num objeto com `results` e não num *array* solto? (d) Como representar R$ 59,90 e como representar 8 de novembro de 2026 às 14h30 em Brasília?

<details><summary>Solução</summary>

(a) `POST /api/v1/orders/`, `GET /api/v1/products/12/`, `GET /api/v1/orders/7/`. (b) `400`; `401` (credenciais inválidas) ; `422` (ou `409`/`400` se for a regra do time, mas consistente); `204`. (c) Permite acrescentar `count`, `next` e `previous` sem quebrar clientes. (d) `"59.90"` (string decimal) ou `5990` (centavos); `"2026-11-08T17:30:00Z"` (ISO 8601 em UTC; Brasília é UTC−3).
</details>

**2. Aplicação no projeto MiniShop**
Escreva o contrato antes do código.

Critérios de pronto (em `docs/api-contrato.md`):
- [ ] Tabela de rotas do MiniShop (método, URL, efeito, status de sucesso e de erro, acesso), com prefixo `/api/v1/`
- [ ] Convenções adotadas: plural, kebab-case, `snake_case` nos campos, dinheiro como string decimal, datas ISO 8601 em UTC
- [ ] Um exemplo completo de requisição e resposta para: listar produtos (com paginação), adicionar ao carrinho, criar pedido (com `Idempotency-Key`) e um erro de validação
- [ ] Formato único de erro documentado (campo → lista de mensagens; erro geral em `detail`)
- [ ] Lista dos campos **expostos** e dos **ocultos** em `Product` (ex.: nunca expor dados internos)
- [ ] Todas as rotas passam no linter (adapte o `linter.py` à sua lista)
- [ ] Commit `docs(api): v1 contract`

<details><summary>Solução de referência (trecho)</summary>

```markdown
## GET /api/v1/products/?search=mouse&ordering=price
200 OK
{"count": 3, "next": null, "previous": null,
 "results": [{"id": 12, "sku": "MOU-1", "name": "Mouse sem fio", "price": "59.90", "stock": 5,
              "category": {"id": 2, "name": "Periféricos", "slug": "perifericos"}, "image": null}]}

## POST /api/v1/orders/    (cabeçalho Idempotency-Key: <uuid>)
201 Created, Location: /api/v1/orders/7/
{"id": 7, "status": "pending", "total": "119.80", "created_at": "2026-11-08T17:30:00Z",
 "items": [{"product": 12, "quantity": 2, "unit_price": "59.90", "subtotal": "119.80"}]}
422 {"detail": "Estoque insuficiente: Mouse: restam 1, você pediu 2."}
```
Campos ocultos de `Product`: nenhum dado de custo/margem (não existem hoje; a regra vale para o futuro) e nada de `updated_at` interno se não houver necessidade.
</details>

**3. Desafio (opcional)**
Escreva a especificação do contrato como um **OpenAPI** mínimo (YAML) com 3 rotas e cole-o em um visualizador de OpenAPI (Swagger Editor, por exemplo). Compare depois com o que o `drf-spectacular` gerará automaticamente na aula 10.

## 🎤 Na entrevista
- **Como você nomeia endpoints REST?** Substantivos no plural para coleções (`/products/`), identificador para o item (`/products/12/`), o verbo fica no método HTTP; filtros na query string; ações que não são CRUD como `POST` num sub-recurso (`/orders/7/cancel/`); minúsculas e hífen; prefixo de versão.
- **Qual a diferença entre 401, 403 e 404?** 401: não autenticado (falta ou é inválida a credencial); 403: autenticado, mas sem permissão; 404: o recurso não existe (e pode ser usado para não revelar a existência de um recurso alheio).
- **Como representar dinheiro e datas em JSON?** Dinheiro como string decimal ou centavos inteiros (nunca `float`); datas em ISO 8601/RFC 3339, em UTC.
- **Como você evita quebrar clientes ao evoluir a API?** Versionamento na URL (`/v1/`), mudanças compatíveis sem nova versão, depreciação avisada e documentação/contrato (OpenAPI) como referência.

## 📚 Para ir além
- 📄 Guia: [Guia de design de APIs do Google](https://cloud.google.com/apis/design). Convenções de recursos, nomes e métodos (em inglês).
- 📄 Guia: [Diretrizes de API REST da Zalando](https://opensource.zalando.com/restful-api-guidelines/). Muito completo, com exemplos de bom e mau uso.
- 📄 Guia: [Diretrizes de API da Microsoft](https://github.com/microsoft/api-guidelines). Outra referência de mercado.
- 📄 Especificação: [JSON:API](https://jsonapi.org/). Um formato de resposta padronizado (útil para comparar com o do DRF).
- 📄 Especificação: [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457). Padrão para corpo de erro.
- 📄 Especificação: [RFC 3339 — Date and Time on the Internet](https://www.rfc-editor.org/rfc/rfc3339). O perfil de datas ISO 8601 usado na web.
- 📄 Referência: [ETag (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Reference/Headers/ETag). Base do cache condicional (`304`).
- 🏋️ Prática extra: leia a referência de uma API pública bem conhecida (GitHub, Stripe) e liste as convenções que ela segue e as que quebra.

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Rotas em substantivos no plural, minúsculas com hífen e prefixo `/api/v1/`
- [ ] Status certo para cada situação (inclui 401 × 403 e 422)
- [ ] Dinheiro como string decimal/centavos e datas em ISO 8601 UTC
- [ ] Formato único de lista paginada e de erro
- [ ] Contrato do MiniShop escrito e validado pelo linter
