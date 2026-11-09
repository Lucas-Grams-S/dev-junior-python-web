"""Adaptador: converte o evento interno `pedido_pago` em mensagem WebSocket. O serviço de pagamentos não sabe que o Channels existe."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.dispatch import receiver

from apps.payments.signals import pedido_pago

logger = logging.getLogger(__name__)


def notificar_navegador(order_id, status):
    """Empurra a mudança para quem está com o pedido aberto. Falha aqui NÃO pode desfazer o pagamento."""
    layer = get_channel_layer()
    if layer is None:  # CHANNEL_LAYERS não configurado: sem camada, não há a quem avisar
        logger.warning("ws_sem_channel_layer order=%s", order_id)
        return
    try:
        async_to_sync(layer.group_send)(f"pedido_{order_id}", {"type": "pedido.atualizado", "status": status})
    except Exception:
        logger.exception("ws_notificacao_falhou order=%s", order_id)


@receiver(pedido_pago, dispatch_uid="realtime.notificar_navegador")
def ao_pagar(sender, order_id, status, **kwargs):
    notificar_navegador(order_id, status)
