import logging

from django.db import transaction
from django.db.models import F

from apps.catalog import cache as catalog_cache
from apps.catalog.models import Product

from . import domain
from .models import Order
from .repositories import DjangoPedidoRepository

logger = logging.getLogger(__name__)


class OrderError(Exception):
    pass


class EmptyCartError(OrderError):
    pass


class StockError(OrderError):
    pass


def create_order(user, repo=None):
    """Caso de uso: criar o pedido a partir do carrinho. Orquestra; as REGRAS estão em `domain` e a PERSISTÊNCIA no repositório."""
    repo = repo or DjangoPedidoRepository()
    with repo.transacao():
        carrinho = repo.travar_carrinho(user)  # trava o carrinho: serializa duplo clique
        itens = repo.itens_do_carrinho(carrinho) if carrinho is not None else []
        if not itens:
            raise EmptyCartError("Seu carrinho está vazio.")
        produtos = repo.travar_produtos(sorted(i.product_id for i in itens))  # trava os produtos em ordem fixa (sem deadlock)
        linhas = domain.montar_linhas(itens, produtos)
        achados = domain.problemas(itens, linhas)  # valida TUDO antes de gravar
        if achados:
            raise StockError(" ".join(achados))
        pedido = repo.criar_pedido(user, linhas, domain.total(linhas))
        for linha in linhas:
            if not repo.baixar_estoque(linha.product_id, linha.quantidade):  # defesa extra: nunca deveria ocorrer com a trava
                raise StockError(f"{linha.nome}: o estoque mudou, tente novamente.")
        repo.esvaziar_carrinho(carrinho)
        logger.info("order_created user=%s linhas=%s", getattr(user, "pk", user), len(linhas))
        return pedido


@transaction.atomic
def cancel_order(user, order_id):
    try:
        order = Order.objects.select_for_update().get(pk=order_id, user=user)
    except Order.DoesNotExist:
        raise OrderError("Pedido não encontrado.") from None
    if order.status != Order.Status.PENDING:
        raise OrderError("Só é possível cancelar pedidos pendentes.")
    for item in sorted(order.items.all(), key=lambda i: i.product_id):
        Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
    transaction.on_commit(catalog_cache.bump)  # estoque devolvido: o catálogo em cache está desatualizado
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    return order
