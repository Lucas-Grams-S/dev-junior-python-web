import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def api(cliente):
    c = APIClient()
    c.force_authenticate(cliente)
    return c


def test_categoria_nao_aceita_delete(api):
    assert api.delete("/api/v1/categories/1/").status_code == 405


def test_pedido_alheio_da_404(api, gerente, seed):
    from apps.cart import services as carrinho
    from apps.orders import services as pedidos
    carrinho.add_item(gerente, 2, 1)
    pedido = pedidos.create_order(gerente)
    assert api.get(f"/api/v1/orders/{pedido.pk}/").status_code == 404


def test_lista_de_produtos_nao_faz_n_mais_1(api, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        assert api.get("/api/v1/products/").status_code == 200
