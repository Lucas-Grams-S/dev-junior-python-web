"""Celery + Redis na prática: o pedido responde rápido e o e-mail sai depois, por um worker separado."""
import base64
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

import httpx
import redis

LAB = Path(os.environ["LAB"])
PY = LAB / ".venv/bin"
PORTA = 8141
BASE = f"http://127.0.0.1:{PORTA}/api/v1"
OUTBOX = LAB / "outbox.jsonl"
R = redis.Redis(port=6390)


def subir_api(modo):
    env = {**os.environ, "ORDER_EMAIL_MODE": modo}
    p = subprocess.Popen([str(PY / "gunicorn"), "config.wsgi", "--bind", f"127.0.0.1:{PORTA}", "--threads", "8", "--log-level", "warning"],
                         cwd=LAB, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(100):
        try:
            if httpx.get(f"{BASE}/categories/", timeout=1).status_code == 200:
                return p
        except httpx.HTTPError:
            time.sleep(0.2)
    raise RuntimeError("API não subiu")


def parar(p):
    os.killpg(p.pid, signal.SIGTERM)
    p.wait(timeout=20)


def token():
    r = httpx.post(f"{BASE}/auth/token/", json={"username": "cliente", "password": "dev-somente-local-123"})
    return {"Authorization": f"Bearer {r.json()['access']}"}


def pedido(h):
    httpx.post(f"{BASE}/cart/items/", json={"product": 2, "quantity": 1}, headers=h)
    t = time.perf_counter()
    r = httpx.post(f"{BASE}/orders/", headers=h, timeout=30)
    return r.status_code, time.perf_counter() - t


def emails_enviados():
    return [json.loads(l) for l in OUTBOX.read_text().splitlines()] if OUTBOX.exists() else []


def limpar():
    R.flushdb()
    OUTBOX.unlink(missing_ok=True)


# ------------------------------------------------------------------------------------------
print("=== A) e-mail SÍNCRONO dentro da requisição (como em 7.01)")
limpar()
api = subir_api("sync")
h = token()
tempos = [pedido(h)[1] for _ in range(3)]
print(f"POST /orders/ com SMTP de 0,8 s no meio → {', '.join(f'{t:.2f} s' for t in tempos)} | e-mails já enviados quando a resposta chegou: {len(emails_enviados())}")
parar(api)

print("\n=== B) e-mail ASSÍNCRONO: a API só ENFILEIRA (e o worker ainda está desligado)")
limpar()
api = subir_api("async")
h = token()
status, t = pedido(h)
print(f"POST /orders/ → {status} em {t:.2f} s | e-mails enviados: {len(emails_enviados())} | mensagens esperando na fila 'celery' do Redis: {R.llen('celery')}")
msg = json.loads(R.lrange("celery", 0, 0)[0])
corpo = json.loads(base64.b64decode(msg["body"]))
print("a mensagem na fila (resumo):")
print("   tarefa   :", msg["headers"]["task"])
print("   id       :", msg["headers"]["id"][:8] + "…")
print("   argumentos:", corpo[0], " ← só o ID do pedido, nunca o objeto")

print("\n=== C) ligamos o worker: ele consome a fila")
log = open(LAB / "worker.log", "w")
worker = subprocess.Popen([str(PY / "celery"), "-A", "config", "worker", "-l", "info", "-c", "4", "--without-gossip", "--without-mingle"],
                          cwd=LAB, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
t0 = time.perf_counter()
while len(emails_enviados()) < 1 and time.perf_counter() - t0 < 30:
    time.sleep(0.1)
print(f"e-mail enviado {time.perf_counter() - t0:.1f} s depois de ligar o worker (inclui a partida do worker) | fila agora: {R.llen('celery')}")
print("e-mail gravado:", {k: (v if k != 'body' else v.splitlines()[2]) for k, v in emails_enviados()[0].items()})

print("\n=== D) 8 pedidos em sequência: a API não espera pelos e-mails")
antes = len(emails_enviados())
t = time.perf_counter()
tempos = [pedido(h)[1] for _ in range(8)]
total_api = time.perf_counter() - t
print(f"as 8 respostas da API levaram {total_api:.2f} s no total (média {sum(tempos) / 8 * 1000:.0f} ms cada)")
t = time.perf_counter()
while len(emails_enviados()) - antes < 8 and time.perf_counter() - t < 30:
    time.sleep(0.1)
print(f"os 8 e-mails (0,8 s cada; 4 workers em paralelo) terminaram {time.perf_counter() - t:.1f} s depois da última resposta | total de e-mails: {len(emails_enviados())}")

os.killpg(worker.pid, signal.SIGTERM)
worker.wait(timeout=30)
parar(api)
log.close()
linhas = [l for l in (LAB / "worker.log").read_text().splitlines() if "Task orders.send_order_confirmation_email" in l]
print("\n=== log do worker (primeiras linhas relevantes)")
for l in linhas[:4]:
    print("  ", re.sub(r"^\[[^\]]*\] ", "", l.replace(str(LAB), "")))
print(f"   ... ({len(linhas)} linhas de tarefas no total)")
