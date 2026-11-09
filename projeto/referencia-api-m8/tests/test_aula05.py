import pytest
from unittest import mock
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def api(cliente):
    c = APIClient(raise_request_exception=False)
    c.force_authenticate(cliente)
    return c


def test_regra_de_negocio_e_422_com_codigo(api):
    r = api.post("/api/v1/orders/")
    assert r.status_code == 422 and r.json() == {"detail": "Seu carrinho está vazio.", "code": "empty_cart"}


def test_validacao_e_400_por_campo(api):
    r = api.post("/api/v1/cart/items/", {"quantity": 1}, format="json")
    assert r.status_code == 400 and "product" in r.json() and "detail" not in r.json()


def test_404_em_portugues(api):
    assert api.get("/api/v1/products/9999/").json()["detail"] == "Não encontrado."


def test_toda_resposta_de_erro_tem_json(api, settings):
    settings.DEBUG = False
    with mock.patch("apps.cart.services.get_cart", side_effect=RuntimeError("segredo")):
        r = api.get("/api/v1/cart/")
    assert r.status_code == 500 and r["Content-Type"].startswith("application/json")
    assert "segredo" not in r.content.decode()                       # nunca vaza a causa interna
