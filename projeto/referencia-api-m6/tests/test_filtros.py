import pytest
from decimal import Decimal
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def api(seed):
    return APIClient()


def skus(r):
    return [i["sku"] for i in r.json()["results"]]


def test_publico_nao_ve_produtos_inativos(api):
    assert all(i["is_active"] for i in api.get("/api/v1/products/", {"page_size": 100}).json()["results"])


def test_equipe_ve_inativos(seed):
    from django.contrib.auth import get_user_model
    c = APIClient()
    c.force_authenticate(get_user_model().objects.get(username="gerente"))
    assert any(not i["is_active"] for i in c.get("/api/v1/products/", {"page_size": 100}).json()["results"])


def test_filtro_por_categoria_e_preco(api):
    r = api.get("/api/v1/products/", {"category": "audio", "price_min": "400", "price_max": "450"})
    itens = r.json()["results"]
    assert itens and all(i["category"]["slug"] == "audio" and Decimal("400") <= Decimal(i["price"]) <= Decimal("450") for i in itens)


def test_busca_ignora_maiusculas_e_acha_por_sku(api):
    assert "INF-005" in skus(api.get("/api/v1/products/", {"search": "MOUSE"}))
    assert skus(api.get("/api/v1/products/", {"search": "inf-001"})) == ["INF-001"]


def test_ordenacao_por_preco(api):
    precos = [Decimal(i["price"]) for i in api.get("/api/v1/products/", {"ordering": "-price", "page_size": 100}).json()["results"]]
    assert precos == sorted(precos, reverse=True)


def test_ordenacao_fora_da_lista_e_ignorada(api):
    r = api.get("/api/v1/products/", {"ordering": "password"})
    assert r.status_code == 200 and skus(r) == skus(api.get("/api/v1/products/"))        # cai na ordem padrão


def test_valor_invalido_da_400_por_campo(api):
    r = api.get("/api/v1/products/", {"price_min": "abc"})
    assert r.status_code == 400 and "price_min" in r.json()


def test_lista_tem_consulta_fixa(api, django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        api.get("/api/v1/products/", {"search": "a", "ordering": "price"})
