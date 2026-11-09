from datetime import timedelta

import pytest
from django.utils import timezone

from apps.cart import services as carrinho
from apps.catalog.models import Product
from apps.orders import services
from apps.orders.models import IdempotencyKey, Order
from apps.orders.tasks import cancelar_pedidos_pendentes_antigos, limpar_chaves_de_idempotencia

pytestmark = pytest.mark.django_db


def pedido_com_idade(user, horas):
    carrinho.add_item(user, 2, 2)
    o = services.create_order(user)
    Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(hours=horas))
    return o


def test_cancela_so_os_pendentes_antigos_e_devolve_estoque(cliente):
    antes = Product.objects.get(pk=2).stock
    velho = pedido_com_idade(cliente, 30)
    novo = pedido_com_idade(cliente, 1)
    pago = pedido_com_idade(cliente, 40)
    Order.objects.filter(pk=pago.pk).update(status="paid")
    assert Product.objects.get(pk=2).stock == antes - 6
    assert cancelar_pedidos_pendentes_antigos(horas=24) == 1
    status = {o.pk: o.status for o in Order.objects.all()}
    assert status == {velho.pk: "cancelled", novo.pk: "pending", pago.pk: "paid"}
    assert Product.objects.get(pk=2).stock == antes - 4  # só os 2 do pedido cancelado voltaram


def test_rodar_de_novo_nao_faz_nada_idempotente(cliente):
    pedido_com_idade(cliente, 30)
    assert cancelar_pedidos_pendentes_antigos(horas=24) == 1
    assert cancelar_pedidos_pendentes_antigos(horas=24) == 0


def test_limpa_chaves_antigas(cliente):
    velha = IdempotencyKey.objects.create(user=cliente, key="v", response_status=201, response_body={})
    IdempotencyKey.objects.create(user=cliente, key="n", response_status=201, response_body={})
    IdempotencyKey.objects.filter(pk=velha.pk).update(created_at=timezone.now() - timedelta(hours=25))
    assert limpar_chaves_de_idempotencia() == 1
    assert list(IdempotencyKey.objects.values_list("key", flat=True)) == ["n"]


def test_agenda_do_beat_aponta_para_tarefas_que_existem():
    from django.conf import settings

    from config.celery import app

    app.loader.import_default_modules()
    for nome, item in settings.CELERY_BEAT_SCHEDULE.items():
        assert item["task"] in app.tasks, f"{nome}: tarefa {item['task']} não registrada"
