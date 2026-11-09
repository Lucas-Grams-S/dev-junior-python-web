import json
import time

import pytest
from django.test import Client

from apps.orders.models import Order
from apps.payments import security
from apps.payments.models import Payment, WebhookEvent
from apps.payments.services import criar_pagamento
from apps.cart import services as carrinho
from apps.orders import services

pytestmark = pytest.mark.django_db
SEGREDO = "whsec_lab_apenas_para_estudo"
URL = "/api/v1/webhooks/payments/"


@pytest.fixture
def pagamento(cliente):
    carrinho.add_item(cliente, 2, 2)
    pedido = services.create_order(cliente)
    return criar_pagamento(pedido, "pay_teste_123")


def evento(pagamento, tipo="payment.succeeded", valor=None, eid="evt_1"):
    return {"id": eid, "type": tipo, "data": {"payment_ref": pagamento.provider_ref, "amount": str(valor or pagamento.amount)}}


def enviar(ev, segredo=SEGREDO, agora=None, cabecalho=None, corpo=None):
    bruto = corpo if corpo is not None else json.dumps(ev, separators=(",", ":")).encode()
    c = cabecalho if cabecalho is not None else security.assinar(segredo, bruto, agora=agora)
    return Client().post(URL, data=bruto, content_type="application/json", HTTP_X_SIGNATURE=c)


def test_sucesso_marca_pedido_e_pagamento_como_pagos(pagamento):
    r = enviar(evento(pagamento))
    assert r.status_code == 200 and r.json()["result"] == "processed"
    pagamento.refresh_from_db()
    assert pagamento.status == "paid" and pagamento.paid_at and pagamento.order.status == Order.Status.PAID


def test_evento_duplicado_nao_reprocessa(pagamento):
    assert enviar(evento(pagamento)).json()["result"] == "processed"
    assert enviar(evento(pagamento)).json()["result"] == "duplicate"
    assert WebhookEvent.objects.count() == 1


def test_assinatura_errada_adulterada_ou_ausente_da_401(pagamento):
    ev = evento(pagamento)
    assert enviar(ev, segredo="outro").status_code == 401
    bruto = json.dumps(ev, separators=(",", ":")).encode()
    assert enviar(None, corpo=bruto.replace(b"evt_1", b"evt_2"), cabecalho=security.assinar(SEGREDO, bruto)).status_code == 401
    assert enviar(ev, cabecalho="").status_code == 401
    assert enviar(ev, cabecalho="lixo").status_code == 401
    pagamento.refresh_from_db()
    assert pagamento.status == "pending" and WebhookEvent.objects.count() == 0       # nada foi gravado


def test_replay_antigo_e_rejeitado(pagamento):
    assert enviar(evento(pagamento), agora=int(time.time()) - 600).status_code == 401
    assert enviar(evento(pagamento), agora=int(time.time()) - 60).status_code == 200      # dentro da tolerância


def test_fora_de_ordem_nao_retrocede(pagamento):
    enviar(evento(pagamento, "payment.succeeded", eid="evt_a"))
    r = enviar(evento(pagamento, "payment.failed", eid="evt_b"))
    assert r.json()["result"] == "ignored"
    pagamento.refresh_from_db()
    assert pagamento.status == "paid"


def test_chegando_na_ordem_inversa_o_estado_final_e_o_mesmo(pagamento):
    enviar(evento(pagamento, "payment.refunded", eid="evt_r"))      # (estorno chega ANTES do pagamento?!)
    enviar(evento(pagamento, "payment.succeeded", eid="evt_s"))
    pagamento.refresh_from_db()
    assert pagamento.status == "refunded"                           # o estado mais "avançado" vence; "paid" depois é ignorado


def test_valor_divergente_e_rejeitado(pagamento):
    r = enviar(evento(pagamento, valor="0.01"))
    assert r.json()["result"] == "rejected"
    pagamento.refresh_from_db()
    assert pagamento.status == "pending" and pagamento.order.status == "pending"


def test_corpo_invalido_e_grande_demais(pagamento):
    assert enviar(None, corpo=b"nao e json").status_code == 400
    assert enviar(None, corpo=b"x" * 70_000).status_code == 413


def test_so_aceita_post():
    assert Client().get(URL).status_code == 405


def test_pagar_pedido_cria_pagamento_pendente_idempotente(api_as):
    cli = api_as("cliente")
    cli.post("/api/v1/cart/items/", {"product": 2, "quantity": 1}, format="json")
    pedido = cli.post("/api/v1/orders/").json()
    oid = pedido["id"]
    r1 = cli.post(f"/api/v1/orders/{oid}/pay/")
    r2 = cli.post(f"/api/v1/orders/{oid}/pay/")
    assert r1.status_code == 201 and r2.status_code == 200 and r1.json()["payment_ref"] == r2.json()["payment_ref"]
    assert api_as("gerente").post(f"/api/v1/orders/{oid}/pay/").status_code == 404      # só o dono paga


def test_assinatura_usa_comparacao_em_tempo_constante():
    import inspect
    assert "compare_digest" in inspect.getsource(security.verificar)


def test_pagamento_notifica_o_navegador_so_apos_o_commit(pagamento, monkeypatch, django_capture_on_commit_callbacks):
    chamadas = []
    from apps.payments.signals import pedido_pago
    pedido_pago.connect(lambda sender, order_id, status, **kw: chamadas.append((order_id, status)), dispatch_uid="teste_notificacao", weak=False)
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        enviar(evento(pagamento))
    assert chamadas == []                                    # ainda dentro da transação
    for cb in callbacks:
        cb()
    pedido_pago.disconnect(dispatch_uid="teste_notificacao")
    assert chamadas == [(pagamento.order_id, "paid")]


def test_pagamento_grava_o_evento_no_outbox_na_mesma_transacao(pagamento):
    from apps.payments.models import OutboxEvent
    enviar(evento(pagamento))
    ev = OutboxEvent.objects.get()
    assert ev.type == "order.paid" and ev.payload["order_id"] == pagamento.order_id and ev.published_at is None
