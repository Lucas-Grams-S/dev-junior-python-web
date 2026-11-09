import pytest

from apps.catalog.models import Product
from apps.orders.models import IdempotencyKey, Order

pytestmark = pytest.mark.django_db


@pytest.fixture
def cli(api_as):
    c = api_as("cliente")
    c.post("/api/v1/cart/items/", {"product": 2, "quantity": 2}, format="json")
    return c


def pedir(c, chave=None):
    extra = {"HTTP_IDEMPOTENCY_KEY": chave} if chave else {}
    return c.post("/api/v1/orders/", **extra)


def test_mesma_chave_devolve_o_mesmo_pedido_sem_duplicar(cli):
    estoque = Product.objects.get(pk=2).stock
    r1 = pedir(cli, "k-123")
    r2 = pedir(cli, "k-123")
    assert r1.status_code == r2.status_code == 201
    assert r1.json() == r2.json() and r2["Idempotent-Replayed"] == "true" and "Idempotent-Replayed" not in r1
    assert Order.objects.count() == 1 and Product.objects.get(pk=2).stock == estoque - 2     # baixou UMA vez


def test_sem_chave_o_segundo_post_falha_por_carrinho_vazio(cli):
    assert pedir(cli).status_code == 201
    assert pedir(cli).status_code == 422


def test_chave_nova_com_carrinho_vazio_nao_reaproveita_resposta(cli):
    pedir(cli, "k-1")
    assert pedir(cli, "k-2").status_code == 422


def test_falha_nao_grava_a_chave_e_pode_ser_repetida(api_as):
    c = api_as("cliente")
    assert pedir(c, "k-9").status_code == 422                               # carrinho vazio
    assert IdempotencyKey.objects.count() == 0
    c.post("/api/v1/cart/items/", {"product": 2, "quantity": 1}, format="json")
    assert pedir(c, "k-9").status_code == 201                               # mesma chave, agora com sucesso


def test_chave_e_por_usuario(api_as):
    a, b = api_as("cliente"), api_as("gerente")
    for c in (a, b):
        c.post("/api/v1/cart/items/", {"product": 2, "quantity": 1}, format="json")
    assert pedir(a, "mesma").json()["id"] != pedir(b, "mesma").json()["id"]
    assert Order.objects.count() == 2


def test_chave_muito_longa_e_rejeitada(cli):
    assert pedir(cli, "x" * 65).status_code == 400


def test_purge_apaga_so_as_antigas(seed, django_user_model):
    from datetime import timedelta
    from django.core.management import call_command
    from django.utils import timezone
    u = django_user_model.objects.get(username="cliente")
    velha = IdempotencyKey.objects.create(user=u, key="v", response_status=201, response_body={})
    nova = IdempotencyKey.objects.create(user=u, key="n", response_status=201, response_body={})
    IdempotencyKey.objects.filter(pk=velha.pk).update(created_at=timezone.now() - timedelta(hours=25))
    call_command("purge_idempotency_keys")
    assert list(IdempotencyKey.objects.values_list("key", flat=True)) == ["n"]
