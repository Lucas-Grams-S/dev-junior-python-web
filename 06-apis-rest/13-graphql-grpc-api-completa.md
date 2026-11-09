# 13. GraphQL e gRPC (conceito) e fechamento da API do MiniShop

> ⏱️ ~1h30 · Módulo 6 · Pré-requisitos: [6.01](01-principios-rest.md) a [6.12](12-testes-de-api.md); [5.17](../05-django/17-pedidos-estoque-transacao.md) (pedido transacional)

> ✅ **Verificação.** Código executado em 2026-11-08 (Python 3.13, Django 5.2.19, DRF 3.18.3, `graphql-core` 3.3.2, `grpcio` 1.85.1 e `grpcio-tools`, SQLite). As saídas são as reais. O laboratório fechou com **64 testes passando, 93% de cobertura, `spectacular --validate --fail-on-warn` com 0 avisos e `makemigrations --check` limpo**.

## 🎯 Objetivos
Ao final desta aula você consegue:
- Comparar **REST, GraphQL e gRPC** (modelo, formato, pontos fortes e custos) e escolher conforme o cenário
- Explicar, com um exemplo executado, **por que o GraphQL evita over-fetching**, onde ele reintroduz o **N+1** e por que precisa de limites de profundidade
- Explicar o que o gRPC adiciona (contrato `.proto`, HTTP/2, binário, *streaming*) e ver uma chamada real
- Implementar a **`Idempotency-Key`** no `POST /orders/` (prometida nas aulas 01 e 02) e testá-la
- Fechar a API do MiniShop: contrato, testes, schema, segurança e checagens de entrega

## 🤔 Por que isso importa
“REST ou GraphQL?” é pergunta de entrevista e de reunião de arquitetura, e a resposta madura nunca é “um é melhor”: é “depende do cliente, da equipe e do custo”. Saber o que cada um resolve (e o que complica) evita tanto o *hype* quanto a resistência. Já a idempotência no `POST` de pedido é o tipo de detalhe que separa uma API de estudo de uma que pode cobrar um cliente duas vezes.

## 💡 Intuição (explicação simples)
Voltando ao **restaurante**. No **REST**, o cardápio tem pratos prontos: você pede “o prato 12” e recebe tudo o que vem nele (às vezes mais do que queria, às vezes precisa pedir um segundo prato para completar). No **GraphQL**, é um **bufê a quilo com balança**: você monta o prato dizendo exatamente quais itens quer, numa só ida ao balcão; o custo é que o restaurante precisa de regras para ninguém encher o prato com a cozinha inteira. O **gRPC** é o **interfone da cozinha**: entre funcionários, em código combinado e compacto, rapidíssimo, mas o cliente da rua não sabe usá-lo.

## 🔬 Como funciona por dentro
| | **REST** (nosso módulo) | **GraphQL** | **gRPC** |
|---|---|---|---|
| Modelo | **recursos** + verbos HTTP | **um endpoint**; o cliente envia uma *query* com os campos | **procedimentos** remotos (`rpc`) |
| Contrato | OpenAPI (opcional, gerado) | **schema tipado** (SDL), obrigatório | **`.proto`**, obrigatório, gera código |
| Formato | JSON (texto) | JSON | **Protocol Buffers** (binário) |
| Transporte | HTTP/1.1 ou 2 | HTTP (normalmente `POST /graphql`) | **HTTP/2** |
| O cliente escolhe os campos? | não (a resposta é fixa) | **sim** | não (a mensagem é fixa) |
| Cache HTTP | fácil (`GET`, `ETag`) | difícil (tudo é `POST`) | não aplicável |
| *Streaming* | limitado (SSE, WebSocket à parte) | *subscriptions* | **nativo** (4 modos) |
| Navegador | nativo | nativo | precisa de *gRPC-web*/proxy |
| Melhor para | APIs públicas, CRUD, integrações | muitos clientes com necessidades diferentes (apps móveis, painéis) | **comunicação entre serviços internos**, baixa latência |
| Armadilhas | *over/under-fetching*, versões | N+1, consultas caras/profundas, cache, autorização por campo | depuração mais difícil, não público |

- **Over-fetching** = a resposta traz campos que o cliente não usa; **under-fetching** = ele precisa de várias chamadas para montar uma tela. O GraphQL ataca os dois, ao custo de **empurrar a complexidade para o servidor**.
- **GraphQL em três ideias:** (1) um **schema** tipado descreve os tipos e as consultas possíveis; (2) cada campo tem um **resolver** (função) que sabe buscá-lo; (3) o cliente envia uma *query* e recebe **exatamente** a forma pedida. *Mutations* alteram dados; *subscriptions* enviam eventos.
- **Os problemas típicos do GraphQL** (e as defesas): **N+1** (o resolver de `category` roda uma vez por produto → olhe a seleção/use *dataloaders*), **consultas profundas** (`category { products { category { … } } }` → limite de profundidade/complexidade), **autorização por campo** (não por rota), **cache** (precisa de camada própria), **erros** (sempre `200` com uma lista `errors`: quebra o monitoramento por status).
- **gRPC em três ideias:** (1) o contrato é um arquivo **`.proto`** (mensagens + serviços); (2) o compilador `protoc` **gera código** de cliente e servidor em várias linguagens; (3) a mensagem trafega em **binário compacto** sobre HTTP/2, com *streaming*. Ótimo entre microsserviços (módulo 8); raro como API pública.
- **E o que usar no MiniShop?** REST. É o caso comum, o mais fácil de cachear, documentar e testar, e o que as vagas pedem. GraphQL entraria se houvesse vários apps com telas muito diferentes; gRPC, se o MiniShop virasse vários serviços internos (módulo 8).
- **Idempotência no `POST /orders/`** (aulas 01/02): o cliente gera um UUID por *intenção de compra* e o envia em `Idempotency-Key`. O servidor guarda `(usuário, chave) → resposta` **na mesma transação** que cria o pedido; repetir a chave devolve o mesmo resultado (cabeçalho `Idempotent-Replayed: true`) **sem** criar outro pedido nem baixar o estoque duas vezes. Falhas não são guardadas, para que o retry possa ter sucesso.

## 🛠️ Exemplo prático
**1. GraphQL na prática (executado com `graphql-core` sobre o ORM do MiniShop)**
```bash
uv add graphql-core
```
```python
import json
from graphql import build_schema, graphql_sync, parse
from graphql.language import ast
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient
from apps.catalog.models import Category, Product

SDL = """
type Category { id: ID!, name: String!, slug: String!, products(first: Int = 3): [Product!]! }
type Product { id: ID!, sku: String!, name: String!, price: String!, stock: Int!, category: Category! }
type Query { products(first: Int = 5, search: String): [Product!]!, product(id: ID!): Product }
"""
schema = build_schema(SDL)

def quer_categoria(info):
    """O resolver olha a seleção: só faz JOIN se o cliente pediu `category`."""
    for no in info.field_nodes:
        for sel in no.selection_set.selections:
            if sel.name.value == "category":
                return True
    return False

def resolve_products(info, first=5, search=None, otimizar=True):
    qs = Product.objects.filter(is_active=True).order_by("name")
    if search:
        qs = qs.filter(name__icontains=search)
    if otimizar and quer_categoria(info):
        qs = qs.select_related("category")
    return list(qs[:first])

OTIMIZAR = {"v": True}
root = {"products": lambda info, **kw: resolve_products(info, otimizar=OTIMIZAR["v"], **kw),
        "product": lambda info, id: Product.objects.filter(pk=id).first()}
schema.type_map["Category"].fields["products"].resolve = lambda cat, info, **kw: list(cat.products.filter(is_active=True)[:kw.get("first", 3)])
schema.type_map["Product"].fields["price"].resolve = lambda p, info: str(p.price)

def rodar(query, titulo):
    with CaptureQueriesContext(connection) as q:
        r = graphql_sync(schema, query, root_value=root)
    corpo = json.dumps(r.data, ensure_ascii=False, separators=(",", ":")) if r.data is not None else "—"
    print(f"{titulo:<44} → {len(corpo):>6} bytes | {len(q)} consultas" + (f" | ERRO: {r.errors[0].message}" if r.errors else ""))
    return r

print("--- 1) REST × GraphQL: mesma necessidade (SKU e preço de 20 produtos)")
rest = APIClient().get("/api/v1/products/", {"page_size": 20}).content
print(f"REST  GET /products/?page_size=20            → {len(rest):>6} bytes (traz TODOS os campos + categoria aninhada)")
r = rodar("{ products(first: 20) { sku price } }", "GraphQL { products { sku price } }")
print("amostra:", json.dumps(r.data["products"][:2]))

print("\n--- 2) pedir um campo relacionado: N+1 × resolver otimizado")
q = "{ products(first: 20) { sku category { name } } }"
OTIMIZAR["v"] = False; rodar(q, "sem otimização (1 consulta por categoria)")
OTIMIZAR["v"] = True;  rodar(q, "com select_related guiado pela seleção")

print("\n--- 3) consulta aninhada em profundidade")
profunda = "{ products(first: 5) { category { products(first: 3) { category { products(first: 3) { sku } } } } } }"
rodar(profunda, "5 produtos → categoria → produtos → categoria → …")

def profundidade(no, nivel=0):
    if isinstance(no, ast.FieldNode) and no.selection_set:
        return max(profundidade(s, nivel + 1) for s in no.selection_set.selections)
    if isinstance(no, ast.OperationDefinitionNode):
        return max(profundidade(s, 0) for s in no.selection_set.selections)
    return nivel + (1 if isinstance(no, ast.FieldNode) else 0)

def executar_com_limite(query, limite=4):
    d = max(profundidade(op) for op in parse(query).definitions)
    return f"RECUSADA: profundidade {d} > limite {limite}" if d > limite else "aceita (profundidade %d)" % d
print("limite de profundidade 4 →", executar_com_limite(profunda), "|", executar_com_limite("{ products { sku category { name } } }"))
```
```text
--- 1) REST × GraphQL: mesma necessidade (SKU e preço de 20 produtos)
REST  GET /products/?page_size=20            →   5619 bytes (traz TODOS os campos + categoria aninhada)
GraphQL { products { sku price } }           →    714 bytes | 1 consultas
amostra: [{"sku": "CAS-049", "price": "701.20"}, {"sku": "CAS-052", "price": "742.30"}]

--- 2) pedir um campo relacionado: N+1 × resolver otimizado
sem otimização (1 consulta por categoria)    →    955 bytes | 21 consultas
com select_related guiado pela seleção       →    955 bytes | 1 consultas

--- 3) consulta aninhada em profundidade
5 produtos → categoria → produtos → categoria → …   →   1384 bytes | 21 consultas
limite de profundidade 4 → RECUSADA: profundidade 6 > limite 4 | aceita (profundidade 3)
```
(O código acima foi extraído desta própria página e executado sem alterações; a saída é a mostrada.) Leitura:
- **Over-fetching:** a mesma necessidade custou **5.619 bytes** no REST e **714** no GraphQL (~8× menos), numa só consulta ao banco.
- **N+1 de volta:** pedir `category` fez **21 consultas** sem cuidado (1 + 20), e **1** quando o resolver olha a seleção e faz `select_related` só se a categoria foi pedida. É a lição da aula 5.07 reaparecendo: o GraphQL **não elimina** o N+1, só muda o lugar onde ele vive (por isso existem *dataloaders*).
- **Profundidade:** a consulta circular produziu 21 consultas e 1.384 bytes; poderia crescer exponencialmente. Um **limite de profundidade** (e de complexidade, e *timeouts*) é obrigatório em produção. Em projetos Django use bibliotecas maduras como Strawberry ou Graphene-Django, que trazem *dataloaders*, extensões de limite e integração com o ORM; o exemplo usa `graphql-core` puro para mostrar o mecanismo.
- Note que o GraphQL devolveu o preço como `"701.20"`, **string decimal**, a mesma convenção do REST (aula 02): o formato dos dados é uma decisão sua, em qualquer estilo de API.

**2. gRPC na prática (executado: servidor e cliente locais)**
```bash
uv add grpcio grpcio-tools
```
```protobuf
// grpc_demo/catalog.proto
syntax = "proto3";
package minishop;

message Product {
  int32  id    = 1;
  string sku   = 2;
  string name  = 3;
  string price = 4;   // decimal como string (igual ao REST)
  int32  stock = 5;
}

message GetProductRequest  { int32 id = 1; }
message ListProductsRequest { int32 limit = 1; }

service Catalog {
  rpc GetProduct   (GetProductRequest)   returns (Product);
  rpc ListProducts (ListProductsRequest) returns (stream Product);   // streaming do servidor
}
```
```bash
cd grpc_demo && uv run python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. catalog.proto
ls
```
```text
catalog.proto
catalog_pb2.py
catalog_pb2_grpc.py
```
```python
# grpc_run.py (servidor e cliente no mesmo processo, só para a demonstração)
import json, sys
from concurrent import futures
sys.path.insert(0, "grpc_demo")
import grpc
import catalog_pb2 as pb
import catalog_pb2_grpc as rpc
from apps.catalog.models import Product


def para_msg(p):
    return pb.Product(id=p.pk, sku=p.sku, name=p.name, price=str(p.price), stock=p.stock)


class Catalog(rpc.CatalogServicer):
    def GetProduct(self, request, context):
        p = Product.objects.filter(pk=request.id, is_active=True).first()
        if p is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "produto não encontrado")
        return para_msg(p)

    def ListProducts(self, request, context):
        for p in Product.objects.filter(is_active=True).order_by("name")[: request.limit or 5]:
            yield para_msg(p)


servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
rpc.add_CatalogServicer_to_server(Catalog(), servidor)
porta = servidor.add_insecure_port("127.0.0.1:0")
servidor.start()

with grpc.insecure_channel(f"127.0.0.1:{porta}") as canal:
    cli = rpc.CatalogStub(canal)
    p = cli.GetProduct(pb.GetProductRequest(id=2))
    print("GetProduct(2) →", p.sku, p.name, p.price)
    try:
        cli.GetProduct(pb.GetProductRequest(id=9999))
    except grpc.RpcError as e:
        print("GetProduct(9999) →", e.code().name, "|", e.details())
    itens = list(cli.ListProducts(pb.ListProductsRequest(limit=3)))
    print("ListProducts(3) (stream) →", [i.sku for i in itens])

    binario = p.SerializeToString()
    como_json = json.dumps({"id": p.id, "sku": p.sku, "name": p.name, "price": p.price, "stock": p.stock}, separators=(",", ":")).encode()
    print(f"\nmesmo produto: protobuf = {len(binario)} bytes | JSON = {len(como_json)} bytes")
    print("bytes do protobuf:", binario.hex(" "))
servidor.stop(0)
```
```text
GetProduct(2) → INF-002 Notebook Plus 57.30
GetProduct(9999) → NOT_FOUND | produto não encontrado
ListProducts(3) (stream) → ['CAS-049', 'CAS-052', 'CAS-050']

mesmo produto: protobuf = 35 bytes | JSON = 74 bytes
bytes do protobuf: 08 02 12 07 49 4e 46 2d 30 30 32 1a 0d 4e 6f 74 65 62 6f 6f 6b 20 50 6c 75 73 22 05 35 37 2e 33 30 28 13
```
O que se vê: o **contrato** (`.proto`) gerou os arquivos de cliente e servidor; os erros usam **códigos gRPC** (`NOT_FOUND`, equivalentes aproximados dos status HTTP); `ListProducts` devolve um **fluxo** de mensagens; e o mesmo produto ocupa **35 bytes** em Protocol Buffers contra **74** em JSON. Olhe os bytes: `08 02` é “campo 1 (id), valor 2”; `12 07 49 4e 46…` é “campo 2 (sku), 7 bytes de texto `INF-002`”. Os **nomes dos campos não trafegam**, só seus números, e é por isso que o binário é menor (e por que mudar números de campo quebra a compatibilidade).

**3. Fechamento: `Idempotency-Key` no `POST /orders/`**
```python
# apps/orders/models.py
class IdempotencyKey(models.Model):
    """Guarda a resposta de um POST já processado, para que repetir a MESMA chave devolva o MESMO resultado."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    key = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField()
    response_body = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "key"], name="idempotency_user_key_unique")]
```
```python
# apps/orders/api.py (OrderViewSet)
def create(self, request, *args, **kwargs):
    chave = request.headers.get("Idempotency-Key", "").strip()
    if not chave:
        return self._criar(request)
    if len(chave) > 64:
        raise ValidationError({"detail": "Idempotency-Key deve ter até 64 caracteres."})
    anterior = IdempotencyKey.objects.filter(user=request.user, key=chave).first()
    if anterior:                                                       # repetição: devolve o resultado guardado
        return Response(anterior.response_body, status=anterior.response_status, headers={"Idempotent-Replayed": "true"})
    try:
        with transaction.atomic():                                     # pedido + registro da chave: tudo ou nada
            resposta = self._criar(request)
            IdempotencyKey.objects.create(user=request.user, key=chave, response_status=resposta.status_code,
                                          response_body=resposta.data)
        return resposta
    except IntegrityError:                                             # outra requisição com a mesma chave ganhou a corrida
        anterior = IdempotencyKey.objects.get(user=request.user, key=chave)
        return Response(anterior.response_body, status=anterior.response_status, headers={"Idempotent-Replayed": "true"})

def _criar(self, request):
    order = services.create_order(request.user)
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED, headers={"Location": f"/api/v1/orders/{order.pk}/"})
```
```bash
uv run python manage.py makemigrations orders -n idempotency_key
uv run python manage.py migrate
```
```text
Migrations for 'orders':
  apps/orders/migrations/0002_idempotency_key.py
    + Create model IdempotencyKey
```
Pontos de desenho: (1) **na mesma transação** do pedido, de modo que ou o pedido e a chave existem, ou nenhum; (2) uma **falha** (carrinho vazio, sem estoque) faz `rollback` e **não** guarda a chave, então o cliente pode tentar de novo com a mesma chave depois de corrigir o problema; (3) a chave é **por usuário** (`unique(user, key)`); (4) a **corrida** entre duas requisições simultâneas com a mesma chave é resolvida pela restrição `UNIQUE` do banco (a perdedora recebe `IntegrityError` e devolve o registro da vencedora). No SQLite, os pedidos são serializados pelo próprio banco; a corrida de verdade só se comprova em PostgreSQL (aula 5.17). Documente o cabeçalho no OpenAPI com `OpenApiParameter` (aula 10).

**4. Testes da idempotência (executados)**
```python
# tests/test_idempotencia.py
import pytest

from apps.catalog.models import Product
from apps.orders.models import IdempotencyKey, Order

pytestmark = pytest.mark.django_db


@pytest.fixture
def cli(api_as):
    c = api_as("cliente")
    c.post("/api/v1/cart/items/", {"product": 2, "quantity": 2}, format="json")
    return c


def pedir(c, chave=None):
    extra = {"HTTP_IDEMPOTENCY_KEY": chave} if chave else {}
    return c.post("/api/v1/orders/", **extra)


def test_mesma_chave_devolve_o_mesmo_pedido_sem_duplicar(cli):
    estoque = Product.objects.get(pk=2).stock
    r1 = pedir(cli, "k-123")
    r2 = pedir(cli, "k-123")
    assert r1.status_code == r2.status_code == 201
    assert r1.json() == r2.json() and r2["Idempotent-Replayed"] == "true" and "Idempotent-Replayed" not in r1
    assert Order.objects.count() == 1 and Product.objects.get(pk=2).stock == estoque - 2     # baixou UMA vez


def test_sem_chave_o_segundo_post_falha_por_carrinho_vazio(cli):
    assert pedir(cli).status_code == 201
    assert pedir(cli).status_code == 422


def test_chave_nova_com_carrinho_vazio_nao_reaproveita_resposta(cli):
    pedir(cli, "k-1")
    assert pedir(cli, "k-2").status_code == 422


def test_falha_nao_grava_a_chave_e_pode_ser_repetida(api_as):
    c = api_as("cliente")
    assert pedir(c, "k-9").status_code == 422                               # carrinho vazio
    assert IdempotencyKey.objects.count() == 0
    c.post("/api/v1/cart/items/", {"product": 2, "quantity": 1}, format="json")
    assert pedir(c, "k-9").status_code == 201                               # mesma chave, agora com sucesso


def test_chave_e_por_usuario(api_as):
    a, b = api_as("cliente"), api_as("gerente")
    for c in (a, b):
        c.post("/api/v1/cart/items/", {"product": 2, "quantity": 1}, format="json")
    assert pedir(a, "mesma").json()["id"] != pedir(b, "mesma").json()["id"]
    assert Order.objects.count() == 2


def test_chave_muito_longa_e_rejeitada(cli):
    assert pedir(cli, "x" * 65).status_code == 400
```
```bash
uv run pytest -q tests/test_idempotencia.py
```
```text
6 passed
```
Quando adicionei o novo cabeçalho à view e rodei a suíte inteira, **o teste do schema commitado falhou** (`test_schema_commitado_esta_em_dia`, aula 10): a documentação mudou e o `schema.yml` não. É o teste fazendo o trabalho dele; a correção é conscientemente regenerar o contrato:
```bash
uv run python manage.py spectacular --file schema.yml --validate --fail-on-warn
```

**5. Auditoria de fechamento da API (executado)**
```bash
uv run pytest --cov=apps -q tests
uv run python cobertura_de_rotas.py | head -3
uv run python manage.py check
uv run python manage.py spectacular --validate --fail-on-warn > /dev/null; echo "spectacular exit=$?"
uv run python manage.py makemigrations --check --dry-run | tail -1
```
```text
TOTAL                                                         560     39    93%
64 passed, 50 warnings in 26.55s
20/20 operações do contrato aparecem em algum teste
todas cobertas
System check identified no issues (0 silenced).
spectacular exit=0
No changes detected
```
Os cinco “sinais verdes” de entrega da API: **testes**, **cobertura de rotas do contrato**, **`check`**, **schema válido e sem avisos** e **migrações em dia**. Coloque os cinco na CI (módulo 12).

**6. A API do MiniShop v1: o que existe agora**
| Aula | O que a API ganhou |
|---|---|
| 01–02 | princípios REST, contrato e convenções (`/api/v1/`, plural, kebab-case, dinheiro como string) |
| 03–04 | serializers e viewsets/router: produtos, categorias, carrinho, pedidos, `cancel` |
| 05 | erros padronizados (`{campo: [...]}` e `{detail, code}`), 422 de regra de negócio |
| 06 | JWT com refresh rotativo e logout |
| 07 | permissões “negar por padrão”, papéis por grupo, `IsOwner` |
| 08–09 | filtros, busca, ordenação, paginação (página e cursor), throttling |
| 10 | OpenAPI/Swagger gerado, versionamento por caminho |
| 11 | CORS por origem explícita |
| 12 | suíte de testes (jornada, contrato, rotas, 93%) |
| 13 | `Idempotency-Key` no pedido; comparação com GraphQL e gRPC |

## 🧠 Pausa para lógica
**Problema (chave de idempotência com TTL).** Implemente `ArmazemDeChaves.executar(usuario, chave, corpo, acao)` com: (1) a mesma chave e o mesmo corpo devolvem o resultado guardado, marcando `replayed`; (2) a mesma chave com **corpo diferente** devolve `422` (`idempotency_key_reuse`); (3) apenas **sucessos** (< 400) são guardados; (4) registros **expiram** após um TTL; (5) a chave é por usuário. Use um relógio injetável para testar.

<details><summary>Dica</summary>
Guarde, por <code>(usuario, chave)</code>, o hash do corpo (<code>sha256(json.dumps(corpo, sort_keys=True))</code>), a resposta e o instante. Ao consultar, descarte o registro se <code>agora - em &gt; ttl</code>.
</details>

<details><summary>Solução comentada</summary>

```python
import hashlib
import json


class ArmazemDeChaves:
    """Chave de idempotência com TTL e detecção de reuso com corpo diferente."""

    def __init__(self, ttl=24 * 3600, relogio=None):
        self.ttl, self.relogio, self.dados = ttl, relogio, {}

    @staticmethod
    def _hash(corpo):
        return hashlib.sha256(json.dumps(corpo, sort_keys=True).encode()).hexdigest()

    def executar(self, usuario, chave, corpo, acao):
        agora = self.relogio()
        registro = self.dados.get((usuario, chave))
        if registro and agora - registro["em"] > self.ttl:
            registro = None                                        # expirou: trata como chave nova
        if registro:
            if registro["hash"] != self._hash(corpo):
                return 422, {"code": "idempotency_key_reuse", "detail": "Esta chave já foi usada com outro conteúdo."}
            return registro["status"], registro["resposta"] | {"replayed": True}
        status, resposta = acao(corpo)
        if status < 400:                                           # só guarda sucesso: falha pode ser repetida
            self.dados[(usuario, chave)] = {"hash": self._hash(corpo), "status": status, "resposta": resposta, "em": agora}
        return status, resposta


t = [0]
armazem = ArmazemDeChaves(ttl=100, relogio=lambda: t[0])
criados = []


def criar(corpo):
    if corpo.get("qtd", 1) <= 0:
        return 400, {"detail": "quantidade inválida"}
    criados.append(corpo)
    return 201, {"id": len(criados), **corpo}


print(armazem.executar("ana", "k1", {"sku": "A", "qtd": 2}, criar))
print(armazem.executar("ana", "k1", {"sku": "A", "qtd": 2}, criar), "← repetição")
print(armazem.executar("ana", "k1", {"sku": "A", "qtd": 9}, criar), "← mesma chave, outro corpo")
print(armazem.executar("bia", "k1", {"sku": "A", "qtd": 2}, criar)[1]["id"], "← outro usuário, mesma chave: pedido novo")
print(armazem.executar("ana", "k2", {"sku": "A", "qtd": 0}, criar), "← falha não é guardada")
print(armazem.executar("ana", "k2", {"sku": "A", "qtd": 1}, criar), "← mesma chave, agora válida")
t[0] = 500
print(armazem.executar("ana", "k1", {"sku": "A", "qtd": 2}, criar), "← depois do TTL: nova execução")
print("pedidos criados:", len(criados))
```
```text
(201, {'id': 1, 'sku': 'A', 'qtd': 2})
(201, {'id': 1, 'sku': 'A', 'qtd': 2, 'replayed': True}) ← repetição
(422, {'code': 'idempotency_key_reuse', 'detail': 'Esta chave já foi usada com outro conteúdo.'}) ← mesma chave, outro corpo
2 ← outro usuário, mesma chave: pedido novo
(400, {'detail': 'quantidade inválida'}) ← falha não é guardada
(201, {'id': 3, 'sku': 'A', 'qtd': 1}) ← mesma chave, agora válida
(201, {'id': 4, 'sku': 'A', 'qtd': 2}) ← depois do TTL: nova execução
pedidos criados: 4
```
(Executado em 2026-11-08.) No `POST /orders/` do MiniShop o corpo é vazio (o pedido sai do carrinho); a verificação de “corpo diferente” passa a importar em endpoints com corpo, como um pagamento.
</details>

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| Pedido duplicado após *timeout* e retry do app | `POST` sem chave de idempotência | `Idempotency-Key` + registro na mesma transação |
| Replay devolve outro corpo | Registro gravado fora da transação do pedido | Pedido e chave no mesmo `atomic` |
| Retry com a mesma chave nunca funciona após um erro | Falha foi guardada | Guardar só sucessos |
| Chaves acumulam para sempre | Sem expiração | TTL (24 h) e limpeza periódica (tarefa agendada, módulo 7) |
| GraphQL: 21 consultas para 20 itens | N+1 nos resolvers | Olhar a seleção, `select_related`/*dataloader* |
| GraphQL: consulta gigante derruba o servidor | Sem limite de profundidade/complexidade | Limites, *timeouts*, listas permitidas de consultas |
| GraphQL: todo erro é `200` | Convenção do protocolo | Monitorar a lista `errors`, não só o status |
| gRPC no navegador não funciona | HTTP/2 + binário | *gRPC-web* com proxy ou usar REST |
| Mudou o número de um campo no `.proto` e quebrou clientes | O número é a identidade do campo | Nunca reutilizar/alterar números; só acrescentar |
| `test_schema_commitado_esta_em_dia` falhou | Mudou o contrato sem regenerar | `manage.py spectacular --file schema.yml` e revisar o diff |

- **Escolha a ferramenta pelo problema**, não pela moda: REST para a API pública do MiniShop, gRPC entre serviços internos se um dia houver, GraphQL se os clientes divergirem muito.
- Quem usa GraphQL precisa **repensar** autorização, cache, N+1 e observabilidade: nada disso vem de graça.
- Toda operação que **cria algo caro ou cobra dinheiro** merece idempotência.
- Mantenha **uma** fonte de verdade para as regras (os serviços): REST, GraphQL e gRPC seriam só “portas de entrada”.

## 🧩 Exercícios
**1. Fixação**
(a) Qual problema o GraphQL resolve em relação ao REST e que problema ele reintroduz? (b) Por que o gRPC é menor e mais rápido que JSON sobre HTTP? (c) Por que a falha não grava a chave de idempotência? (d) Por que a chave é por usuário?

<details><summary>Solução</summary>

(a) Resolve *over/under-fetching* (o cliente pede os campos); reintroduz o N+1 nos resolvers, consultas profundas/caras e dificulta cache. (b) Protocol Buffers é binário e envia números de campo em vez de nomes; HTTP/2 multiplexa e permite *streaming*. (c) Para o cliente poder repetir a mesma operação depois de corrigir o problema (sem estoque, carrinho vazio) sem ser preso a uma resposta de erro antiga. (d) Para que usuários diferentes não colidam nem leiam respostas uns dos outros.
</details>

**2. Aplicação no projeto MiniShop** *(fecha a API)*
Entregue a **API REST do MiniShop v1**.

Critérios de pronto:
- [ ] `Idempotency-Key` no `POST /orders/` com migração, documentada no OpenAPI, e testes (repetição, falha, outro usuário, chave longa)
- [ ] Tarefa/comando `purge_idempotency_keys` que apaga chaves com mais de 24 h (e teste)
- [ ] Os cinco sinais verdes: testes, cobertura de rotas 100% do contrato, `check`, `spectacular --validate --fail-on-warn` e `makemigrations --check`
- [ ] `docs/api-contrato.md` atualizado com todas as rotas, erros (`code`), papéis, taxas e a política de idempotência
- [ ] `docs/rest-graphql-grpc.md` (1 página): por que REST para o MiniShop e quando mudaria de ideia
- [ ] Coleção de chamadas (Bruno, aula 2.04, ou `curl`) com um exemplo por operação
- [ ] Commit `feat(api): idempotency key and API v1 closing checks`

<details><summary>Solução de referência (purge)</summary>

```python
# apps/orders/management/commands/purge_idempotency_keys.py
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import IdempotencyKey


class Command(BaseCommand):
    help = "Apaga chaves de idempotência com mais de 24 horas."

    def handle(self, *args, **opts):
        limite = timezone.now() - timedelta(hours=24)
        apagadas, _ = IdempotencyKey.objects.filter(created_at__lt=limite).delete()
        self.stdout.write(f"{apagadas} chave(s) apagada(s)")
```
```python
def test_purge_apaga_so_as_antigas(seed, django_user_model):
    from datetime import timedelta
    from django.core.management import call_command
    from django.utils import timezone
    u = django_user_model.objects.get(username="cliente")
    velha = IdempotencyKey.objects.create(user=u, key="v", response_status=201, response_body={})
    nova = IdempotencyKey.objects.create(user=u, key="n", response_status=201, response_body={})
    IdempotencyKey.objects.filter(pk=velha.pk).update(created_at=timezone.now() - timedelta(hours=25))
    call_command("purge_idempotency_keys")
    assert list(IdempotencyKey.objects.values_list("key", flat=True)) == ["n"]
```
</details>

**3. Desafio (opcional)**
Exponha `GET /graphql/` com o schema do exemplo usando Strawberry (ou Graphene-Django) integrado ao Django, com **autenticação JWT**, limite de profundidade e *dataloader* para a categoria. Compare, com `CaptureQueriesContext`, o número de consultas e o tamanho das respostas com os do REST para a mesma tela.

## 🎤 Na entrevista
- **REST, GraphQL ou gRPC?** REST para APIs públicas e CRUD (simples, cacheável, ecossistema); GraphQL quando vários clientes precisam de formatos diferentes e queremos evitar over/under-fetching (pagando em complexidade de servidor); gRPC para comunicação interna entre serviços, com contrato forte, binário e *streaming*.
- **Que problemas o GraphQL traz?** N+1 nos resolvers, consultas profundas/caras (limites de profundidade e complexidade), autorização por campo, cache mais difícil e erros com status `200`.
- **O que é um `.proto` e por que o gRPC é compacto?** É o contrato (mensagens e serviços) a partir do qual se gera código; a serialização é binária e identifica campos por número, não por nome.
- **Como evitar cobrar duas vezes num `POST` repetido?** Chave de idempotência enviada pelo cliente; o servidor guarda `(usuário, chave) → resposta` na mesma transação e devolve o resultado guardado na repetição, sem executar de novo.

## 📚 Para ir além
- 📄 Documentação: [GraphQL — Learn](https://graphql.org/learn/). Conceitos de schema, queries e resolvers.
- 📄 Documentação: [graphql-core](https://graphql-core-3.readthedocs.io/). A implementação de referência em Python usada no exemplo.
- 📄 Documentação: [Strawberry GraphQL](https://strawberry.rocks/). GraphQL em Python com integração ao Django.
- 📄 Documentação: [gRPC — Introdução](https://grpc.io/docs/what-is-grpc/introduction/). Contratos, HTTP/2 e os quatro modos de RPC.
- 📄 Documentação: [gRPC — Python, tutorial básico](https://grpc.io/docs/languages/python/basics/). O passo a passo do `.proto` ao cliente.
- 📄 Documentação: [Protocol Buffers — Visão geral](https://protobuf.dev/overview/). Como o formato binário funciona e boas práticas de evolução.
- 📑 Artigo/tutorial: [Stripe — Requisições idempotentes](https://docs.stripe.com/api/idempotent_requests). O padrão `Idempotency-Key` em produção (em inglês).
- 🏋️ Prática extra: gere um cliente gRPC em outra linguagem a partir do mesmo `catalog.proto`.

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Sei comparar REST, GraphQL e gRPC e escolher para o MiniShop
- [ ] Vi o over-fetching, o N+1 e o limite de profundidade no GraphQL
- [ ] Vi um `.proto`, uma chamada gRPC real e o tamanho do binário
- [ ] `Idempotency-Key` implementada, testada e documentada
- [ ] Os cinco sinais verdes de entrega da API conferidos
