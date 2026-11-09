"""O 'Acme Pay': um provedor de pagamento de mentira com API e webhooks DIFERENTES dos do MiniShop."""
import hashlib
import hmac
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

ESTADO = {"requisicoes": 0, "cobrancas": {}, "falhar_primeira": True, "tentativas": {}}


class Servidor(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def responder(self, status, corpo):
        dados = json.dumps(corpo).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(dados)))
        self.end_headers(); self.wfile.write(dados)

    def do_POST(self):
        ESTADO["requisicoes"] += 1
        corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        chave = self.headers.get("Idempotency-Key")
        if self.path != "/v1/charges":
            return self.responder(404, {"error": "not_found"})
        ESTADO["tentativas"][chave] = ESTADO["tentativas"].get(chave, 0) + 1
        if ESTADO["falhar_primeira"] and ESTADO["tentativas"][chave] == 1:
            return self.responder(503, {"error": "temporarily_unavailable"})           # instável na 1ª tentativa
        if chave in ESTADO["cobrancas"]:                                                # idempotência do lado do provedor
            return self.responder(200, ESTADO["cobrancas"][chave])
        cobranca = {"charge_id": "ch_" + uuid.uuid4().hex[:12], "state": "PENDING", "amount_cents": corpo["amount_cents"]}
        ESTADO["cobrancas"][chave] = cobranca
        return self.responder(201, cobranca)


def iniciar(porta=8150):
    srv = Servidor(("127.0.0.1", porta), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def enviar_webhook(url, segredo, evento, charge_id, amount_cents, state, *, created=None, corpo_extra=None, assinar=True):
    """Assinatura da Acme: 'sha256=' + HMAC-SHA256(segredo, corpo). SEM timestamp no cabeçalho (o 'created' vai no corpo)."""
    corpo = json.dumps({"id": "evt_" + uuid.uuid4().hex[:10], "event": evento, "created": int(created or time.time()),
                        "charge": {"id": charge_id, "amount_cents": amount_cents, "state": state}, **(corpo_extra or {})}, separators=(",", ":")).encode()
    assinatura = "sha256=" + hmac.new(segredo.encode(), corpo, hashlib.sha256).hexdigest() if assinar else "sha256=invalida"
    return httpx.post(url, content=corpo, headers={"X-Acme-Signature": assinatura, "Content-Type": "application/json"}, timeout=5), corpo
