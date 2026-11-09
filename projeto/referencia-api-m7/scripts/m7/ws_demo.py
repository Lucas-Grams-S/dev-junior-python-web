"""Tempo real: o navegador (cliente WebSocket) vê o pedido virar 'paid' no instante em que o webhook chega a OUTRO processo."""
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx
import websockets
from websockets.exceptions import InvalidStatus

LAB = Path(os.environ["LAB"])
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB.parent / "m7"))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django

django.setup()
from apps.payments.security import assinar

API, WS = "http://127.0.0.1:8142/api/v1", "ws://127.0.0.1:8143"
env = {**os.environ, "ORDER_EMAIL_MODE": "off"}
procs = [
    subprocess.Popen([str(LAB / ".venv/bin/gunicorn"), "config.wsgi", "--bind", "127.0.0.1:8142", "--threads", "4", "--log-level", "warning"],
                     cwd=LAB, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True),
    subprocess.Popen([str(LAB / ".venv/bin/uvicorn"), "config.asgi:application", "--host", "127.0.0.1", "--port", "8143", "--log-level", "warning"],
                     cwd=LAB, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True),
]
for _ in range(100):
    try:
        httpx.get(f"{API}/categories/", timeout=1)
        httpx.get("http://127.0.0.1:8143/api/v1/categories/", timeout=1)
        break
    except httpx.HTTPError:
        time.sleep(0.2)


def token(user):
    return httpx.post(f"{API}/auth/token/", json={"username": user, "password": "dev-somente-local-123"}).json()["access"]


async def tentar(url, rotulo):
    try:
        async with websockets.connect(url, open_timeout=5) as ws:
            return f"{rotulo:<46} → CONECTOU: {json.loads(await ws.recv())}"
    except InvalidStatus as e:
        return f"{rotulo:<46} → recusado no handshake (HTTP {e.response.status_code})"


async def main():
    tk, tg = token("cliente"), token("gerente")
    h = {"Authorization": f"Bearer {tk}"}
    httpx.post(f"{API}/cart/items/", json={"product": 2, "quantity": 1}, headers=h)
    pedido = httpx.post(f"{API}/orders/", headers=h).json()
    pag = httpx.post(f"{API}/orders/{pedido['id']}/pay/", headers=h).json()
    url = f"{WS}/ws/pedidos/{pedido['id']}/"
    print(f"pedido #{pedido['id']} pendente; a API (WSGI) está na porta 8142 e o WebSocket (ASGI) na 8143: processos DIFERENTES\n")

    print("--- autenticação e autorização no WebSocket")
    print(await tentar(url, "sem token"))
    print(await tentar(url + "?token=lixo", "token inválido"))
    print(await tentar(url + f"?token={tg}", "token de OUTRO usuário (gerente) no pedido da cliente"))

    print("\n--- duas abas abertas no mesmo pedido; o webhook chega ao outro processo")
    async def aba(nome):
        async with websockets.connect(f"{url}?token={tk}") as ws:
            inicial = json.loads(await ws.recv())
            pronto[nome].set()
            msg = json.loads(await asyncio.wait_for(ws.recv(), 10))
            return nome, inicial, msg, time.perf_counter()
    pronto = {"aba 1": asyncio.Event(), "aba 2": asyncio.Event()}
    tarefas = [asyncio.create_task(aba(n)) for n in pronto]
    await asyncio.gather(*(e.wait() for e in pronto.values()))
    print("as duas abas estão conectadas e aguardando (cada uma já recebeu o estado inicial)")

    corpo = json.dumps({"id": "evt_ws_1", "type": "payment.succeeded", "data": {"payment_ref": pag["payment_ref"], "amount": pedido["total"]}}, separators=(",", ":")).encode()
    t0 = time.perf_counter()
    r = httpx.post(f"{API}/webhooks/payments/", content=corpo, headers={"X-Signature": assinar("whsec_lab_apenas_para_estudo", corpo), "Content-Type": "application/json"})
    t_resp = time.perf_counter()
    print(f"webhook → {r.status_code} {r.json()}")
    for nome, inicial, msg, quando in await asyncio.gather(*tarefas):
        print(f"{nome}: estado inicial = {inicial['status']!r} | mensagem em tempo real = {msg} | chegou {(quando - t0) * 1000:.0f} ms depois de enviar o webhook")


try:
    asyncio.run(main())
finally:
    for p in procs:
        os.killpg(p.pid, signal.SIGTERM)
    for p in procs:
        p.wait(timeout=20)
