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

def resolve_category_products(categoria, info, first=3):
    return list(categoria.products.filter(is_active=True)[:first])

OTIMIZAR = {"v": True}
root = {"products": lambda info, **kw: resolve_products(info, otimizar=OTIMIZAR["v"], **kw),
        "product": lambda info, id: Product.objects.filter(pk=id).first()}
Category.products_gql = resolve_category_products                 # resolver do campo aninhado Category.products
schema.type_map["Category"].fields["products"].resolve = lambda cat, info, **kw: resolve_category_products(cat, info, **kw)
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
OTIMIZAR["v"] = True; rodar(profunda, "5 produtos → categoria → produtos → categoria → …")

def profundidade(no, nivel=0):
    if isinstance(no, ast.FieldNode) and no.selection_set:
        return max(profundidade(s, nivel + 1) for s in no.selection_set.selections)
    if isinstance(no, ast.OperationDefinitionNode):
        return max(profundidade(s, 0) for s in no.selection_set.selections)
    return nivel + (1 if isinstance(no, ast.FieldNode) else 0)

def executar_com_limite(query, limite=4):
    d = max(profundidade(op) for op in parse(query).definitions)
    if d > limite:
        return f"RECUSADA: profundidade {d} > limite {limite}"
    return "aceita (profundidade %d)" % d
print("limite de profundidade 4 →", executar_com_limite(profunda), "|", executar_com_limite("{ products { sku category { name } } }"))
