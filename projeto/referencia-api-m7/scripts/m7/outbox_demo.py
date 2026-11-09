"""O problema da ESCRITA DUPLA (banco + broker) e o padrão outbox, com Django e RabbitMQ de verdade."""
import os
import sys
from pathlib import Path

LAB = Path(os.environ["LAB"])
sys.path.insert(0, str(LAB))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

import django

django.setup()
import pika
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.orders.models import Order
from apps.payments.models import MensagemProcessada, OutboxEvent
from apps.payments.outbox import EXCHANGE, conexao, consumir, publicar_pendentes

usuario = get_user_model().objects.get(username="cliente")
OutboxEvent.objects.all().delete(); MensagemProcessada.objects.all().delete()

c, ch = conexao()
ch.queue_delete("q.recibo")
ch.queue_declare("q.recibo", durable=True)
ch.queue_bind("q.recibo", EXCHANGE, routing_key="order.paid")


def na_fila():
    return ch.queue_declare("q.recibo", passive=True).method.message_count


def novo_pedido_pago():
    return Order.objects.create(user=usuario, total=10, status="paid")


print("--- A) ESCRITA DUPLA ingênua: grava no banco, DEPOIS publica (dois sistemas, sem transação entre eles)")
try:
    with transaction.atomic():
        pedido_a = novo_pedido_pago()                                  # 1) o banco confirma
    raise ConnectionError("💥 o processo caiu AQUI, depois do commit e antes de publicar")
    ch.basic_publish(EXCHANGE, "order.paid", b"{}")                    # 2) nunca executa
except ConnectionError as e:
    print(e)
print(f"pedido #{pedido_a.pk} está 'paid' no banco, mas mensagens na fila de recibos: {na_fila()}  ← o evento se PERDEU para sempre\n")

print("--- B) OUTBOX: o evento é gravado NA MESMA transação do estado")
with transaction.atomic():
    pedido_b = novo_pedido_pago()
    OutboxEvent.objects.create(type="order.paid", payload={"order_id": pedido_b.pk})
print(f"pedido #{pedido_b.pk} 'paid' e evento no outbox, atomicamente. Pendentes no outbox: {OutboxEvent.objects.filter(published_at__isnull=True).count()} | na fila: {na_fila()}")
print("(mesmo que o processo caia agora, o evento NÃO se perde: está no banco)")
print("o relé roda (agora ou minutos depois) → publicados:", publicar_pendentes(ch), "| na fila:", na_fila(), "| pendentes no outbox:", OutboxEvent.objects.filter(published_at__isnull=True).count())

print("\n--- C) o relé cai DEPOIS de publicar e ANTES de marcar → o evento é publicado de NOVO (at-least-once)")
with transaction.atomic():
    pedido_c = novo_pedido_pago()
    OutboxEvent.objects.create(type="order.paid", payload={"order_id": pedido_c.pk})
try:
    publicar_pendentes(ch, cair_depois_de_publicar=True)
except RuntimeError as e:
    print(e)
print("rodando o relé outra vez → publicados:", publicar_pendentes(ch), "| mensagens na fila (3 = 1 do passo B + 2 cópias do passo C):", na_fila())

print("\n--- D) o CONSUMIDOR idempotente trata as 3 mensagens (2 têm o mesmo message_id)")
efeitos = []
feitas, ignoradas = consumir(ch, "q.recibo", lambda corpo: efeitos.append(corpo["order_id"]))
print(f"executou o efeito {feitas} vezes e ignorou {ignoradas} duplicata(s) | pedidos que receberam recibo: {efeitos}")
ch.queue_delete("q.recibo")
c.close()
Order.objects.filter(pk__in=[pedido_a.pk, pedido_b.pk, pedido_c.pk]).delete()
