"""Um verificador de camadas em 25 linhas: dado quem importa quem e a ordem das camadas (de cima para baixo), aponta as violações."""


def violacoes(arestas, camadas):
    """arestas: lista de (origem, destino); camadas: ['interface', 'servicos', 'dados'] (de cima para baixo).
    Regra: uma camada só pode depender das que estão ABAIXO dela."""
    nivel = {c: i for i, c in enumerate(camadas)}
    ruins = []
    for origem, destino in arestas:
        co, cd = origem.split(".")[0], destino.split(".")[0]
        if co in nivel and cd in nivel and nivel[cd] < nivel[co]:
            ruins.append((origem, destino, f"'{co}' (nível {nivel[co]}) não pode depender de '{cd}' (nível {nivel[cd]}, acima)"))
    return ruins


def ciclos(arestas):
    """Dependência circular entre módulos/apps: A → B → A (busca em profundidade)."""
    grafo = {}
    for a, b in arestas:
        grafo.setdefault(a, set()).add(b)
    achados = set()

    def visita(no, caminho):
        for vizinho in grafo.get(no, ()):
            if vizinho in caminho:
                ciclo = caminho[caminho.index(vizinho):] + [vizinho]
                achados.add(tuple(ciclo))
            else:
                visita(vizinho, caminho + [vizinho])

    for no in grafo:
        visita(no, [no])
    return achados


arestas = [("interface.pedidos", "servicos.pedidos"), ("servicos.pedidos", "dados.pedido"), ("interface.pedidos", "dados.pedido"),
           ("dados.pedido", "servicos.pedidos"),                        # ERRO: o modelo conhece o serviço
           ("servicos.pedidos", "interface.serializers")]              # ERRO: o serviço conhece a interface
for o, d, motivo in violacoes(arestas, ["interface", "servicos", "dados"]):
    print(f"✘ {o} → {d}: {motivo}")

apps = [("orders", "payments"), ("payments", "orders"), ("realtime", "orders"), ("orders", "cart"), ("cart", "catalog")]
print("ciclos entre apps:", [" → ".join(c) for c in sorted(ciclos(apps))])
print("depois de mover o 'pagar' para payments:", [" → ".join(c) for c in sorted(ciclos([a for a in apps if a != ("orders", "payments")]))] or "nenhum ciclo")
