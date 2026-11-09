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
