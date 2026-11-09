"""O erro clássico: enfileirar a tarefa DENTRO da transação, antes do COMMIT."""
import os
import signal
import subprocess
import time
from pathlib import Path
import sys

LAB = Path(os.environ["LAB"])
sys.path.insert(0, str(LAB))

import django
import redis
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.orders.models import Order
from apps.orders.tasks import send_order_confirmation_email

R = redis.Redis(port=6390)
R.flushdb()
Path(LAB / "outbox.jsonl").unlink(missing_ok=True)
usuario = get_user_model().objects.get(username="cliente")

log = open(LAB / "worker2.log", "w")
worker = subprocess.Popen([str(LAB / ".venv/bin/celery"), "-A", "config", "worker", "-l", "info", "-c", "2", "--without-gossip", "--without-mingle"],
                          cwd=LAB, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
time.sleep(4)                                                      # worker no ar


def com_erro():
    with transaction.atomic():
        pedido = Order.objects.create(user=usuario, total=10)
        send_order_confirmation_email.delay(pedido.pk)             # ERRADO: o worker é mais rápido que o COMMIT
        time.sleep(0.6)                                            # (o resto da view demorando um pouco)
    return pedido.pk


def correto():
    with transaction.atomic():
        pedido = Order.objects.create(user=usuario, total=10)
        transaction.on_commit(lambda: send_order_confirmation_email.delay(pedido.pk))   # só DEPOIS do commit
        time.sleep(0.6)
    return pedido.pk


a = com_erro()
time.sleep(1.5)
b = correto()
time.sleep(3)
os.killpg(worker.pid, signal.SIGTERM)
worker.wait(timeout=30)
log.close()
for l in (LAB / "worker2.log").read_text().splitlines():
    if "Task orders.send_order_confirmation_email" in l and ("raised unexpected" in l or "succeeded" in l):
        pid = a if "Order matching" in l or False else None
        print(" ", l.split("] ", 1)[1][:150] if l.startswith("[") else l[:150])
print(f"(pedido do caso ERRADO: #{a}; pedido do caso CORRETO: #{b})")
