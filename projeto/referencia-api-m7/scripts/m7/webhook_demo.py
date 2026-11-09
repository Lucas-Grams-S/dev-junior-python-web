"""Webhook de pagamento: um gateway de mentira ENVIA eventos assinados a uma API de verdade (Gunicorn)."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx

LAB = Path(os.environ["LAB"])
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(LAB.parent / "m7"))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

import django

django.setup()
from apps.orders.models import Order
from apps.payments.models import Payment, WebhookEvent
from gateway_fake import enviar, evento

PORTA = 8142
BASE = f"http://127.0.0.1:{PORTA}/api/v1"
SEGREDO = "whsec_lab_apenas_para_estudo"
URL = f"{BASE}/webhooks/payments/"

WebhookEvent.objects.all().delete()
env = {**os.environ, "ORDER_EMAIL_MODE": "off", "WEBHOOK_FAIL_FIRST": "2"}
api = subprocess.Popen([str(LAB / ".venv/bin/gunicorn"), "config.wsgi", "--bind", f"127.0.0.1:{PORTA}", "--threads", "4", "--log-level", "warning"],
                       cwd=LAB, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
for _ in range(100):
    try:
        if httpx.get(f"{BASE}/categories/", timeout=1).status_code == 200:
            break
    except httpx.HTTPError:
        time.sleep(0.2)

h = {"Authorization": "Bearer " + httpx.post(f"{BASE}/auth/token/", json={"username": "cliente", "password": "dev-somente-local-123"}).json()["access"]}


def novo_pedido(qtd=1):
    httpx.post(f"{BASE}/cart/items/", json={"product": 2, "quantity": qtd}, headers=h)
    pedido = httpx.post(f"{BASE}/orders/", headers=h).json()
    pag = httpx.post(f"{BASE}/orders/{pedido['id']}/pay/", headers=h).json()
    return pedido, pag


def estado(pedido_id):
    return f"pedido={Order.objects.get(pk=pedido_id).status}, pagamento={Payment.objects.get(order_id=pedido_id).status}"


def linha(titulo, r, extra=""):
    corpo = r.json()
    print(f"{titulo:<58} → {r.status_code} {corpo.get('result') or corpo.get('code', ''):<18} {extra}")


try:
    pedido, pag = novo_pedido(2)
    print(f"pedido #{pedido['id']} criado (total {pedido['total']}); POST /orders/{pedido['id']}/pay/ → {pag['payment_ref']} ({pag['status']})")
    print("antes de qualquer webhook:", estado(pedido["id"]), "\n")

    ev = evento("payment.succeeded", pag["payment_ref"], pedido["total"], event_id="evt_sucesso_1")

    print("--- o gateway tenta entregar, mas NOSSO servidor está instável (503 nas 2 primeiras vezes)")
    r, tentativas = enviar(URL, SEGREDO, ev, tentativas=5, espera=0.1)
    linha(f"1) payment.succeeded (entregue na tentativa {tentativas})", r, estado(pedido["id"]))

    print("\n--- depois disso, tudo o que pode dar errado:")
    r, _ = enviar(URL, SEGREDO, ev)
    linha("2) o MESMO evento de novo (duplicata)", r, f"eventos gravados: {WebhookEvent.objects.filter(event_id='evt_sucesso_1').count()}")

    corpo = json.dumps(evento("payment.succeeded", pag["payment_ref"], "0.01", event_id="evt_x"), separators=(",", ":")).encode()
    from apps.payments.security import assinar
    assinatura_do_original = assinar(SEGREDO, corpo)
    corpo_adulterado = corpo.replace(b"0.01", b"9.99")
    r, _ = enviar(URL, SEGREDO, None, corpo=corpo_adulterado, cabecalho=assinatura_do_original)
    linha("3) corpo ALTERADO depois de assinado", r)

    r, _ = enviar(URL, "segredo-errado", evento("payment.succeeded", pag["payment_ref"], pedido["total"]))
    linha("4) assinado com o segredo ERRADO", r)

    r, _ = enviar(URL, SEGREDO, evento("payment.succeeded", pag["payment_ref"], pedido["total"]), timestamp=int(time.time()) - 600)
    linha("5) REPLAY: assinatura válida, mas de 10 minutos atrás", r)

    r, _ = enviar(URL, SEGREDO, None, corpo=b"{}", cabecalho="")
    linha("6) sem assinatura", r)

    r, _ = enviar(URL, SEGREDO, evento("payment.failed", pag["payment_ref"], pedido["total"]))
    linha("7) payment.failed chegando DEPOIS do succeeded (fora de ordem)", r, estado(pedido["id"]))

    r, _ = enviar(URL, SEGREDO, evento("payment.succeeded", "pay_inexistente", "10.00"))
    linha("8) pagamento desconhecido", r)

    pedido2, pag2 = novo_pedido(1)
    r, _ = enviar(URL, SEGREDO, evento("payment.succeeded", pag2["payment_ref"], "0.01"))
    linha("9) valor DIVERGENTE (0,01 em vez de %s)" % pedido2["total"], r, estado(pedido2["id"]))

    r, _ = enviar(URL, SEGREDO, None, corpo=b"isto nao e json")
    linha("10) assinatura válida, corpo não é JSON", r)

    r, _ = enviar(URL, SEGREDO, None, corpo=b"x" * 70_000)
    linha("11) corpo de 70 KB (limite 64 KB)", r)

    r = httpx.get(URL)
    print(f"{'12) GET no endpoint':<58} → {r.status_code}")

    print("\n--- auditoria: tabela WebhookEvent")
    for e in WebhookEvent.objects.order_by("id"):
        print(f"  {e.event_id:<18} {e.type:<18} {e.result:<10} {e.detail}")
finally:
    os.killpg(api.pid, signal.SIGTERM)
    api.wait(timeout=20)
