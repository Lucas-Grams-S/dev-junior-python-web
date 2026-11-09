import logging
from decimal import Decimal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order

from .models import OutboxEvent, Payment, WebhookEvent

logger = logging.getLogger(__name__)
ORDEM = {"pending": 0, "failed": 1, "paid": 2, "refunded": 3}      # estados só ANDAM para frente (fora de ordem não retrocede)


def criar_pagamento(order, provider_ref):
    return Payment.objects.create(order=order, provider_ref=provider_ref, amount=order.total)


@transaction.atomic
def processar_evento(evento: dict) -> tuple[str, str]:
    """Aplica UM evento do gateway. Devolve (resultado, detalhe). Idempotente por event_id; tolerante a ordem e duplicata."""
    existente = WebhookEvent.objects.filter(event_id=evento["id"]).first()
    if existente:
        return "duplicate", f"evento já {existente.result}"
    tipo, dados = evento["type"], evento.get("data", {})

    def registrar(resultado, detalhe=""):
        WebhookEvent.objects.create(event_id=evento["id"], type=tipo, payload=evento, result=resultado, detail=detalhe)
        return resultado, detalhe

    novo = {"payment.succeeded": "paid", "payment.failed": "failed", "payment.refunded": "refunded"}.get(tipo)
    if novo is None:
        return registrar("ignored", f"tipo desconhecido: {tipo}")
    pagamento = Payment.objects.select_for_update().select_related("order").filter(provider_ref=dados.get("payment_ref")).first()
    if pagamento is None:
        return registrar("rejected", "pagamento desconhecido")
    if novo == "paid" and Decimal(str(dados.get("amount"))) != pagamento.amount:           # NUNCA confie só no que o corpo diz
        return registrar("rejected", f"valor divergente: recebido {dados.get('amount')} ≠ esperado {pagamento.amount}")
    if ORDEM[novo] <= ORDEM[pagamento.status]:
        return registrar("ignored", f"fora de ordem: já está {pagamento.status}, chegou {novo}")
    pagamento.status = novo
    if novo == "paid":
        pagamento.paid_at = timezone.now()
        order = Order.objects.select_for_update().get(pk=pagamento.order_id)
        if order.status == Order.Status.PENDING:
            order.status = Order.Status.PAID
            order.save(update_fields=["status"])
        else:                                                                                  # pagou um pedido já cancelado: precisa de atenção humana
            logger.warning("pagamento_em_pedido_nao_pendente order=%s status=%s", order.pk, order.status)
    pagamento.save()
    if novo == "paid":                                                          # o evento de DOMÍNIO nasce na MESMA transação (outbox)
        OutboxEvent.objects.create(type="order.paid", payload={"order_id": pagamento.order_id, "amount": str(pagamento.amount),
                                                               "webhook_event": evento["id"]})
        transaction.on_commit(lambda: notificar_navegador(pagamento.order_id, "paid"))      # tempo real: só DEPOIS do commit
    return registrar("processed", f"pagamento {novo}")


def notificar_navegador(order_id, status):
    """Empurra a mudança para quem está com o pedido aberto (WebSocket). Falha aqui NÃO pode desfazer o pagamento."""
    try:
        async_to_sync(get_channel_layer().group_send)(f"pedido_{order_id}", {"type": "pedido.atualizado", "status": status})
    except Exception:                                                            # Redis fora do ar: o cliente ainda vê o status ao recarregar
        logger.exception("ws_notificacao_falhou order=%s", order_id)
