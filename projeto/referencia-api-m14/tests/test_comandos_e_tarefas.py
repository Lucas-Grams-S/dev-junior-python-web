"""Comandos de manutenção (LGPD) e tarefas que faltavam."""

import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.cart import services as carrinho
from apps.orders import services as pedidos
from apps.orders.models import EmailLog, IdempotencyKey
from apps.orders.tasks import KIND, MarcaFalha, batimento, limpar_chaves_de_idempotencia

pytestmark = pytest.mark.django_db


def test_anonimizar_titular_via_comando_e_idempotente(cliente):
    out = StringIO()
    call_command("anonimizar_titular", "cliente", stdout=out)
    assert out.getvalue().strip() == "anonimizado"
    out2 = StringIO()
    call_command("anonimizar_titular", "anonimo-" + str(cliente.pk), stdout=out2)
    assert "já estava" in out2.getvalue()


@pytest.mark.parametrize("comando", ["anonimizar_titular", "exportar_dados_titular"])
def test_comandos_de_titular_recusam_usuario_inexistente(seed, comando):
    with pytest.raises(CommandError, match="não encontrado"):
        call_command(comando, "ninguem")


def test_exportar_via_comando_gera_json(cliente):
    out = StringIO()
    call_command("exportar_dados_titular", "cliente", stdout=out)
    assert json.loads(out.getvalue())["conta"]["usuario"] == "cliente"


def test_marca_falha_registra_a_desistencia_da_tarefa(cliente, criar_produto, settings):
    settings.ORDER_EMAIL_MODE = "off"
    carrinho.add_item(cliente, criar_produto().pk, 1)
    pedido = pedidos.create_order(cliente)
    log = EmailLog.objects.create(order=pedido, kind=KIND, status=EmailLog.Status.SENDING)
    MarcaFalha().on_failure(RuntimeError("SMTP caiu"), "id-1", (pedido.pk,), {}, None)
    log.refresh_from_db()
    assert log.status == EmailLog.Status.FAILED and "SMTP caiu" in log.last_error


def test_limpar_chaves_antigas_devolve_quantas_apagou(cliente):
    from datetime import timedelta

    from django.utils import timezone

    velha = IdempotencyKey.objects.create(user=cliente, key="velha", response_body={}, response_status=201)
    IdempotencyKey.objects.filter(pk=velha.pk).update(created_at=timezone.now() - timedelta(hours=48))
    IdempotencyKey.objects.create(user=cliente, key="nova", response_body={}, response_status=201)
    assert limpar_chaves_de_idempotencia(horas=24) == 1


def test_batimento_responde_ok():
    assert batimento() == "ok"
