"""Dispara N requisições simultâneas e mede o tempo total. Uso: carga.py URL [N]"""

import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

url, n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 20


def um(_):
    t = time.perf_counter()
    with urllib.request.urlopen(url, timeout=60) as r:
        r.read()
    return time.perf_counter() - t


ini = time.perf_counter()
with ThreadPoolExecutor(n) as ex:
    tempos = sorted(ex.map(um, range(n)))
print(f"{n} requisições simultâneas em {time.perf_counter() - ini:5.2f} s  (mais rápida {tempos[0]:.2f} s, mais lenta {tempos[-1]:.2f} s)")
