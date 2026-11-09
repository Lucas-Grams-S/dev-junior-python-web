import logging

from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order

from .models import OutboxEvent, Payment, WebhookEvent
from .signals import pedido_pago

logger = logging.getLogger(__name__)
ORDEM = {"pending": 0, "failed": 1, "paid": 2, "refunded": 3}  # estados só ANDAM para frente (fora de ordem não retrocede)


def criar_pagamento(order, provider_ref):
    return Payment.objects.create(order=order, provider_ref=provider_ref, amount=order.total)


@transaction.atomic
def processar_evento(evento) -> tuple[str, str]:
    """Aplica UM evento NORMALIZADO (`EventoPagamento`), venha de qual provedor vier. Idempotente por id; tolerante a ordem e duplicata."""
    existente = WebhookEvent.objects.filter(event_id=evento.id).first()
    if existente:
        return "duplicate", f"evento já {existente.result}"

    def registrar(resultado, detalhe=""):
        WebhookEvent.objects.create(event_id=evento.id, type=evento.tipo, payload=evento.bruto, result=resultado, detail=detalhe)
        return resultado, detalhe

    novo = evento.tipo if evento.tipo in ORDEM else None
    if novo is None:
        return registrar("ignored", f"tipo sem efeito: {evento.tipo}")
    pagamento = Payment.objects.select_for_update().select_related("order").filter(provider_ref=evento.payment_ref).first()
    if pagamento is None:
        return registrar("rejected", "pagamento desconhecido")
    if novo == "paid" and evento.valor != pagamento.amount:  # NUNCA confie só no que o corpo diz
        return registrar("rejected", f"valor divergente: recebido {evento.valor} ≠ esperado {pagamento.amount}")
    if ORDEM[novo] <= ORDEM[pagamento.status]:
        return registrar("ignored", f"fora de ordem: já está {pagamento.status}, chegou {novo}")
    pagamento.status = novo
    if novo == "paid":
        pagamento.paid_at = timezone.now()
        order = Order.objects.select_for_update().get(pk=pagamento.order_id)
        if order.status == Order.Status.PENDING:
            order.status = Order.Status.PAID
            order.save(update_fields=["status"])
        else:  # pagou um pedido já cancelado: precisa de atenção humana
            logger.warning("pagamento_em_pedido_nao_pendente order=%s status=%s", order.pk, order.status)
    pagamento.save()
    if novo == "paid":  # o evento de DOMÍNIO nasce na MESMA transação (outbox)
        OutboxEvent.objects.create(
            type="order.paid", payload={"order_id": pagamento.order_id, "amount": str(pagamento.amount), "webhook_event": evento.id}
        )
        transaction.on_commit(lambda: pedido_pago.send(sender=Payment, order_id=pagamento.order_id, status="paid"))  # só DEPOIS do commit
    return registrar("processed", f"pagamento {novo}")
