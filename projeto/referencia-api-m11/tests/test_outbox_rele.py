"""O relé do outbox e o consumidor idempotente, com um canal FALSO em memória (sem RabbitMQ)."""

import json
from types import SimpleNamespace

import pytest

from apps.payments.models import MensagemProcessada, OutboxEvent
from apps.payments.outbox import consumir, publicar_pendentes

pytestmark = pytest.mark.django_db


class CanalFalso:
    """Imita só o que o relé usa do pika: publicar, buscar e confirmar."""

    def __init__(self):
        self.fila, self.confirmadas = [], []

    def basic_publish(self, exchange, routing_key, corpo, propriedades, mandatory=False):
        self.fila.append((routing_key, corpo, propriedades))

    def basic_get(self, nome_da_fila, auto_ack=False):
        if not self.fila:
            return None, None, None
        _tipo, corpo, props = self.fila.pop(0)
        return SimpleNamespace(delivery_tag=len(self.confirmadas) + 1), props, corpo

    def basic_ack(self, tag):
        self.confirmadas.append(tag)


def criar_eventos(n):
    return [OutboxEvent.objects.create(type="order.paid", payload={"order_id": i}) for i in range(1, n + 1)]


def test_publica_os_pendentes_e_marca_como_publicados():
    criar_eventos(3)
    ch = CanalFalso()
    assert publicar_pendentes(ch) == 3 and len(ch.fila) == 3
    assert OutboxEvent.objects.filter(published_at__isnull=True).count() == 0
    assert publicar_pendentes(ch) == 0  # nada novo: não republica


def test_respeita_o_limite_do_lote():
    criar_eventos(5)
    assert publicar_pendentes(CanalFalso(), limite=2) == 2
    assert OutboxEvent.objects.filter(published_at__isnull=True).count() == 3


def test_queda_entre_publicar_e_marcar_republica_at_least_once():
    criar_eventos(1)
    ch = CanalFalso()
    with pytest.raises(RuntimeError):
        publicar_pendentes(ch, cair_depois_de_publicar=True)
    assert len(ch.fila) == 1 and OutboxEvent.objects.filter(published_at__isnull=True).count() == 1  # publicou, mas não marcou
    assert publicar_pendentes(ch) == 1 and len(ch.fila) == 2  # reenvio: duplicata no broker


def test_consumidor_idempotente_ignora_duplicata_pelo_message_id():
    criar_eventos(1)
    ch = CanalFalso()
    publicar_pendentes(ch)
    ch.fila.append(ch.fila[0])  # o broker entregou a MESMA mensagem duas vezes
    vistos = []
    feitas, ignoradas = consumir(ch, "fila", vistos.append)
    assert (feitas, ignoradas) == (1, 1) and vistos == [{"order_id": 1}]
    assert MensagemProcessada.objects.count() == 1 and len(ch.confirmadas) == 2  # as DUAS foram confirmadas


def test_o_corpo_publicado_e_o_payload_em_json():
    criar_eventos(1)
    ch = CanalFalso()
    publicar_pendentes(ch)
    assert json.loads(ch.fila[0][1]) == {"order_id": 1} and ch.fila[0][0] == "order.paid"
