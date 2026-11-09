from django.db import transaction
from django.db.models import F

from apps.catalog.models import Product

from .models import Cart, CartItem

QUANTIDADE_MAXIMA = 20


class CartError(Exception):
    """Regra de negócio do carrinho violada; a mensagem é apresentável ao usuário."""


def get_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@transaction.atomic
def add_item(user, product_id, quantity=1):
    if quantity < 1:
        raise CartError("A quantidade deve ser pelo menos 1.")
    try:
        product = Product.objects.get(pk=product_id, is_active=True)
    except Product.DoesNotExist:
        raise CartError("Produto indisponível.") from None
    cart = get_cart(user)
    item = CartItem.objects.filter(cart=cart, product=product).first()
    novo = (item.quantity if item else 0) + quantity
    if novo > product.stock:
        raise CartError(f"Estoque insuficiente: restam {product.stock} unidade(s) de {product.name}.")
    if novo > QUANTIDADE_MAXIMA:
        raise CartError(f"Máximo de {QUANTIDADE_MAXIMA} unidades por produto.")
    if item:
        CartItem.objects.filter(pk=item.pk).update(quantity=F("quantity") + quantity)
    else:
        CartItem.objects.create(cart=cart, product=product, quantity=quantity)
    cart.save(update_fields=["updated_at"])
    return cart


@transaction.atomic
def set_quantity(user, product_id, quantity):
    cart = get_cart(user)
    if quantity == 0:
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        return cart
    if quantity < 0:
        raise CartError("Quantidade inválida.")
    item = CartItem.objects.select_related("product").filter(cart=cart, product_id=product_id).first()
    if item is None:
        raise CartError("Este produto não está no carrinho.")
    if quantity > item.product.stock:
        raise CartError(f"Estoque insuficiente: restam {item.product.stock} unidade(s).")
    if quantity > QUANTIDADE_MAXIMA:
        raise CartError(f"Máximo de {QUANTIDADE_MAXIMA} unidades por produto.")
    item.quantity = quantity
    item.save(update_fields=["quantity"])
    return cart


def remove_item(user, product_id):
    return set_quantity(user, product_id, 0)
