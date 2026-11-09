# -*- coding: utf-8 -*-
# "Código herdado" do MiniShop v0: funciona, ninguém tem coragem de mexer. (Escrito de propósito para a aula 8.07.)
from django.db import connection

TOTAL_PEDIDOS = 0          # contador global "para o relatório"
LOG = []


def processar_pedido(dados):
    global TOTAL_PEDIDOS
    c = connection.cursor()
    itens = dados["itens"]
    if len(itens) == 0:
        return {"ok": False, "erro": "sem itens"}
    total = 0
    linhas = []
    for i in itens:
        c.execute("select id, price, stock, is_active from catalog_product where sku = '" + i["sku"] + "'")
        p = c.fetchone()
        if p is None:
            return {"ok": False, "erro": "produto " + i["sku"] + " nao existe"}
        else:
            if p[3] == 0:
                return {"ok": False, "erro": "produto " + i["sku"] + " inativo"}
            else:
                if p[2] < i["qtd"]:
                    return {"ok": False, "erro": "sem estoque " + i["sku"]}
                else:
                    sub = float(p[1]) * i["qtd"]
                    total = total + sub
                    linhas.append((p[0], i["qtd"], float(p[1])))
    desc = 0
    if dados.get("cupom"):
        if dados["cupom"] == "PROMO10":
            desc = total * 0.10
        elif dados["cupom"] == "PROMO20":
            if total > 500:
                desc = total * 0.20
            else:
                desc = total * 0.10
        elif dados["cupom"] == "FRETEGRATIS":
            desc = 0
        else:
            return {"ok": False, "erro": "cupom invalido"}
    if dados.get("forma_pgto") == "pix":
        desc = desc + total * 0.05
    elif dados.get("forma_pgto") == "cartao":
        desc = desc + 0
    elif dados.get("forma_pgto") == "boleto":
        desc = desc - 2.5
    else:
        return {"ok": False, "erro": "forma de pagamento invalida"}
    frete = 0
    if total - desc < 200:
        frete = 19.9
    if dados.get("cupom") == "FRETEGRATIS":
        frete = 0
    final = total - desc + frete
    final = round(final, 2)
    c.execute("insert into orders_order (user_id, status, total, created_at) values (%s, 'pending', %s, datetime('now'))", [dados["user_id"], str(final)])
    oid = c.lastrowid
    for l in linhas:
        c.execute("insert into orders_orderitem (order_id, product_id, quantity, unit_price) values (%s, %s, %s, %s)", [oid, l[0], l[1], str(l[2])])
        c.execute("update catalog_product set stock = stock - %s where id = %s", [l[1], l[0]])
    TOTAL_PEDIDOS = TOTAL_PEDIDOS + 1
    LOG.append("pedido " + str(oid) + " total " + str(final))
    print("pedido criado", oid)
    return {"ok": True, "pedido_id": oid, "total": final, "frete": frete, "desconto": round(desc, 2)}
