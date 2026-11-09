"""Custo de testar a MESMA regra com o repositório em memória e com o banco (SQLite aqui; PostgreSQL seria mais lento ainda)."""
import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.cart import services as carrinho
from apps.catalog.models import Product
from apps.orders import services
from apps.orders.domain import ItemCarrinho, ProdutoInfo
from apps.orders.repositories import MemoriaPedidoRepository

N = 500
t = time.perf_counter()
for _ in range(N):
    r = MemoriaPedidoRepository(carrinhos={"ana": [ItemCarrinho(1, 2)]}, produtos={1: ProdutoInfo(1, "Mouse", Decimal("59.90"), 5, True)})
    services.create_order("ana", r)
memoria = (time.perf_counter() - t) / N

user = get_user_model().objects.get(username="cliente")
p = Product.objects.get(sku="INF-002")
M = 100
total = 0.0
with transaction.atomic():
    Product.objects.filter(pk=p.pk).update(stock=10_000)             # estoque de sobra (também será desfeito)
    for _ in range(M):
        carrinho.add_item(user, p.pk, 1)
        t = time.perf_counter()
        pedido = services.create_order(user)                          # a MESMA função, agora com o ORM
        total += time.perf_counter() - t
    transaction.set_rollback(True)                                    # não deixa rastro no banco
banco = total / M
print(f"create_order com repositório EM MEMÓRIA: {memoria * 1e6:8.0f} µs por chamada ({N} chamadas)")
print(f"create_order com o ORM (SQLite)        : {banco * 1e6:8.0f} µs por chamada ({M} chamadas, sem contar a preparação)")
print(f"→ a versão em memória é ≈ {banco / memoria:,.0f}× mais rápida (e não precisa de banco, migrações nem fixtures)")
