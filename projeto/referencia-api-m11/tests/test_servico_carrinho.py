"""Ramos de erro do serviço de carrinho: cada regra de negócio é um caso."""

import pytest

from apps.cart import services
from apps.cart.models import CartItem

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "quantidade,msg",
    [
        pytest.param(0, "pelo menos 1", id="zero"),
        pytest.param(-3, "pelo menos 1", id="negativa"),
    ],
)
def test_adicionar_quantidade_invalida(cliente, criar_produto, quantidade, msg):
    with pytest.raises(services.CartError, match=msg):
        services.add_item(cliente, criar_produto().pk, quantidade)


def test_produto_inativo_ou_inexistente_nao_entra(cliente, criar_produto):
    inativo = criar_produto(ativo=False)
    with pytest.raises(services.CartError, match="indisponível"):
        services.add_item(cliente, inativo.pk, 1)
    with pytest.raises(services.CartError, match="indisponível"):
        services.add_item(cliente, 999999, 1)


def test_nao_passa_do_estoque_nem_do_maximo(cliente, criar_produto):
    pouco = criar_produto(estoque=2)
    with pytest.raises(services.CartError, match="Estoque insuficiente"):
        services.add_item(cliente, pouco.pk, 3)
    muito = criar_produto(estoque=500)
    with pytest.raises(services.CartError, match=f"Máximo de {services.QUANTIDADE_MAXIMA}"):
        services.add_item(cliente, muito.pk, services.QUANTIDADE_MAXIMA + 1)


def test_somar_ao_item_existente_respeita_o_estoque(cliente, criar_produto):
    p = criar_produto(estoque=3)
    services.add_item(cliente, p.pk, 2)
    services.add_item(cliente, p.pk, 1)
    assert CartItem.objects.get(cart__user=cliente, product=p).quantity == 3
    with pytest.raises(services.CartError):
        services.add_item(cliente, p.pk, 1)


# ------------------------------------------------------------------------------------------ set_quantity
def test_definir_quantidade_zero_remove_o_item(cliente, criar_produto):
    p = criar_produto()
    services.add_item(cliente, p.pk, 2)
    services.set_quantity(cliente, p.pk, 0)
    assert not CartItem.objects.filter(cart__user=cliente, product=p).exists()


@pytest.mark.parametrize(
    "quantidade,msg",
    [
        pytest.param(-1, "inválida", id="negativa"),
        pytest.param(50, "Estoque insuficiente", id="acima-do-estoque"),
    ],
)
def test_definir_quantidade_invalida(cliente, criar_produto, quantidade, msg):
    p = criar_produto(estoque=5)
    services.add_item(cliente, p.pk, 1)
    with pytest.raises(services.CartError, match=msg):
        services.set_quantity(cliente, p.pk, quantidade)


def test_definir_quantidade_de_item_que_nao_esta_no_carrinho(cliente, criar_produto):
    with pytest.raises(services.CartError, match="não está no carrinho"):
        services.set_quantity(cliente, criar_produto().pk, 2)


def test_definir_quantidade_acima_do_maximo(cliente, criar_produto):
    p = criar_produto(estoque=500)
    services.add_item(cliente, p.pk, 1)
    with pytest.raises(services.CartError, match="Máximo"):
        services.set_quantity(cliente, p.pk, services.QUANTIDADE_MAXIMA + 1)
