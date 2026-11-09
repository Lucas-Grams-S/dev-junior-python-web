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
