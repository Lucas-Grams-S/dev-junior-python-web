import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from apps.cart.models import Cart
from apps.catalog.models import Product

from .models import Order, OrderItem

logger = logging.getLogger(__name__)


class OrderError(Exception):
    pass


class EmptyCartError(OrderError):
    pass


class StockError(OrderError):
    pass


@transaction.atomic
def create_order(user):
    try:
        cart = Cart.objects.select_for_update().get(user=user)
    except Cart.DoesNotExist:
        raise EmptyCartError("Seu carrinho está vazio.") from None
    itens = list(cart.items.all())
    if not itens:
        raise EmptyCartError("Seu carrinho está vazio.")
    ids = sorted(i.product_id for i in itens)
    produtos = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=ids).order_by("pk")}
    problemas = []
    for item in itens:
        p = produtos.get(item.product_id)
        if p is None or not p.is_active:
            problemas.append(f"{p.name if p else 'Um produto'} não está mais disponível.")
        elif item.quantity > p.stock:
            problemas.append(f"{p.name}: restam {p.stock}, você pediu {item.quantity}.")
    if problemas:
        raise StockError(" ".join(problemas))
    total = Decimal("0")
    order = Order.objects.create(user=user, total=0)
    for item in itens:
        p = produtos[item.product_id]
        OrderItem.objects.create(order=order, product=p, quantity=item.quantity, unit_price=p.price)
        total += item.quantity * p.price
        if Product.objects.filter(pk=p.pk, stock__gte=item.quantity).update(stock=F("stock") - item.quantity) != 1:
            raise StockError(f"{p.name}: o estoque mudou, tente novamente.")
    order.total = total
    order.save(update_fields=["total"])
    cart.items.all().delete()
    return order


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
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    return order
