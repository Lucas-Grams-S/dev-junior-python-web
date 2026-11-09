import functools


def com_chave_de_idempotencia(funcao):
    """Repetir a MESMA chave devolve o resultado guardado, sem executar de novo."""
    guardado = {}

    @functools.wraps(funcao)
    def interna(chave, *args, **kwargs):
        if chave not in guardado:
            guardado[chave] = funcao(*args, **kwargs)
        return guardado[chave]

    return interna


pedidos = []


@com_chave_de_idempotencia
def criar_pedido(sku, qtd):
    pedidos.append((sku, qtd))
    return {"pedido": len(pedidos), "sku": sku, "qtd": qtd}


print(criar_pedido("k-1", "MOU-1", 2))
print(criar_pedido("k-1", "MOU-1", 2))      # repetição (timeout + retry do cliente): mesmo resultado
print(criar_pedido("k-2", "MOU-1", 2))      # outra intenção do usuário: novo pedido
print("pedidos criados:", len(pedidos))
