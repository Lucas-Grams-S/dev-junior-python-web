"""Operações do contrato que a verificação de cobertura de rotas apontou como sem teste."""

import pytest
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def alvo(seed):
    return Product.objects.create(category=Category.objects.get(slug="audio"), sku="TST-001", name="Alvo", price=10, stock=5)


def test_categoria_detalhe(api_as):
    assert api_as(None).get("/api/v1/categories/1/").json()["slug"] == "informatica"


def test_produto_put_patch_delete_como_gerente(api_as, alvo):
    ger = api_as("gerente")
    corpo = {"sku": "TST-001", "name": "Alvo 2", "price": "12.50", "stock": 4, "category_slug": "audio"}
    assert ger.put(f"/api/v1/products/{alvo.pk}/", corpo, format="json").json()["name"] == "Alvo 2"
    assert ger.patch(f"/api/v1/products/{alvo.pk}/", {"stock": 9}, format="json").json()["stock"] == 9
    assert ger.delete(f"/api/v1/products/{alvo.pk}/").status_code == 204


def test_estoquista_nao_exclui(api_as, alvo):
    assert api_as("estoquista").delete(f"/api/v1/products/{alvo.pk}/").status_code == 403


def test_refresh_e_logout_invalidam_o_refresh_antigo(seed):
    c = APIClient()
    tok = c.post("/api/v1/auth/token/", {"username": "cliente", "password": "dev-somente-local-123"}, format="json").json()
    novo = c.post("/api/v1/auth/token/refresh/", {"refresh": tok["refresh"]}, format="json").json()
    assert c.post("/api/v1/auth/token/refresh/", {"refresh": tok["refresh"]}, format="json").status_code == 401  # rotação
    assert c.post("/api/v1/auth/logout/", {"refresh": novo["refresh"]}, format="json").status_code == 200
    assert c.post("/api/v1/auth/token/refresh/", {"refresh": novo["refresh"]}, format="json").status_code == 401
