"""Trocar de provedor de pagamento = trocar UMA variável de ambiente. O resto do MiniShop não muda."""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx

LAB = Path(os.environ["LAB"])
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB.parent / "m8"))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django

django.setup()
from apps.orders.models import Order
from apps.payments.gateway import obter_gateway
from apps.payments.models import Payment, WebhookEvent
from django.test import override_settings
from servidor_acme import ESTADO, enviar_webhook, iniciar

SEGREDO_ACME = "acme_whsec_lab_apenas_para_estudo"
WebhookEvent.objects.all().delete()
for nome in ("fake", "acme"):
    with override_settings(PAYMENT_GATEWAY=nome):
        print(f"PAYMENT_GATEWAY={nome:<5} → obter_gateway() devolve {type(obter_gateway()).__name__}")

acme = iniciar(8150)
env = {**os.environ, "PAYMENT_GATEWAY": "acme", "ORDER_EMAIL_MODE": "off"}
api = subprocess.Popen([str(LAB / ".venv/bin/gunicorn"), "config.wsgi", "--bind", "127.0.0.1:8142", "--threads", "4", "--log-level", "warning"],
                       cwd=LAB, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
BASE = "http://127.0.0.1:8142/api/v1"
for _ in range(100):
    try:
        httpx.get(f"{BASE}/categories/", timeout=1); break
    except httpx.HTTPError:
        time.sleep(0.2)
try:
    h = {"Authorization": "Bearer " + httpx.post(f"{BASE}/auth/token/", json={"username": "cliente", "password": "dev-somente-local-123"}).json()["access"]}
    httpx.post(f"{BASE}/cart/items/", json={"product": 2, "quantity": 2}, headers=h)
    pedido = httpx.post(f"{BASE}/orders/", headers=h).json()
    pag = httpx.post(f"{BASE}/orders/{pedido['id']}/pay/", headers=h, timeout=15).json()
    cents = int(float(pedido["total"]) * 100)
    print(f"\npedido #{pedido['id']} total {pedido['total']}; POST /pay/ → {pag['payment_ref']} ({pag['status']})")
    print(f"  o MiniShop pediu a cobrança em centavos ({cents}); a Acme recebeu {ESTADO['requisicoes']} requisição(ões): a 1ª deu 503 e o adaptador REPETIU com a mesma Idempotency-Key")
    print(f"  cobranças criadas na Acme: {len(ESTADO['cobrancas'])} (uma só, apesar da repetição)")

    URL = f"{BASE}/webhooks/payments/"
    def teste(titulo, r):
        print(f"  {titulo:<58} → {r.status_code} {r.json().get('result') or r.json().get('code')}")
    print("\nwebhooks no dialeto da Acme (evento 'charge.captured', valor em centavos, outra assinatura):")
    r, corpo = enviar_webhook(URL, SEGREDO_ACME, "charge.captured", pag["payment_ref"], cents, "CAPTURED")
    teste("1) charge.captured válido", r)
    print("      estado:", f"pedido={Order.objects.get(pk=pedido['id']).status}, pagamento={Payment.objects.get(order_id=pedido['id']).status}")
    teste("2) o MESMO corpo de novo (duplicata)", httpx.post(URL, content=corpo, headers={"X-Acme-Signature": "sha256=" + __import__('hmac').new(SEGREDO_ACME.encode(), corpo, "sha256").hexdigest()}))
    teste("3) assinatura inválida", enviar_webhook(URL, SEGREDO_ACME, "charge.captured", pag["payment_ref"], cents, "CAPTURED", assinar=False)[0])
    teste("4) assinado com o segredo do MiniShop (outro dialeto!)", enviar_webhook(URL, "whsec_lab_apenas_para_estudo", "charge.captured", pag["payment_ref"], cents, "CAPTURED")[0])
    teste("5) evento antigo (replay, 10 min)", enviar_webhook(URL, SEGREDO_ACME, "charge.captured", pag["payment_ref"], cents, "CAPTURED", created=time.time() - 600)[0])
    teste("6) charge.authorized (a Acme tem, nós não usamos)", enviar_webhook(URL, SEGREDO_ACME, "charge.authorized", pag["payment_ref"], cents, "AUTHORIZED")[0])
    teste("7) charge.declined depois do captured (fora de ordem)", enviar_webhook(URL, SEGREDO_ACME, "charge.declined", pag["payment_ref"], cents, "DECLINED")[0])
    print("\nauditoria (WebhookEvent):")
    for e in WebhookEvent.objects.order_by("id"):
        print(f"  {e.type:<9} {e.result:<10} {e.detail}")
finally:
    os.killpg(api.pid, signal.SIGTERM); api.wait(timeout=20)
