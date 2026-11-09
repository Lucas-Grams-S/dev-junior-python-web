"""Várias pessoas compram a ÚLTIMA unidade ao mesmo tempo. Só faz sentido em PostgreSQL (SQLite ignora select_for_update)."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connection

from apps.cart import services as carrinho
from apps.catalog.models import Product
from apps.orders import services as pedidos

pytestmark = [
    pytest.mark.django_db(transaction=True, serialized_rollback=True),   # commits reais; restaura content types após o flush
    pytest.mark.skipif(connection.vendor != "postgresql", reason="concorrência real exige PostgreSQL"),
]


def test_oito_compradores_uma_unidade_so_um_vence(seed, django_user_model):
    produto = Product.objects.filter(is_active=True).first()
    Product.objects.filter(pk=produto.pk).update(stock=1)
    usuarios = [django_user_model.objects.create_user(username=f"c{i}", password="x" * 12) for i in range(8)]
    for u in usuarios:
        carrinho.add_item(u, produto.pk, 1)

    def comprar(u):
        try:
            pedidos.create_order(u)
            return "ok"
        except pedidos.StockError:
            return "sem_estoque"
        finally:
            connection.close()                    # cada thread tem a própria conexão

    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = list(pool.map(comprar, usuarios))

    produto.refresh_from_db()
    assert resultados.count("ok") == 1 and resultados.count("sem_estoque") == 7
    assert produto.stock == 0
