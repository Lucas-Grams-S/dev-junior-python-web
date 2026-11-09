import base64
import json

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db
SENHA = "dev-somente-local-123"


def b64(d):
    return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()


def token(cliente):
    return cliente.post("/api/v1/auth/token/", {"username": "cliente", "password": SENHA}, content_type="application/json").json()


def test_post_com_cookie_de_sessao_sem_token_csrf_e_recusado(seed, django_user_model):
    django_user_model.objects.create_superuser("adm", "a@x.com", SENHA)
    c = Client(enforce_csrf_checks=True)
    assert c.post("/admin/login/", {"username": "adm", "password": SENHA}).status_code == 403


def test_com_token_csrf_o_login_funciona(seed, django_user_model):
    django_user_model.objects.create_superuser("adm", "a@x.com", SENHA)
    c = Client(enforce_csrf_checks=True)
    c.get("/admin/login/")
    r = c.post("/admin/login/", {"username": "adm", "password": SENHA, "csrfmiddlewaretoken": c.cookies["csrftoken"].value})
    assert r.status_code == 302


def test_jwt_com_payload_alterado_e_recusado(seed):
    h, p, s = token(Client())["access"].split(".")
    pl = json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))
    pl["user_id"] = "1"
    r = Client(HTTP_AUTHORIZATION=f"Bearer {h}.{b64(pl)}.{s}").get("/api/v1/auth/me/")
    assert r.status_code == 401


def test_jwt_sem_assinatura_algoritmo_none_e_recusado(seed):
    _, p, _ = token(Client())["access"].split(".")
    r = Client(HTTP_AUTHORIZATION=f"Bearer {b64({'alg': 'none', 'typ': 'JWT'})}.{p}.").get("/api/v1/auth/me/")
    assert r.status_code == 401


def test_access_token_e_curto(settings):
    assert settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds() <= 900


def test_cookies_de_sessao_tem_atributos_seguros(settings):
    assert settings.SESSION_COOKIE_HTTPONLY is True and settings.SESSION_COOKIE_SAMESITE in ("Lax", "Strict")
    assert settings.CSRF_COOKIE_SAMESITE in ("Lax", "Strict")
