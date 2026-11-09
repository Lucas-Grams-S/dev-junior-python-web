# PASSO 3: regras de preço movidas para `precificacao` (puras e testáveis sem banco). Aqui sobrou só orquestração e I/O.
from django.db import connection

from .precificacao import PedidoInvalido, precificar

TOTAL_PEDIDOS = 0  # contador global "para o relatório" (próximo passo: tirar do módulo)
LOG: list[str] = []


def _ler_linhas(c, itens):
    """Valida cada item contra o banco; devolve (linhas, total)."""
    total = 0
    linhas = []
    for i in itens:
        c.execute("select id, price, stock, is_active from catalog_product where sku = %s", [i["sku"]])
        p = c.fetchone()
        if p is None:
            raise PedidoInvalido("produto " + i["sku"] + " nao existe")
        if p[3] == 0:
            raise PedidoInvalido("produto " + i["sku"] + " inativo")
        if p[2] < i["qtd"]:
            raise PedidoInvalido("sem estoque " + i["sku"])
        total = total + float(p[1]) * i["qtd"]
        linhas.append((p[0], i["qtd"], float(p[1])))
    return linhas, total


def _gravar(c, user_id, linhas, final):
    c.execute(
        "insert into orders_order (user_id, status, total, created_at) values (%s, 'pending', %s, datetime('now'))", [user_id, str(final)]
    )
    oid = c.lastrowid
    for produto_id, qtd, preco in linhas:
        c.execute(
            "insert into orders_orderitem (order_id, product_id, quantity, unit_price) values (%s, %s, %s, %s)",
            [oid, produto_id, qtd, str(preco)],
        )
        c.execute("update catalog_product set stock = stock - %s where id = %s", [qtd, produto_id])
    return oid


def processar_pedido(dados):
    global TOTAL_PEDIDOS
    c = connection.cursor()
    if len(dados["itens"]) == 0:
        return {"ok": False, "erro": "sem itens"}
    try:
        linhas, total = _ler_linhas(c, dados["itens"])
        desc, frete, final = precificar(total, dados.get("cupom"), dados.get("forma_pgto"))
    except PedidoInvalido as e:
        return {"ok": False, "erro": str(e)}
    oid = _gravar(c, dados["user_id"], linhas, final)
    TOTAL_PEDIDOS = TOTAL_PEDIDOS + 1
    LOG.append("pedido " + str(oid) + " total " + str(final))
    print("pedido criado", oid)
    return {"ok": True, "pedido_id": oid, "total": final, "frete": frete, "desconto": round(desc, 2)}
