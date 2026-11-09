"""WSGI e ASGI sem framework: a interface entre o servidor e a aplicação, nua e crua."""
import asyncio
import json
import threading
import time
from wsgiref.simple_server import WSGIRequestHandler, make_server

import httpx
import uvicorn


# ------------------------------------------------------------------ WSGI: uma FUNÇÃO síncrona
def app_wsgi(environ, start_response):
    corpo = json.dumps({
        "metodo": environ["REQUEST_METHOD"],
        "caminho": environ["PATH_INFO"],
        "query": environ["QUERY_STRING"],
        "cabecalho_x": environ.get("HTTP_X_TESTE"),            # cabeçalhos viram HTTP_<NOME_EM_MAIUSCULAS>
    }).encode()
    start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(corpo)))])
    return [corpo]                                              # um iterável de bytes


# middleware WSGI = uma função que ENVOLVE outra aplicação WSGI
def tempo_wsgi(app):
    def novo(environ, start_response):
        t = time.perf_counter()
        def sr(status, headers, exc_info=None):
            headers.append(("X-Tempo-ms", f"{(time.perf_counter() - t) * 1000:.2f}"))
            return start_response(status, headers, exc_info)
        return app(environ, sr)
    return novo


# ------------------------------------------------------------------ ASGI: uma CORROTINA com (scope, receive, send)
EVENTOS = []


async def app_asgi(scope, receive, send):
    EVENTOS.append(f"scope: type={scope['type']} method={scope.get('method')} path={scope.get('path')}")
    if scope["type"] != "http":
        return
    evento = await receive()                                    # {"type": "http.request", "body": b"", "more_body": False}
    EVENTOS.append(f"receive: {evento['type']}")
    await asyncio.sleep(0.2)                                    # espera SEM bloquear o laço
    corpo = json.dumps({"metodo": scope["method"], "caminho": scope["path"], "esperou": "0,2 s sem bloquear"}).encode()
    await send({"type": "http.response.start", "status": 200,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(corpo)).encode())]})
    await send({"type": "http.response.body", "body": corpo})
    EVENTOS.append("send: http.response.start + http.response.body")


# middleware ASGI = uma corrotina que ENVOLVE outra aplicação ASGI
def tempo_asgi(app):
    async def novo(scope, receive, send):
        if scope["type"] != "http":
            return await app(scope, receive, send)
        t = time.perf_counter()
        async def send2(msg):
            if msg["type"] == "http.response.start":
                msg["headers"].append((b"x-tempo-ms", f"{(time.perf_counter() - t) * 1000:.0f}".encode()))
            await send(msg)
        await app(scope, receive, send2)
    return novo


class Mudo(WSGIRequestHandler):
    def log_message(self, *a):
        pass


# ------------------------------------------------------------------ execução
srv_w = make_server("127.0.0.1", 0, tempo_wsgi(app_wsgi), handler_class=Mudo)
threading.Thread(target=srv_w.serve_forever, daemon=True).start()
r = httpx.get(f"http://127.0.0.1:{srv_w.server_port}/produtos/?q=mouse", headers={"X-Teste": "oi"})
print("WSGI →", r.status_code, r.json())
print("       cabeçalho do middleware X-Tempo-ms:", r.headers["x-tempo-ms"])

config = uvicorn.Config(tempo_asgi(app_asgi), host="127.0.0.1", port=8151, log_level="error")
srv_a = uvicorn.Server(config)
threading.Thread(target=srv_a.run, daemon=True).start()
while not srv_a.started:
    time.sleep(0.05)
r = httpx.get("http://127.0.0.1:8151/produtos/")
print("\nASGI →", r.status_code, r.json())
print("       cabeçalho do middleware x-tempo-ms:", r.headers["x-tempo-ms"])
print("       o que o servidor entregou à aplicação:")
for e in EVENTOS:
    print("        ·", e)
srv_a.should_exit = True
srv_w.shutdown()
