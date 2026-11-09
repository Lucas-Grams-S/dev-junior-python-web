"""O 'relé' do outbox: lê eventos ainda não publicados e os entrega ao RabbitMQ, confirmando cada um."""

import json

import pika
from django.db import transaction
from django.utils import timezone

from .models import MensagemProcessada, OutboxEvent

EXCHANGE = "minishop.eventos"


def conexao(porta=5680):
    c = pika.BlockingConnection(pika.ConnectionParameters("127.0.0.1", porta, heartbeat=30))
    ch = c.channel()
    ch.exchange_declare(EXCHANGE, exchange_type="topic", durable=True)
    ch.confirm_delivery()  # o broker confirma cada publicação
    return c, ch


def publicar_pendentes(ch, limite=100, cair_depois_de_publicar=False):
    """Publica os eventos pendentes. Se o processo cair ENTRE publicar e marcar, o evento será publicado de novo (at-least-once)."""
    publicados = 0
    for ev in OutboxEvent.objects.filter(published_at__isnull=True).order_by("id")[:limite]:
        ch.basic_publish(
            EXCHANGE,
            ev.type,
            json.dumps(ev.payload).encode(),
            pika.BasicProperties(delivery_mode=2, message_id=f"outbox-{ev.pk}", content_type="application/json"),
            mandatory=True,
        )
        if cair_depois_de_publicar:
            raise RuntimeError("💥 o relé caiu depois de publicar e antes de marcar como publicado")
        OutboxEvent.objects.filter(pk=ev.pk).update(published_at=timezone.now())
        publicados += 1
    return publicados


def consumir(ch, fila, tratar, maximo=10):
    """Consumidor IDEMPOTENTE: ignora message_id já visto. Devolve (executadas, ignoradas)."""
    feitas = ignoradas = 0
    for _ in range(maximo):
        metodo, props, corpo = ch.basic_get(fila, auto_ack=False)
        if metodo is None:
            break
        with transaction.atomic():
            _, novo = MensagemProcessada.objects.get_or_create(message_id=props.message_id)
            if novo:
                tratar(json.loads(corpo))
                feitas += 1
            else:
                ignoradas += 1
        ch.basic_ack(metodo.delivery_tag)  # confirma DEPOIS de gravar o efeito
    return feitas, ignoradas
