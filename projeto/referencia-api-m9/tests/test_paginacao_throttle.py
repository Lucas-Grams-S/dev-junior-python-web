import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_lista_vem_em_envelope_com_20_itens(seed):
    d = APIClient().get("/api/v1/products/").json()
    assert set(d) == {"count", "next", "previous", "results"} and len(d["results"]) == 20


def test_page_size_tem_teto(seed):
    assert len(APIClient().get("/api/v1/products/", {"page_size": 100000}).json()["results"]) <= 100


def test_pagina_invalida_da_404_no_formato_padrao(seed):
    r = APIClient().get("/api/v1/products/", {"page": 999})
    assert r.status_code == 404 and r.json()["code"] == "not_found"


def test_login_e_limitado_a_5_por_minuto(seed):
    codigos = [APIClient().post("/api/v1/auth/token/", {"username": "x", "password": "y"}, format="json").status_code for _ in range(6)]
    assert codigos == [401] * 5 + [429]
