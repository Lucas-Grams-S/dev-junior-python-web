import hashlib, hmac, json, time
from decimal import Decimal

import httpx
import pytest

from apps.payments.gateway import GatewayAcme, GatewayFake, GatewayIndisponivel, obter_gateway
from apps.payments.security import AssinaturaInvalida, assinar

SEG = "acme_segredo"


def acme(handler):
    return GatewayAcme("http://acme", SEG, client=httpx.Client(base_url="http://acme", transport=httpx.MockTransport(handler)))


def webhook_acme(event="charge.captured", cents=11460, created=None, segredo=SEG):
    corpo = json.dumps({"id": "evt_1", "event": event, "created": int(created or time.time()), "charge": {"id": "ch_1", "amount_cents": cents}}).encode()
    return {"X-Acme-Signature": "sha256=" + hmac.new(segredo.encode(), corpo, hashlib.sha256).hexdigest()}, corpo


def test_cobranca_repete_503_com_a_mesma_chave_e_converte_para_centavos():
    vistas = []
    def h(req):
        vistas.append((req.headers["Idempotency-Key"], json.loads(req.content)["amount_cents"]))
        return httpx.Response(503) if len(vistas) == 1 else httpx.Response(201, json={"charge_id": "ch_9"})
    assert acme(h).criar_cobranca(7, Decimal("114.60")).ref == "ch_9"
    assert vistas == [("order-7", 11460), ("order-7", 11460)]


def test_recusa_4xx_nao_repete_e_5xx_esgota():
    n = {"c": 0}
    def h4(req):
        n["c"] += 1; return httpx.Response(422)
    with pytest.raises(GatewayIndisponivel):
        acme(h4).criar_cobranca(1, Decimal("1"))
    assert n["c"] == 1
    with pytest.raises(GatewayIndisponivel):
        acme(lambda r: httpx.Response(503)).criar_cobranca(1, Decimal("1"))


def test_webhook_acme_e_traduzido_para_o_vocabulario_do_minishop():
    cab, corpo = webhook_acme()
    ev = acme(lambda r: httpx.Response(200)).interpretar_webhook(cab, corpo)
    assert (ev.tipo, ev.payment_ref, ev.valor) == ("paid", "ch_1", Decimal("114.60"))


@pytest.mark.parametrize("kw", [dict(segredo="outro"), dict(created=time.time() - 900)])
def test_webhook_acme_rejeita_assinatura_ruim_e_replay(kw):
    cab, corpo = webhook_acme(**kw)
    with pytest.raises(AssinaturaInvalida):
        acme(lambda r: httpx.Response(200)).interpretar_webhook(cab, corpo)


def test_ambos_os_adaptadores_falam_o_mesmo_vocabulario(settings):
    corpo = json.dumps({"id": "e", "type": "payment.succeeded", "data": {"payment_ref": "p", "amount": "10.00"}}).encode()
    ev_fake = GatewayFake().interpretar_webhook({"X-Signature": assinar(settings.WEBHOOK_SECRET, corpo)}, corpo)
    cab, c2 = webhook_acme(cents=1000)
    ev_acme = acme(lambda r: httpx.Response(200)).interpretar_webhook(cab, c2)
    assert ev_fake.tipo == ev_acme.tipo == "paid" and ev_fake.valor == ev_acme.valor == Decimal("10")


def test_fabrica_escolhe_pelo_settings(settings):
    settings.PAYMENT_GATEWAY = "acme"
    assert isinstance(obter_gateway(), GatewayAcme)
    settings.PAYMENT_GATEWAY = "fake"
    assert isinstance(obter_gateway(), GatewayFake)
    settings.PAYMENT_GATEWAY = "xyz"
    with pytest.raises(ValueError):
        obter_gateway()
