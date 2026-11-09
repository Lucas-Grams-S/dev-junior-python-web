"""Uma 'API externa' de mentira, com os defeitos de uma real: lenta, instável, com limite de taxa e que trava."""
import json
import threading
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ESTADO = {"conexoes": 0, "pedidos": Counter(), "lock": threading.Lock(), "criados": 0, "chaves": {}, "perde_resposta": True}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"                         # keep-alive: a conexão pode ser reaproveitada

    def setup(self):
        super().setup()
        with ESTADO["lock"]:
            ESTADO["conexoes"] += 1                       # uma conexão TCP nova chegou

    def log_message(self, *a):
        pass

    def _responder(self, status, corpo, extra=None):
        dados = json.dumps(corpo).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        chave = q.get("k", "padrao")
        with ESTADO["lock"]:
            ESTADO["pedidos"][(url.path, chave)] += 1
            n = ESTADO["pedidos"][(url.path, chave)]
        if url.path == "/ok":
            return self._responder(200, {"ok": True})
        if url.path == "/lento":                          # demora `ms` milissegundos
            time.sleep(int(q.get("ms", 500)) / 1000)
            return self._responder(200, {"ok": True})
        if url.path == "/instavel":                       # falha com 503 nas primeiras `falhas` chamadas
            if n <= int(q.get("falhas", 2)):
                return self._responder(503, {"erro": "indisponível"})
            return self._responder(200, {"ok": True, "tentativa": n})
        if url.path == "/limite":                         # 429 com Retry-After na primeira chamada
            if n == 1:
                return self._responder(429, {"erro": "calma"}, {"Retry-After": "1"})
            return self._responder(200, {"ok": True, "tentativa": n})
        if url.path == "/trava":                          # aceita e nunca responde (até 10 s)
            time.sleep(10)
            return self._responder(200, {"ok": True})
        return self._responder(404, {"erro": "não existe"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(n)
        chave = self.headers.get("Idempotency-Key")
        with ESTADO["lock"]:
            if chave and chave in ESTADO["chaves"]:                        # repetição da mesma intenção: devolve o que já foi criado
                return self._responder(201, {"id": ESTADO["chaves"][chave], "replayed": True})
            ESTADO["criados"] += 1                                         # o EFEITO COLATERAL acontece aqui
            novo = ESTADO["criados"]
            if chave:
                ESTADO["chaves"][chave] = novo
            primeira = novo == 1 or (chave is None and novo == 1)
        if ESTADO["perde_resposta"] and ESTADO["criados"] == 1:
            return self._responder(503, {"erro": "indisponível"})          # criou, mas a RESPOSTA falhou (o pior caso)
        return self._responder(201, {"id": novo})


class Servidor(ThreadingHTTPServer):
    request_queue_size = 256                              # o padrão (5) faria conexões simultâneas esperarem ~1 s de retransmissão
    daemon_threads = True


def iniciar():
    srv = Servidor(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}"
