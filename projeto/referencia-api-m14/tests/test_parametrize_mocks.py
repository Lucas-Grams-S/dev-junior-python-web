"""Aula 10.02: parametrize e mocks nas BORDAS (relógio, fila, gateway). O que é nosso, usamos de verdade."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import create_autospec

import pytest
from django.utils import timezone

from apps.orders import notifications
from apps.orders.models import Order
from apps.orders.tasks import cancelar_pedidos_pendentes_antigos
from apps.payments.gateway import Cobranca, GatewayIndisponivel, PaymentGateway


# ------------------------------------------------------------------------------------------ parametrize
class EspiaDaTarefa:
    """Substituto simples da tarefa de e-mail: registra o que foi pedido."""

    def __init__(self):
        self.chamadas, self.enfileiradas = [], []

    def __call__(self, order_id):
        self.chamadas.append(order_id)

    def delay(self, order_id):
        self.enfileiradas.append(order_id)


@pytest.mark.parametrize(
    "modo,executa_agora,enfileira_no_commit",
    [
        pytest.param("sync", True, False, id="sync-executa-na-hora"),
        pytest.param("async", False, True, id="async-enfileira-so-no-commit"),
        pytest.param("off", False, False, id="off-nao-faz-nada"),
    ],
)
def test_notificacao_conforme_o_modo(
    db, modo, executa_agora, enfileira_no_commit, settings, monkeypatch, django_capture_on_commit_callbacks
):
    settings.ORDER_EMAIL_MODE = modo
    espia = EspiaDaTarefa()
    monkeypatch.setattr(notifications, "send_order_confirmation_email", espia)  # onde é USADA (não onde é definida)
    pedido = type("Pedido", (), {"pk": 42})()
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        notifications.notificar_pedido_criado(pedido)
    assert (espia.chamadas == [42]) is executa_agora
    assert espia.enfileiradas == []  # nada sai antes do commit
    for cb in callbacks:
        cb()
    assert (espia.enfileiradas == [42]) is enfileira_no_commit


# ------------------------------------------------------------------------------------------ relógio controlado
def test_cancela_pendentes_antigos_avancando_o_relogio(cliente, criar_produto, monkeypatch):
    from apps.cart import services as carrinho
    from apps.orders import services

    p = criar_produto(estoque=10)
    carrinho.add_item(cliente, p.pk, 2)
    pedido = services.create_order(cliente)
    cancelar_pedidos_pendentes_antigos(horas=24)
    pedido.refresh_from_db()
    assert pedido.status == Order.Status.PENDING  # agora mesmo: ainda vale

    futuro = timezone.now() + timedelta(hours=25)
    monkeypatch.setattr(timezone, "now", lambda: futuro)  # o "amanhã" chegou, sem dormir
    cancelar_pedidos_pendentes_antigos(horas=24)
    pedido.refresh_from_db()
    assert pedido.status == Order.Status.CANCELLED
    p.refresh_from_db()
    assert p.stock == 10  # e o estoque voltou


# ------------------------------------------------------------------------------------------ gateway com autospec
@pytest.fixture
def pedido_pendente(api_as, settings, criar_produto, cliente):
    from apps.cart import services as carrinho
    from apps.orders import services

    settings.ORDER_EMAIL_MODE = "off"
    p = criar_produto(preco="50.00", estoque=10)
    carrinho.add_item(cliente, p.pk, 2)
    return services.create_order(cliente)


@pytest.mark.parametrize(
    "resultado,status_http,corpo",
    [
        pytest.param(Cobranca(ref="mock-123"), 201, {"payment_ref": "mock-123"}, id="gateway-ok"),
        pytest.param(GatewayIndisponivel("fora do ar"), 422, {"code": "gateway_unavailable"}, id="gateway-fora-do-ar"),
    ],
)
def test_pagar_com_gateway_dublado(api_as, pedido_pendente, monkeypatch, resultado, status_http, corpo):
    gateway = create_autospec(PaymentGateway, instance=True)  # só aceita o que a PORTA real tem
    if isinstance(resultado, Exception):
        gateway.criar_cobranca.side_effect = resultado
    else:
        gateway.criar_cobranca.return_value = resultado
    monkeypatch.setattr("apps.payments.api.obter_gateway", lambda: gateway)  # onde é USADO
    r = api_as("cliente").post(f"/api/v1/orders/{pedido_pendente.pk}/pay/")
    assert r.status_code == status_http and all(r.json()[k] == v for k, v in corpo.items())
    gateway.criar_cobranca.assert_called_once_with(pedido_pendente.pk, Decimal("100.00"))
