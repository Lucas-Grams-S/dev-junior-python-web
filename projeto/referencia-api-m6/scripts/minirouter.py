ROTAS_PADRAO = {                       # método do viewset -> (verbo HTTP, tem id?)
    "list": ("GET", False), "create": ("POST", False),
    "retrieve": ("GET", True), "update": ("PUT", True), "partial_update": ("PATCH", True), "destroy": ("DELETE", True),
}


def gerar_rotas(prefixo, viewset):
    rotas = []
    for acao, (verbo, com_id) in ROTAS_PADRAO.items():
        if hasattr(viewset, acao):
            rotas.append((verbo, f"/{prefixo}/{{id}}/" if com_id else f"/{prefixo}/", acao))
    for nome in dir(viewset):                                   # ações extras marcadas
        f = getattr(viewset, nome)
        if getattr(f, "_acao", None):
            detalhe, verbo = f._acao
            rotas.append((verbo, f"/{prefixo}/{{id}}/{nome}/" if detalhe else f"/{prefixo}/{nome}/", nome))
    return rotas


def acao(detalhe, verbo):
    def deco(f):
        f._acao = (detalhe, verbo)
        return f
    return deco


class PedidoViewSet:
    def list(self): ...
    def create(self): ...
    def retrieve(self): ...

    @acao(True, "POST")
    def cancel(self): ...


class CategoriaViewSet:
    def list(self): ...
    def retrieve(self): ...


for prefixo, vs in [("orders", PedidoViewSet), ("categories", CategoriaViewSet)]:
    for verbo, url, nome in gerar_rotas(prefixo, vs):
        print(f"{verbo:<6} {url:<22} → {vs.__name__}.{nome}")
