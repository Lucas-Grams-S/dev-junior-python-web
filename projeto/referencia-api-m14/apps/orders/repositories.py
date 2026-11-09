"""Porta (interface) e adaptadores de persistência do pedido. O serviço conversa com a PORTA; quem implementa decide COMO gravar."""

import copy
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol

from django.db import transaction
from django.db.models import F

from apps.cart.models import Cart
from apps.catalog import cache as catalog_cache
from apps.catalog.models import Product

from .domain import ItemCarrinho, LinhaCompra, ProdutoInfo
from .models import Order, OrderItem


class PedidoRepository(Protocol):
    def transacao(self) -> AbstractContextManager: ...
    def travar_carrinho(self, user): ...
    def itens_do_carrinho(self, carrinho) -> list[ItemCarrinho]: ...
    def travar_produtos(self, ids: list[int]) -> dict[int, ProdutoInfo]: ...
    def criar_pedido(self, user, linhas: list[LinhaCompra], total: Decimal): ...
    def baixar_estoque(self, product_id: int, quantidade: int) -> bool: ...
    def esvaziar_carrinho(self, carrinho) -> None: ...


class DjangoPedidoRepository:
    """Implementação real: ORM do Django, com travas (`select_for_update`) e atualização condicional do estoque."""

    def transacao(self):
        return transaction.atomic()

    def travar_carrinho(self, user):
        return Cart.objects.select_for_update().filter(user=user).first()

    def itens_do_carrinho(self, carrinho):
        return [ItemCarrinho(i.product_id, i.quantity) for i in carrinho.items.all()]

    def travar_produtos(self, ids):
        qs = Product.objects.select_for_update().filter(pk__in=ids).order_by("pk")  # SEMPRE na mesma ordem (evita deadlock)
        return {p.pk: ProdutoInfo(p.pk, p.name, p.price, p.stock, p.is_active) for p in qs}

    def criar_pedido(self, user, linhas, total):
        pedido = Order.objects.create(user=user, total=total)
        OrderItem.objects.bulk_create(
            [OrderItem(order=pedido, product_id=linha.product_id, quantity=linha.quantidade, unit_price=linha.preco) for linha in linhas]
        )
        return pedido

    def baixar_estoque(self, product_id, quantidade):
        transaction.on_commit(
            catalog_cache.bump
        )  # `.update()` não dispara signals: o estoque exibido no catálogo precisa ser invalidado à mão
        return Product.objects.filter(pk=product_id, stock__gte=quantidade).update(stock=F("stock") - quantidade) == 1

    def esvaziar_carrinho(self, carrinho):
        carrinho.items.all().delete()


@dataclass
class PedidoMemoria:
    id: int
    total: Decimal
    linhas: list = field(default_factory=list)


class MemoriaPedidoRepository:
    """Implementação em MEMÓRIA, para testar as regras do serviço sem banco (rápida e determinística)."""

    def __init__(self, carrinhos=None, produtos=None):
        self.carrinhos = carrinhos or {}  # user -> [ItemCarrinho]
        self.produtos = produtos or {}  # id -> ProdutoInfo
        self.pedidos = []  # (user, linhas, total)

    @contextmanager
    def transacao(self):
        """Um 'fake' honesto precisa imitar a ATOMICIDADE: tira uma foto (BEGIN) e a restaura se algo falhar (ROLLBACK)."""
        foto = copy.deepcopy((self.carrinhos, self.produtos, self.pedidos))
        try:
            yield
        except Exception:
            self.carrinhos, self.produtos, self.pedidos = foto
            raise

    def travar_carrinho(self, user):
        return user if user in self.carrinhos else None

    def itens_do_carrinho(self, carrinho):
        return list(self.carrinhos[carrinho])

    def travar_produtos(self, ids):
        return {i: self.produtos[i] for i in ids if i in self.produtos}

    def criar_pedido(self, user, linhas, total):
        self.pedidos.append((user, list(linhas), total))
        return PedidoMemoria(len(self.pedidos), total, list(linhas))

    def baixar_estoque(self, product_id, quantidade):
        p = self.produtos[product_id]
        if p.estoque < quantidade:
            return False
        self.produtos[product_id] = ProdutoInfo(p.id, p.nome, p.preco, p.estoque - quantidade, p.ativo)
        return True

    def esvaziar_carrinho(self, carrinho):
        self.carrinhos[carrinho] = []
