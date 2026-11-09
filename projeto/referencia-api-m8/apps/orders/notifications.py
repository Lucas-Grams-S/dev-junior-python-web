from django.conf import settings
from django.db import transaction

from .tasks import send_order_confirmation_email


def notificar_pedido_criado(order):
    """O que fazer DEPOIS que o pedido foi criado, conforme ORDER_EMAIL_MODE."""
    modo = settings.ORDER_EMAIL_MODE
    if modo == "sync":                                   # ANTES (aula 7.01): o cliente espera o SMTP
        send_order_confirmation_email(order.pk)
    elif modo == "async":                                # DEPOIS: enfileira, e só depois do COMMIT
        transaction.on_commit(lambda: send_order_confirmation_email.delay(order.pk))
