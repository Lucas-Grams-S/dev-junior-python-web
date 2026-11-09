import pytest

pytestmark = pytest.mark.django_db


def test_token_expirado_da_401(api_anonimo, cliente):
    from datetime import timedelta
    from rest_framework_simplejwt.tokens import AccessToken
    t = AccessToken.for_user(cliente)
    t.set_exp(lifetime=timedelta(seconds=-1))
    api_anonimo.credentials(HTTP_AUTHORIZATION=f"Bearer {t}")
    assert api_anonimo.get("/api/v1/cart/").status_code == 401


def test_me_so_expoe_campos_do_contrato(api_anonimo, cliente):
    r = api_anonimo.post("/api/v1/auth/token/", {"username": "cliente", "password": "dev-somente-local-123"}, format="json")
    api_anonimo.credentials(HTTP_AUTHORIZATION="Bearer " + r.json()["access"])
    assert set(api_anonimo.get("/api/v1/auth/me/").json()) == {"id", "username", "email"}
