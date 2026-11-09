"""Bloqueante × não bloqueante; I/O-bound × CPU-bound: medindo o tempo de parede e o tempo de CPU."""
import hashlib
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen


class Lento(BaseHTTPRequestHandler):                 # uma "API externa" que demora 0,3 s para responder
    def do_GET(self):
        time.sleep(0.3)
        self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), Lento)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_port}/"


def medir(titulo, fn):
    p0, c0 = time.perf_counter(), time.process_time()
    fn()
    parede, cpu = time.perf_counter() - p0, time.process_time() - c0
    print(f"{titulo:<48} parede={parede:5.2f}s  cpu={cpu:5.2f}s  cpu/parede={cpu / parede:4.0%}")
    return parede, cpu


print("--- I/O-bound: o programa ESPERA")
medir("4 × time.sleep(0.5)", lambda: [time.sleep(0.5) for _ in range(4)])
medir("5 chamadas HTTP seguidas à API lenta (0,3 s)", lambda: [urlopen(URL).read() for _ in range(5)])

print("\n--- CPU-bound: o programa TRABALHA")
def hash_pesado():
    for _ in range(4):
        hashlib.pbkdf2_hmac("sha256", b"senha", b"sal", 400_000)
medir("4 × PBKDF2 com 400 mil iterações", hash_pesado)
medir("soma de 10 milhões de inteiros (laço Python)", lambda: sum(i * i for i in range(10_000_000)))

print("\n--- o pedido do MiniShop, feito de forma síncrona (a cada passo o servidor ESPERA)")
def pedido_sincrono():
    time.sleep(0.05)      # grava o pedido no banco
    time.sleep(0.8)       # envia o e-mail de confirmação (SMTP)
    time.sleep(0.5)       # avisa o antifraude (HTTP)
    time.sleep(0.05)      # monta a resposta
t, cpu = medir("POST /orders/ com e-mail e antifraude no meio", pedido_sincrono)
print(f"→ o cliente espera {t:.1f} s; o servidor gastou só {cpu * 1000:.0f} ms de CPU: o resto foi ESPERA")

print("\n--- quantos pedidos por segundo cabem em um worker síncrono?")
for latencia in (0.05, 0.3, 1.4):
    print(f"latência {latencia:>4} s → {1 / latencia:5.1f} req/s por worker | com 4 workers: {4 / latencia:5.1f} req/s")
srv.shutdown()
