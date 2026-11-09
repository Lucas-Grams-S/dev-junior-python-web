import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client

from apps.accounts.lgpd import anonimizar, exportar_dados
from apps.cart import services as carrinho
from apps.cart.models import Cart
from apps.catalog.models import Product
from apps.orders import services as pedidos
from apps.orders.models import Order

pytestmark = pytest.mark.django_db
SENHA = "dev-somente-local-123"


@pytest.fixture
def titular(seed, django_user_model, settings):
    settings.ORDER_EMAIL_MODE = "off"
    u = django_user_model.objects.get(username="cliente")
    u.first_name, u.last_name = "Maria", "Souza"
    u.save()
    p = Product.objects.filter(is_active=True, stock__gt=5).first()
    carrinho.add_item(u, p.pk, 2)
    pedidos.create_order(u)
    carrinho.add_item(u, p.pk, 1)
    return u


def test_exportacao_traz_conta_pedidos_e_carrinho_sem_segredos(titular):
    dados = exportar_dados(titular)
    assert dados["conta"]["email"] == "cliente@minishop.local" and dados["conta"]["nome"] == "Maria Souza"
    assert len(dados["pedidos"]) == 1 and dados["pedidos"][0]["itens"][0]["quantidade"] == 2
    assert len(dados["carrinho"]) == 1
    texto = json.dumps(dados)
    assert "password" not in texto and "pbkdf2" not in texto and "argon2" not in texto


def test_comando_de_exportacao_imprime_json_valido(titular):
    saida = StringIO()
    call_command("exportar_dados_titular", "cliente", stdout=saida)
    assert json.loads(saida.getvalue())["conta"]["usuario"] == "cliente"


def test_anonimizacao_remove_dados_pessoais_e_mantem_os_pedidos(titular):
    antes = Order.objects.filter(user=titular).count()
    assert anonimizar(titular) is True
    titular.refresh_from_db()
    assert titular.username == f"anonimo-{titular.pk}" and titular.email == "" and titular.first_name == "" and titular.last_name == ""
    assert not titular.is_active and not titular.has_usable_password()
    assert Order.objects.filter(user=titular).count() == antes == 1  # a venda continua registrada
    assert not Cart.objects.filter(user_id=titular.pk).exists()  # o carrinho não é registro fiscal: foi apagado


def test_anonimizar_duas_vezes_e_seguro(titular):
    assert anonimizar(titular) is True
    titular.refresh_from_db()
    assert anonimizar(titular) is False


def test_depois_de_anonimizar_o_login_e_o_refresh_deixam_de_funcionar(titular):
    c = Client()
    tokens = c.post("/api/v1/auth/token/", {"username": "cliente", "password": SENHA}, content_type="application/json").json()
    anonimizar(titular)
    assert (
        Client().post("/api/v1/auth/token/", {"username": "cliente", "password": SENHA}, content_type="application/json").status_code == 401
    )
    assert Client().post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]}, content_type="application/json").status_code == 401


def test_o_email_liberado_pode_ser_reusado_por_outra_conta(titular, django_user_model):
    anonimizar(titular)
    assert django_user_model.objects.create_user(username="nova", email="cliente@minishop.local", password=SENHA).pk
