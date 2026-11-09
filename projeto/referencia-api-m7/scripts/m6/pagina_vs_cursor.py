def por_offset(itens, pagina, tamanho):
    ini = (pagina - 1) * tamanho
    return itens[ini:ini + tamanho]


def por_cursor(itens, tamanho, depois_de=None):
    """Itens em ordem decrescente de id. O cursor é o id do último item visto."""
    restantes = [i for i in itens if depois_de is None or i < depois_de]
    pagina = restantes[:tamanho]
    return pagina, (pagina[-1] if pagina else None)


# pedidos 20..1, mais novo primeiro; o cliente lê de 5 em 5
pedidos = list(range(20, 0, -1))

# --- offset: um pedido novo (21) chega entre a leitura da página 1 e da página 2
p1 = por_offset(pedidos, 1, 5)
pedidos = [21] + pedidos
p2 = por_offset(pedidos, 2, 5)
print("OFFSET  p1:", p1, "p2:", p2, "→ repetido:", set(p1) & set(p2))

# --- cursor: mesma situação
pedidos = list(range(20, 0, -1))
c1, cursor = por_cursor(pedidos, 5)
pedidos = [21] + pedidos
c2, _ = por_cursor(pedidos, 5, cursor)
print("CURSOR  p1:", c1, "p2:", c2, "→ repetido:", set(c1) & set(c2) or "nenhum")
