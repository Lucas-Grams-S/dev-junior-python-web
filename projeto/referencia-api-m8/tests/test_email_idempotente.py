import pytest
from django.core import mail

from apps.orders.models import EmailLog, Order, OrderItem
from apps.orders.tasks import ErroTransitorio, send_order_confirmation_email
from apps.catalog.models import Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def pedido(cliente, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    p = Product.objects.get(sku="INF-002")
    o = Order.objects.create(user=cliente, total=p.price)
    OrderItem.objects.create(order=o, product=p, quantity=1, unit_price=p.price)
    return o


def test_executar_duas_vezes_envia_um_email(pedido):
    assert send_order_confirmation_email(pedido.pk) == "enviado"
    assert send_order_confirmation_email(pedido.pk) == "ja_tratado"          # a repetição não faz nada
    assert len(mail.outbox) == 1
    log = EmailLog.objects.get(order=pedido)
    assert (log.status, log.attempts) == ("sent", 1)


def test_pedido_inexistente_nao_repete(db):
    assert send_order_confirmation_email(999999) == "pedido_inexistente"


def test_falha_transitoria_solta_o_reclamo_para_a_proxima_tentativa(pedido, monkeypatch):
    def quebra(*a, **k):
        raise ConnectionError("SMTP caiu")
    monkeypatch.setattr("apps.orders.tasks.send_mail", quebra)
    with pytest.raises(Exception):                                            # o autoretry do Celery relança/agenda
        send_order_confirmation_email.apply(args=[pedido.pk], throw=True)
    log = EmailLog.objects.get(order=pedido)
    assert log.status in ("pending", "failed") and "SMTP caiu" in log.last_error and len(mail.outbox) == 0


def test_depois_da_falha_a_nova_tentativa_envia(pedido, monkeypatch):
    chamadas = {"n": 0}
    original = __import__("django.core.mail", fromlist=["send_mail"]).send_mail

    def instavel(*a, **k):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            raise ConnectionError("SMTP caiu")
        return original(*a, **k)
    monkeypatch.setattr("apps.orders.tasks.send_mail", instavel)
    try:
        send_order_confirmation_email.apply(args=[pedido.pk], throw=True)
    except Exception:
        pass
    log = EmailLog.objects.get(order=pedido)
    if log.status != "sent":                                                  # (a 1ª tentativa deixou 'pending')
        assert send_order_confirmation_email(pedido.pk) == "enviado"
    assert len(mail.outbox) == 1 and EmailLog.objects.get(order=pedido).status == "sent"


def test_sem_email_e_erro_permanente(pedido):
    pedido.user.email = ""
    pedido.user.save()
    with pytest.raises(Exception, match="sem e-mail"):
        send_order_confirmation_email(pedido.pk)
    assert EmailLog.objects.get(order=pedido).status == "failed" and len(mail.outbox) == 0


def test_reenviar_falhos_volta_para_a_fila(pedido, monkeypatch):
    from django.core.management import call_command
    EmailLog.objects.create(order=pedido, kind="order_confirmation", status="failed", attempts=5, last_error="x")
    enfileirados = []
    monkeypatch.setattr(send_order_confirmation_email, "delay", lambda pk: enfileirados.append(pk))
    call_command("reenviar_emails_falhos")
    log = EmailLog.objects.get(order=pedido)
    assert enfileirados == [pedido.pk] and (log.status, log.attempts) == ("pending", 0)
