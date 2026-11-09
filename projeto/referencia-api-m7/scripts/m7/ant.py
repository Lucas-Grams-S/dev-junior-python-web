import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen


class Antifraude(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.3)
        self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), Antifraude)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_port}/"

processados, trava = 0, threading.Lock()


def checar(pedido_id):
    global processados
    urlopen(URL, timeout=2).read()
    with trava:
        processados += 1
    return pedido_id


t = time.perf_counter(); [checar(i) for i in range(8)]; seq = time.perf_counter() - t
processados = 0
t = time.perf_counter()
with ThreadPoolExecutor(8) as ex:
    list(ex.map(checar, range(8)))
conc = time.perf_counter() - t
print(f"sequencial {seq:.2f} s | 8 threads {conc:.2f} s | processados={processados}")
assert conc < seq * 0.4 and processados == 8
print("ok")
