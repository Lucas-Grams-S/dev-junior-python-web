"""Comportamento que o golden master NÃO deve preservar: entrada maliciosa no SKU."""

import pytest
from django.db import connection

from apps.catalog.models import Product
from legado import pedidos_legado

pytestmark = [pytest.mark.django_db, pytest.mark.skipif(connection.vendor != "sqlite", reason="legado usa SQL específico do SQLite")]


@pytest.fixture
def mundo(criar_produto, criar_usuario):
    criar_produto(sku="A-100", preco="100.00", estoque=10)
    return criar_usuario("x")


@pytest.mark.parametrize("sku", ["' or '1'='1", "A-100' or '1'='1", "O'Brien"])
def test_sku_estranho_e_tratado_como_texto(mundo, sku):
    r = pedidos_legado.processar_pedido({"user_id": mundo.pk, "itens": [{"sku": sku, "qtd": 1}], "cupom": None, "forma_pgto": "cartao"})
    assert r["ok"] is False and "nao existe" in r["erro"]
    assert Product.objects.get(sku="A-100").stock == 10  # nada foi vendido
