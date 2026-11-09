def ordenar(itens, ordering, permitidos):
    """'-price,name' -> ordena por preço desc e, em empate, por nome asc. Rejeita campos fora da lista."""
    chaves = []
    for parte in filter(None, (p.strip() for p in ordering.split(","))):
        campo, desc = (parte[1:], True) if parte.startswith("-") else (parte, False)
        if campo not in permitidos:
            raise ValueError(f"ordenação por '{campo}' não permitida (use: {', '.join(sorted(permitidos))})")
        chaves.append((campo, desc))
    resultado = list(itens)
    for campo, desc in reversed(chaves):            # sort estável: aplica a chave menos importante primeiro
        resultado.sort(key=lambda i: i[campo], reverse=desc)
    return resultado


produtos = [{"name": "Mouse", "price": 59.9}, {"name": "Teclado", "price": 120.5}, {"name": "Cabo", "price": 59.9}, {"name": "Hub", "price": 120.5}]
for o in ["name", "-price,name", "price,-name"]:
    print(f"{o:<12}", [p["name"] for p in ordenar(produtos, o, {"price", "name"})])
try:
    ordenar(produtos, "password", {"price", "name"})
except ValueError as e:
    print("erro:", e)
