import pytest
from django.core import mail

from apps.orders.tasks import send_order_confirmation_email

pytestmark = pytest.mark.django_db


@pytest.fixture
def cli(api_as):
    c = api_as("cliente")
    c.post("/api/v1/cart/items/", {"product": 2, "quantity": 2}, format="json")
    return c


def test_pedido_enfileira_o_email_so_apos_o_commit(cli, settings, monkeypatch, django_capture_on_commit_callbacks):
    settings.ORDER_EMAIL_MODE = "async"
    enfileirados = []
    monkeypatch.setattr(send_order_confirmation_email, "delay", lambda pk: enfileirados.append(pk))
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        r = cli.post("/api/v1/orders/")
    assert r.status_code == 201
    assert enfileirados == []  # nada saiu antes do commit
    for cb in callbacks:
        cb()  # "o commit aconteceu"
    assert enfileirados == [r.json()["id"]]


def test_pedido_que_falha_nao_enfileira_nada(api_as, settings, monkeypatch, django_capture_on_commit_callbacks):
    settings.ORDER_EMAIL_MODE = "async"
    enfileirados = []
    monkeypatch.setattr(send_order_confirmation_email, "delay", lambda pk: enfileirados.append(pk))
    with django_capture_on_commit_callbacks(execute=True):
        r = api_as("cliente").post("/api/v1/orders/")  # carrinho vazio → 422
    assert r.status_code == 422 and enfileirados == []


def test_tarefa_monta_e_envia_o_email(cli, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.ORDER_EMAIL_MODE = "off"
    pedido_id = cli.post("/api/v1/orders/").json()["id"]
    send_order_confirmation_email(pedido_id)  # chamada direta (síncrona), como em um teste unitário
    assert len(mail.outbox) == 1
    m = mail.outbox[0]
    assert m.to == ["cliente@minishop.local"] and f"#{pedido_id}" in m.subject and "Notebook" in m.body


def test_modo_off_nao_envia_nem_enfileira(cli, settings, monkeypatch, django_capture_on_commit_callbacks):
    settings.ORDER_EMAIL_MODE = "off"
    monkeypatch.setattr(send_order_confirmation_email, "delay", lambda pk: pytest.fail("não deveria enfileirar"))
    with django_capture_on_commit_callbacks(execute=True):
        assert cli.post("/api/v1/orders/").status_code == 201
