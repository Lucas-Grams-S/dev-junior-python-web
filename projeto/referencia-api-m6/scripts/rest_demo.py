"""Demonstra segurança, idempotência e statelessness com o servidor HTTP da biblioteca padrão."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import request as rq
from urllib.error import HTTPError

PRODUTOS = {}          # id -> dict
PROXIMO = [1]
TOKEN = "segredo-de-laboratorio"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _enviar(self, status, corpo=None, extra=None):
        dados = b"" if corpo is None else json.dumps(corpo).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(dados)

    def _autorizado(self):
        if self.headers.get("Authorization") != f"Bearer {TOKEN}":   # sem estado: confere a CADA requisição
            self._enviar(401, {"erro": "token ausente ou inválido"}, {"WWW-Authenticate": "Bearer"})
            return False
        return True

    def _corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if not self._autorizado():
            return
        if self.path == "/produtos":
            return self._enviar(200, list(PRODUTOS.values()))
        pid = int(self.path.rsplit("/", 1)[1])
        return self._enviar(200, PRODUTOS[pid]) if pid in PRODUTOS else self._enviar(404, {"erro": "não encontrado"})

    def do_POST(self):                                    # cria: NÃO é idempotente
        if not self._autorizado():
            return
        pid = PROXIMO[0]; PROXIMO[0] += 1
        PRODUTOS[pid] = {"id": pid, **self._corpo()}
        self._enviar(201, PRODUTOS[pid], {"Location": f"/produtos/{pid}"})

    def do_PUT(self):                                     # substitui: idempotente
        if not self._autorizado():
            return
        pid = int(self.path.rsplit("/", 1)[1])
        criado = pid not in PRODUTOS
        PRODUTOS[pid] = {"id": pid, **self._corpo()}
        self._enviar(201 if criado else 200, PRODUTOS[pid])

    def do_DELETE(self):                                  # remove: idempotente no ESTADO (status pode variar)
        if not self._autorizado():
            return
        pid = int(self.path.rsplit("/", 1)[1])
        self._enviar(204 if PRODUTOS.pop(pid, None) else 404)


srv = HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_port}"


def chamar(metodo, caminho, corpo=None, token=True):
    cab = {"Content-Type": "application/json"}
    if token:
        cab["Authorization"] = f"Bearer {TOKEN}"
    req = rq.Request(BASE + caminho, method=metodo, headers=cab, data=None if corpo is None else json.dumps(corpo).encode())
    try:
        with rq.urlopen(req) as r:
            return r.status, r.read().decode()
    except HTTPError as e:
        return e.code, e.read().decode()


def mostrar(titulo, *chamadas):
    print(f"\n--- {titulo}")
    for metodo, caminho, corpo in chamadas:
        status, texto = chamar(metodo, caminho, corpo)
        print(f"{metodo:<6} {caminho:<12} → {status}  estado agora: {len(PRODUTOS)} produto(s)")


mostrar("POST duas vezes (NÃO idempotente: cria dois)", ("POST", "/produtos", {"nome": "Mouse"}), ("POST", "/produtos", {"nome": "Mouse"}))
mostrar("PUT duas vezes no mesmo id (idempotente: um só)", ("PUT", "/produtos/10", {"nome": "Teclado"}), ("PUT", "/produtos/10", {"nome": "Teclado"}))
mostrar("DELETE duas vezes (mesmo estado final)", ("DELETE", "/produtos/10", None), ("DELETE", "/produtos/10", None))
mostrar("GET várias vezes (seguro: não muda nada)", ("GET", "/produtos", None), ("GET", "/produtos", None))

print("\n--- statelessness: sem o cabeçalho, nada é lembrado entre requisições")
print("GET sem token       →", chamar("GET", "/produtos", token=False)[0])
print("GET com token       →", chamar("GET", "/produtos")[0])
print("GET sem token (de novo, o servidor não 'lembra') →", chamar("GET", "/produtos", token=False)[0])
srv.shutdown()
