"""Custo de uma chamada: função no mesmo processo vs HTTP local (mesma máquina, sem rede real)."""
import statistics, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx

def estoque_disponivel(produto_id: int) -> int:
    return 42

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    wbufsize = 65536  # um único send por resposta (evita Nagle + ACK atrasado = +40 ms)
    def do_GET(self):
        corpo = b'{"disponivel": 42}'
        self.send_response(200); self.send_header("Content-Length", str(len(corpo))); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(corpo)
    def log_message(self, *a): pass

srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/estoque/1"

N = 2000
t = time.perf_counter()
for _ in range(N): estoque_disponivel(1)
fn = (time.perf_counter() - t) / N

with httpx.Client() as c:
    c.get(url)
    amostras = []
    for _ in range(N):
        t = time.perf_counter(); c.get(url); amostras.append(time.perf_counter() - t)
amostras.sort()
print(f"função no mesmo processo : {fn*1e6:10.2f} µs por chamada")
print(f"HTTP local (conexão viva) : mediana {statistics.median(amostras)*1e6:8.0f} µs · p99 {amostras[int(N*.99)]*1e6:8.0f} µs")
print(f"razão (mediana HTTP / função): ~{statistics.median(amostras)/fn:,.0f}x")

# disponibilidade composta: pedido chama k serviços em série, cada um com 99,9% de disponibilidade
for k in (1, 3, 5, 10):
    print(f"{k:>2} dependências a 99,9% → disponibilidade combinada {0.999**k*100:.2f}% (~{(1-0.999**k)*30*24*60:.0f} min fora do ar/mês)")
