"""Teste de jornada: o fluxo completo do cliente pela API, como o front vai usá-lo."""
from decimal import Decimal

import pytest

from apps.catalog.models import Product

pytestmark = pytest.mark.django_db


def test_jornada_login_busca_carrinho_pedido_e_cancelamento(api_as):
    anon = api_as(None)
    # 1) navegar no catálogo sem login
    r = anon.get("/api/v1/products/", {"search": "mouse", "ordering": "price"})
    assert r.status_code == 200 and r.json()["count"] >= 1
    produto = r.json()["results"][0]
    estoque_inicial = Product.objects.get(pk=produto["id"]).stock

    # 2) login e carrinho
    cli = api_as("cliente")
    r = cli.post("/api/v1/cart/items/", {"product": produto["id"], "quantity": 2}, format="json")
    assert r.status_code == 201 and r["Location"].startswith("/api/v1/cart/items/")
    carrinho = cli.get("/api/v1/cart/").json()
    assert carrinho["count"] == 2 and Decimal(carrinho["total"]) == 2 * Decimal(produto["price"])

    # 3) pedido: estoque baixa, carrinho esvazia, preço congelado
    r = cli.post("/api/v1/orders/")
    assert r.status_code == 201
    pedido = r.json()
    assert pedido["status"] == "pending" and Decimal(pedido["total"]) == Decimal(carrinho["total"])
    assert Product.objects.get(pk=produto["id"]).stock == estoque_inicial - 2
    assert cli.get("/api/v1/cart/").json()["count"] == 0
    assert cli.post("/api/v1/orders/").status_code == 422                          # carrinho vazio

    # 4) cancelamento devolve o estoque, só uma vez
    assert cli.post(f"/api/v1/orders/{pedido['id']}/cancel/").status_code == 200
    assert Product.objects.get(pk=produto["id"]).stock == estoque_inicial
    assert cli.post(f"/api/v1/orders/{pedido['id']}/cancel/").status_code == 422

    # 5) outro usuário não enxerga o pedido
    assert api_as("gerente").get(f"/api/v1/orders/{pedido['id']}/").status_code == 404
