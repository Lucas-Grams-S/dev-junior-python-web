import asyncio
import json
import ssl
import urllib.request

from websockets.asyncio.client import connect

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
base = "https://127.0.0.1:8443/api/v1"
req = urllib.request.Request(
    base + "/auth/token/",
    data=json.dumps({"username": "cliente", "password": "dev-somente-local-123"}).encode(),
    headers={"Content-Type": "application/json", "Host": "localhost"},
)
token = json.load(urllib.request.urlopen(req, context=ctx))["access"]


async def main():
    try:
        async with connect(f"wss://127.0.0.1:8443/ws/pedidos/1/?token={token}", ssl=ctx, open_timeout=5) as ws:
            print("WebSocket ABERTO; primeira mensagem:", await asyncio.wait_for(ws.recv(), 3))
    except Exception as e:
        print("falhou:", type(e).__name__, str(e)[:100])


asyncio.run(main())
