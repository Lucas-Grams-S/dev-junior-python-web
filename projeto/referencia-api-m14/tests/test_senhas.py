import pytest
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.test import Client

pytestmark = pytest.mark.django_db


def test_senhas_novas_usam_argon2id(hasher_de_producao):
    h = make_password("uma-senha-bem-longa-123")
    assert h.startswith("argon2$argon2id$") and identify_hasher(h).algorithm == "argon2"


def test_mesma_senha_gera_hashes_diferentes_por_causa_do_salt():
    assert make_password("igual-igual-igual") != make_password("igual-igual-igual")


def test_senha_antiga_em_pbkdf2_ainda_e_aceita_e_regravada_em_argon2_no_login(django_user_model, hasher_de_producao):
    u = django_user_model.objects.create(username="antigo")
    u.password = make_password("senha-antiga-segura-1", hasher="pbkdf2_sha256")
    u.save()
    assert u.password.startswith("pbkdf2_sha256$")
    r = Client().post("/api/v1/auth/token/", {"username": "antigo", "password": "senha-antiga-segura-1"}, content_type="application/json")
    assert r.status_code == 200
    u.refresh_from_db()
    assert u.password.startswith("argon2$argon2id$") and check_password("senha-antiga-segura-1", u.password)


@pytest.mark.parametrize("fraca", ["123", "12345678", "password", "senha123", "abc", "11111111111111"])
def test_senhas_fracas_sao_recusadas(fraca):
    with pytest.raises(ValidationError):
        validate_password(fraca)


def test_senha_parecida_com_o_usuario_e_recusada(django_user_model):
    u = django_user_model(username="mariaoliveira", email="maria@exemplo.com")
    with pytest.raises(ValidationError):
        validate_password("mariaoliveira2024", user=u)


def test_frase_longa_e_aceita():
    validate_password("correto cavalo bateria grampo")
