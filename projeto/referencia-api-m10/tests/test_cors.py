import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
PERMITIDA = "http://127.0.0.1:8200"
MALICIOSA = "https://site-malicioso.example"


def test_origem_permitida_recebe_cabecalho():
    r = APIClient().get("/api/v1/categories/", HTTP_ORIGIN=PERMITIDA)
    assert r["Access-Control-Allow-Origin"] == PERMITIDA


def test_origem_nao_permitida_nao_recebe_cabecalho():
    r = APIClient().get("/api/v1/categories/", HTTP_ORIGIN=MALICIOSA)
    assert "Access-Control-Allow-Origin" not in r


def test_preflight_lista_metodos_e_cabecalhos():
    r = APIClient().options(
        "/api/v1/cart/items/",
        HTTP_ORIGIN=PERMITIDA,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type",
    )
    assert r.status_code == 200 and "authorization" in r["Access-Control-Allow-Headers"] and "POST" in r["Access-Control-Allow-Methods"]


def test_nunca_curinga_com_credenciais(settings):
    assert settings.CORS_ALLOW_CREDENTIALS is False and "*" not in settings.CORS_ALLOWED_ORIGINS


def test_admin_fica_fora_do_cors():
    assert "Access-Control-Allow-Origin" not in APIClient().get("/admin/login/", HTTP_ORIGIN=PERMITIDA)


def test_preflight_libera_o_cabecalho_idempotency_key():
    r = APIClient().options(
        "/api/v1/orders/",
        HTTP_ORIGIN=PERMITIDA,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,idempotency-key",
    )
    assert "idempotency-key" in r["Access-Control-Allow-Headers"]
    assert "Idempotent-Replayed" in r["Access-Control-Expose-Headers"]
