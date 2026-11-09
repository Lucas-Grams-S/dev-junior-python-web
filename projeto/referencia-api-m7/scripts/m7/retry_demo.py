"""Retentativas e idempotência com um worker de verdade: SMTP que cai, mensagens duplicadas, erro permanente, desistência."""
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(os.environ["LAB"])
sys.path.insert(0, str(LAB))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

import django
import redis

django.setup()
from django.contrib.auth import get_user_model

from apps.catalog.models import Product
from apps.orders.models import EmailLog, Order, OrderItem
from apps.orders.tasks import send_order_confirmation_email

R = redis.Redis(port=6390)
U = get_user_model()
OUTBOX = LAB / "outbox.jsonl"


def novo_pedido(email="cliente@minishop.local"):
    u = U.objects.get(username="cliente")
    U.objects.filter(pk=u.pk).update(email=email)
    p = Product.objects.get(sku="INF-002")
    o = Order.objects.create(user=u, total=p.price)
    OrderItem.objects.create(order=o, product=p, quantity=1, unit_price=p.price)
    return o.pk


def cenario(titulo, falhas, acao, finais=1, espera=14):
    R.flushdb(); OUTBOX.unlink(missing_ok=True)
    log = LAB / "worker3.log"
    env = {**os.environ, "EMAIL_FAIL_FIRST": str(falhas), "EMAIL_SIMULATED_DELAY": "0.1"}
    w = subprocess.Popen([str(LAB / ".venv/bin/celery"), "-A", "config", "worker", "-l", "info", "-c", "1", "--without-gossip", "--without-mingle"],
                         cwd=LAB, env=env, stdout=open(log, "w"), stderr=subprocess.STDOUT, start_new_session=True)
    time.sleep(3.5)
    pedido = acao()
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < espera:                       # espera o(s) desfecho(s) final(is): sucesso ou falha definitiva
        time.sleep(0.3)
        txt = log.read_text()
        if len(re.findall(r"succeeded in|raised unexpected", txt)) >= finais:
            break
    time.sleep(0.5)
    os.killpg(w.pid, signal.SIGTERM); w.wait(timeout=30)
    print(f"\n=== {titulo}")
    for l in log.read_text().splitlines():
        if re.search(r"Task orders\.|email_(sent|skip|retry|failed|desistiu)", l):
            hora = re.match(r"\[\d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2})", l)
            msg = re.sub(r"^\[[^\]]*\] ", "", l)
            msg = re.sub(r"orders\.send_order_confirmation_email\[[0-9a-f]{8}-[0-9a-f-]+\]", "tarefa[…]", msg)
            print(f"  {hora.group(1) if hora else '        '} {msg[:130]}")
    reg = EmailLog.objects.filter(order_id=pedido).first()
    enviados = len(OUTBOX.read_text().splitlines()) if OUTBOX.exists() else 0
    print(f"  → e-mails realmente enviados: {enviados} | EmailLog: status={reg.status if reg else None}, tentativas={reg.attempts if reg else None}, erro={reg.last_error if reg else ''!r}")


cenario("1) SMTP cai nas 3 primeiras tentativas → retentativas com backoff exponencial + jitter", 3,
        lambda: (lambda p: (send_order_confirmation_email.delay(p), p)[1])(novo_pedido()), espera=20)


def tres_copias():
    p = novo_pedido()
    for _ in range(3):                                             # a MESMA mensagem entregue 3 vezes (at-least-once)
        send_order_confirmation_email.delay(p)
    return p


cenario("2) a mesma mensagem chega 3 vezes → só 1 e-mail (idempotência)", 0, tres_copias, finais=3, espera=8)

cenario("3) erro PERMANENTE (usuário sem e-mail) → não repete, registra a falha", 0,
        lambda: (lambda p: (send_order_confirmation_email.delay(p), p)[1])(novo_pedido(email="")), espera=8)

cenario("4) o SMTP nunca volta → esgota as 4 retentativas e desiste", 99,
        lambda: (lambda p: (send_order_confirmation_email.delay(p), p)[1])(novo_pedido()), espera=40)
U.objects.filter(username="cliente").update(email="cliente@minishop.local")
