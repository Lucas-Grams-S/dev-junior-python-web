"""processar_evento direto (sem HTTP): cada ramo de rejeição/ordem/estado do pedido."""

import logging
from decimal import Decimal

import pytest

from apps.cart import services as carrinho
from apps.orders import services as pedidos
from apps.orders.models import Order
from apps.payments import services
from apps.payments.gateway import EventoPagamento
from apps.payments.models import OutboxEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def pagamento(cliente, criar_produto, settings):
    settings.ORDER_EMAIL_MODE = "off"
    carrinho.add_item(cliente, criar_produto(preco="50.00", estoque=9).pk, 2)
    pedido = pedidos.create_order(cliente)
    return services.criar_pagamento(pedido, "ref-1")


def evento(tipo, id="e1", ref="ref-1", valor=Decimal("100.00")):
    return EventoPagamento(id=id, tipo=tipo, payment_ref=ref, valor=valor, bruto={})


@pytest.mark.parametrize(
    "tipo,ref,valor,resultado,trecho",
    [
        pytest.param("paid", "ref-inexistente", Decimal("100.00"), "rejected", "desconhecido", id="pagamento-desconhecido"),
        pytest.param("paid", "ref-1", Decimal("1.00"), "rejected", "valor divergente", id="valor-divergente"),
        pytest.param("ignored", "ref-1", Decimal("100.00"), "ignored", "sem efeito", id="tipo-sem-efeito"),
    ],
)
def test_eventos_que_nao_mudam_nada(pagamento, tipo, ref, valor, resultado, trecho):
    res, detalhe = services.processar_evento(evento(tipo, ref=ref, valor=valor))
    assert res == resultado and trecho in detalhe
    pagamento.refresh_from_db()
    assert pagamento.status == "pending" and OutboxEvent.objects.count() == 0


def test_pago_atualiza_pedido_e_grava_o_evento_de_dominio_na_mesma_transacao(pagamento):
    assert services.processar_evento(evento("paid"))[0] == "processed"
    pagamento.refresh_from_db()
    pagamento.order.refresh_from_db()
    assert pagamento.status == "paid" and pagamento.order.status == Order.Status.PAID
    assert OutboxEvent.objects.filter(type="order.paid", payload__order_id=pagamento.order_id).count() == 1


def test_repetir_o_mesmo_evento_e_duplicata(pagamento):
    services.processar_evento(evento("paid"))
    assert services.processar_evento(evento("paid"))[0] == "duplicate"
    assert OutboxEvent.objects.count() == 1


def test_estado_nao_retrocede(pagamento):
    services.processar_evento(evento("paid", id="e1"))
    res, detalhe = services.processar_evento(evento("failed", id="e2"))
    assert res == "ignored" and "fora de ordem" in detalhe


def test_pagamento_de_pedido_ja_cancelado_pede_atencao_humana(pagamento, caplog):
    Order.objects.filter(pk=pagamento.order_id).update(status=Order.Status.CANCELLED)
    with caplog.at_level(logging.WARNING, logger="apps.payments.services"):
        services.processar_evento(evento("paid"))
    pagamento.order.refresh_from_db()
    assert pagamento.order.status == Order.Status.CANCELLED  # não ressuscita o pedido
    assert "pagamento_em_pedido_nao_pendente" in caplog.text
